#!/usr/bin/env python3
"""
Standalone Conversation Manager for Jorge's Bot System

Handles conversation context and state management without external dependencies.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Simple conversation manager for Jorge's bots.

    Stores conversation context in local files for simplicity.
    In production, this would use a database like Redis or PostgreSQL.
    """

    def __init__(self, storage_dir: str = "data/conversations"):
        """Initialize conversation manager"""

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def get_context(self, contact_id: str, location_id: str) -> Dict[str, Any]:
        """Get conversation context for a contact"""

        try:
            context_file = self.storage_dir / f"{contact_id}_{location_id}.json"

            if context_file.exists():
                with open(context_file, 'r') as f:
                    context = json.load(f)
                    return context
            else:
                # Return default context for new conversations
                return self._create_default_context(contact_id, location_id)

        except Exception as e:
            self.logger.error(f"Error getting context for {contact_id}: {e}")
            return self._create_default_context(contact_id, location_id)

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Dict[str, Any],
        location_id: str,
        **kwargs
    ) -> None:
        """Update conversation context with new information"""

        try:
            # Get existing context
            context = await self.get_context(contact_id, location_id)

            # Update conversation history
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response,
                "extracted_data": extracted_data
            }

            if "conversation_history" not in context:
                context["conversation_history"] = []

            context["conversation_history"].append(conversation_entry)

            # Keep only last 50 messages to prevent file from growing too large
            context["conversation_history"] = context["conversation_history"][-50:]

            # Update context with extracted data
            context.update(kwargs)
            context["last_updated"] = datetime.now().isoformat()
            context["last_ai_response_time"] = datetime.now().isoformat()

            # Update lead/seller preferences based on extracted data
            if "lead_preferences" not in context:
                context["lead_preferences"] = {}
            if "seller_preferences" not in context:
                context["seller_preferences"] = {}

            # Merge extracted data into appropriate preferences
            lead_type = extracted_data.get("lead_type", "unknown")
            if lead_type == "buyer":
                context["lead_preferences"].update(extracted_data)
            elif lead_type == "seller":
                context["seller_preferences"].update(extracted_data)
            else:
                # Update both for unknown types
                context["lead_preferences"].update(extracted_data)
                context["seller_preferences"].update(extracted_data)

            # Save updated context
            await self.save_context(contact_id, context, location_id)

        except Exception as e:
            self.logger.error(f"Error updating context for {contact_id}: {e}")

    async def save_context(self, contact_id: str, context: Dict[str, Any], location_id: str) -> None:
        """Save conversation context to storage"""

        try:
            context_file = self.storage_dir / f"{contact_id}_{location_id}.json"

            with open(context_file, 'w') as f:
                json.dump(context, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving context for {contact_id}: {e}")

    async def extract_seller_data(
        self,
        user_message: str,
        current_seller_data: Dict[str, Any],
        tenant_config: Dict[str, Any],
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Extract seller data from user message (simplified version)"""

        try:
            # Simple extraction using keyword matching
            extracted = current_seller_data.copy()
            message_lower = user_message.lower()

            # Extract motivation
            if not extracted.get("motivation"):
                motivation_keywords = ["sell", "selling", "move", "relocat", "downsize", "divorce", "inherited"]
                for keyword in motivation_keywords:
                    if keyword in message_lower:
                        extracted["motivation"] = user_message[:100]  # First 100 chars as motivation
                        break

            # Extract timeline acceptance
            if extracted.get("timeline_acceptable") is None:
                if any(word in message_lower for word in ["yes", "ok", "fine", "sure", "work"]):
                    extracted["timeline_acceptable"] = True
                elif any(word in message_lower for word in ["no", "can't", "cannot", "impossible"]):
                    extracted["timeline_acceptable"] = False

            # Extract property condition
            if not extracted.get("property_condition"):
                if any(phrase in message_lower for phrase in ["move in ready", "perfect", "great condition"]):
                    extracted["property_condition"] = "Move-in Ready"
                elif any(phrase in message_lower for phrase in ["needs work", "fixer", "repairs"]):
                    extracted["property_condition"] = "Needs Work"

            # Extract price expectation
            if not extracted.get("price_expectation"):
                import re
                price_match = re.search(r'\$?([\d,]+)k?', user_message)
                if price_match:
                    extracted["price_expectation"] = price_match.group(0)

            # Count questions answered
            question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
            questions_answered = sum(1 for field in question_fields if extracted.get(field) is not None)
            extracted["questions_answered"] = questions_answered

            # Calculate basic response quality
            response_quality = min(1.0, len(user_message) / 50.0)  # Simple length-based quality
            extracted["response_quality"] = response_quality

            return extracted

        except Exception as e:
            self.logger.error(f"Error extracting seller data: {e}")
            return current_seller_data

    def _create_default_context(self, contact_id: str, location_id: str) -> Dict[str, Any]:
        """Create default context for new conversations"""

        return {
            "contact_id": contact_id,
            "location_id": location_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "conversation_history": [],
            "lead_preferences": {},
            "seller_preferences": {},
            "bot_state": "initial",
            "lead_score": 0,
            "seller_temperature": "cold"
        }