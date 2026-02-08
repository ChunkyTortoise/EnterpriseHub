"""
🤖 MLOps Retraining Job - Service 6 Phase 2
==========================================

Automated pipeline to monitor lead conversion data and trigger model retraining.
Features:
- Monitors MemoryService for new interaction data
- Feature extraction for training samples
- Threshold-based retraining triggers
- Performance validation before deployment

Author: Claude AI Enhancement System
Date: 2026-01-25
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
    AdvancedMLLeadScoringEngine,
    MLFeatureVector,
    create_advanced_ml_scoring_engine,
)
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)


class MLOpsRetrainingJob:
    """
    Automated MLOps job for model retraining.
    """

    def __init__(
        self,
        engine: Optional[AdvancedMLLeadScoringEngine] = None,
        threshold: int = 50,
        check_interval_seconds: int = 3600,
    ):
        self.engine = engine
        self.threshold = threshold
        self.check_interval_seconds = check_interval_seconds
        self.memory_service = MemoryService()
        self.is_running = False
        self._last_training_count = 0

    async def initialize(self):
        """Initialize the engine if not provided"""
        if self.engine is None:
            self.engine = await create_advanced_ml_scoring_engine()

        # Load current model state/count from cache if possible
        # For now, just start fresh or use current memory count
        current_data = await self._collect_training_data()
        self._last_training_count = len(current_data)
        logger.info(f"MLOps job initialized with {self._last_training_count} initial samples")

    async def run_once(self):
        """Execute one cycle of the retraining monitor"""
        logger.info("Starting MLOps retraining check...")

        training_data = await self._collect_training_data()
        current_count = len(training_data)

        new_samples = current_count - self._last_training_count
        logger.info(f"MLOps check: Total samples={current_count}, New={new_samples}, Threshold={self.threshold}")

        if new_samples >= self.threshold:
            logger.info(f"Threshold met ({new_samples} >= {self.threshold}). Triggering retraining...")
            results = await self.engine.retrain_models(training_data)

            if all(results.values()):
                logger.info("Model retraining successful for all components")
                self._last_training_count = current_count
                # In a real system, we might save the new last_training_count to persistent storage
            else:
                logger.warning(f"Model retraining partially failed: {results}")
        else:
            logger.info("Threshold not met. Skipping retraining.")

    async def start(self):
        """Start the background retraining monitor"""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"MLOps retraining job started (interval: {self.check_interval_seconds}s)")

        while self.is_running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Error in MLOps retraining cycle: {e}")

            await asyncio.sleep(self.check_interval_seconds)

    async def stop(self):
        """Stop the background monitor"""
        self.is_running = False
        logger.info("MLOps retraining job stopped")

    async def _collect_training_data(self) -> pd.DataFrame:
        """
        Collect and label training data from MemoryService.
        """
        all_samples = []

        # In a real production system with thousands of files,
        # we would use a database query or an indexed search.
        # For this implementation, we scan the data/memory directory.
        memory_dir = self.memory_service.memory_dir

        # Walk through all JSON files in memory_dir
        for root, _, files in os.walk(memory_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)

                        sample = await self._process_lead_into_sample(data)
                        if sample:
                            all_samples.append(sample)
                    except Exception as e:
                        # Skip malformed files
                        continue

        if not all_samples:
            return pd.DataFrame()

        return pd.DataFrame(all_samples)

    async def _process_lead_into_sample(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert raw lead data into a labeled feature dictionary.
        """
        lead_id = data.get("contact_id")
        if not lead_id:
            return None

        # 1. Extract features using the engine's pipeline
        try:
            features = await self.engine.feature_pipeline.extract_features(lead_id, data)
            feature_dict = asdict(features)

            # 2. Determine conversion label
            # Conversion defined as reaching high-intent stages or specific engagement statuses
            conversation_stage = data.get("conversation_stage", "").lower()
            engagement_status = data.get("engagement_status", "").lower()

            converted = 0
            if conversation_stage in ["purchase", "evaluation", "qualified"]:
                converted = 1
            elif engagement_status in ["showing_booked", "offer_sent", "under_contract", "qualified"]:
                converted = 1

            feature_dict["converted"] = converted
            return feature_dict

        except Exception as e:
            logger.debug(f"Failed to process lead {lead_id} for training: {e}")
            return None


async def start_mlops_job(threshold: int = 50, interval: int = 3600):
    """Entry point to start the MLOps job"""
    job = MLOpsRetrainingJob(threshold=threshold, check_interval_seconds=interval)
    await job.initialize()
    asyncio.create_task(job.start())
    return job
