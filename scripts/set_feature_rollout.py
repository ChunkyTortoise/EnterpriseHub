#!/usr/bin/env python3
"""
Feature Rollout Manager for Phase 3 Production Deployment

Controls progressive feature rollout with A/B testing support.
Manages feature flags in Redis and assignment logic for gradual deployment.

Usage:
    python set_feature_rollout.py --feature realtime_intelligence --percentage 10
    python set_feature_rollout.py --percentage 25 --all-features
    python set_feature_rollout.py --feature churn_prevention --disable
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

import redis.asyncio as redis

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


PHASE_3_FEATURES = [
    'realtime_intelligence',
    'property_vision',
    'churn_prevention',
    'ai_coaching'
]


class FeatureRolloutManager:
    """Manages feature rollout percentages and assignments"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis_client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        logger.info("Connected to Redis")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")

    async def set_rollout_percentage(
        self,
        feature_name: str,
        percentage: int,
        enabled: bool = True
    ):
        """
        Set rollout percentage for a feature

        Args:
            feature_name: Name of the feature
            percentage: Rollout percentage (0-100)
            enabled: Whether feature is enabled
        """
        if feature_name not in PHASE_3_FEATURES:
            raise ValueError(
                f"Invalid feature name. Must be one of: {PHASE_3_FEATURES}"
            )

        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        config = {
            'enabled': enabled,
            'rollout_percentage': percentage,
            'updated_at': datetime.now().isoformat(),
            'updated_by': 'deployment_script'
        }

        # Store in Redis
        key = f'feature_flag:{feature_name}'
        await self.redis_client.set(key, json.dumps(config))

        logger.info(
            f"Set {feature_name} rollout to {percentage}% "
            f"(enabled={enabled})"
        )

        # Also store in a sorted set for easy querying
        score = percentage
        await self.redis_client.zadd(
            'feature_rollout_status',
            {feature_name: score}
        )

    async def get_rollout_status(
        self,
        feature_name: Optional[str] = None
    ) -> Dict:
        """
        Get current rollout status

        Args:
            feature_name: Specific feature or None for all

        Returns:
            Dictionary with rollout status
        """
        if feature_name:
            key = f'feature_flag:{feature_name}'
            config_str = await self.redis_client.get(key)

            if not config_str:
                return {
                    'feature': feature_name,
                    'enabled': False,
                    'rollout_percentage': 0,
                    'status': 'not_configured'
                }

            config = json.loads(config_str)
            return {
                'feature': feature_name,
                **config
            }
        else:
            # Get all features
            status = {}
            for feature in PHASE_3_FEATURES:
                feature_status = await self.get_rollout_status(feature)
                status[feature] = feature_status

            return status

    async def enable_all_features(self, percentage: int = 100):
        """
        Enable all Phase 3 features at specified percentage

        Args:
            percentage: Rollout percentage for all features
        """
        for feature in PHASE_3_FEATURES:
            await self.set_rollout_percentage(
                feature,
                percentage,
                enabled=True
            )

        logger.info(f"Enabled all features at {percentage}%")

    async def disable_feature(self, feature_name: str):
        """
        Disable a feature (set to 0% and enabled=False)

        Args:
            feature_name: Feature to disable
        """
        await self.set_rollout_percentage(
            feature_name,
            percentage=0,
            enabled=False
        )
        logger.info(f"Disabled {feature_name}")

    async def disable_all_features(self):
        """Disable all Phase 3 features"""
        for feature in PHASE_3_FEATURES:
            await self.disable_feature(feature)

        logger.info("Disabled all features")

    async def print_status(self):
        """Print current rollout status to console"""
        status = await self.get_rollout_status()

        print("\n" + "="*60)
        print("PHASE 3 FEATURE ROLLOUT STATUS")
        print("="*60)

        for feature_name, feature_status in status.items():
            enabled = feature_status.get('enabled', False)
            percentage = feature_status.get('rollout_percentage', 0)
            updated_at = feature_status.get('updated_at', 'Never')

            status_icon = "✅" if enabled else "❌"
            print(f"\n{status_icon} {feature_name.replace('_', ' ').title()}")
            print(f"   Enabled: {enabled}")
            print(f"   Rollout: {percentage}%")
            print(f"   Updated: {updated_at}")

        print("\n" + "="*60)


async def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Manage Phase 3 feature rollout percentages'
    )

    parser.add_argument(
        '--feature',
        type=str,
        choices=PHASE_3_FEATURES,
        help='Specific feature to configure'
    )

    parser.add_argument(
        '--percentage',
        type=int,
        help='Rollout percentage (0-100)'
    )

    parser.add_argument(
        '--all-features',
        action='store_true',
        help='Apply to all Phase 3 features'
    )

    parser.add_argument(
        '--disable',
        action='store_true',
        help='Disable the feature'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current rollout status'
    )

    parser.add_argument(
        '--redis-url',
        type=str,
        default=None,
        help='Redis URL (defaults to env REDIS_URL)'
    )

    args = parser.parse_args()

    # Get Redis URL
    import os
    redis_url = args.redis_url or os.getenv('REDIS_URL')

    if not redis_url:
        print("Error: Redis URL not provided. Set REDIS_URL env var or use --redis-url")
        sys.exit(1)

    # Create manager
    manager = FeatureRolloutManager(redis_url)

    try:
        await manager.connect()

        if args.status:
            # Just show status
            await manager.print_status()

        elif args.disable:
            # Disable feature
            if args.all_features:
                await manager.disable_all_features()
                print("✅ All features disabled")
            elif args.feature:
                await manager.disable_feature(args.feature)
                print(f"✅ {args.feature} disabled")
            else:
                print("Error: Specify --feature or --all-features with --disable")
                sys.exit(1)

        elif args.percentage is not None:
            # Set rollout percentage
            if args.all_features:
                await manager.enable_all_features(args.percentage)
                print(f"✅ All features set to {args.percentage}%")
            elif args.feature:
                await manager.set_rollout_percentage(
                    args.feature,
                    args.percentage
                )
                print(f"✅ {args.feature} set to {args.percentage}%")
            else:
                print("Error: Specify --feature or --all-features with --percentage")
                sys.exit(1)

        else:
            # No action specified, show status
            await manager.print_status()

        # Always show final status
        print("\nCurrent Status:")
        await manager.print_status()

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        await manager.close()


if __name__ == '__main__':
    asyncio.run(main())
