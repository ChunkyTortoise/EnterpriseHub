"""
Generate Training and Test Datasets

This script generates synthetic training/test data that matches the schema
of real LeadBehavioralFeatures. In production, this would be replaced with
real data extraction from the behavioral learning engine.

Author: TDD ML Model Development Specialist
Created: 2026-01-10
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generate realistic training data for ML models"""

    def __init__(self, output_dir: Path, random_seed: int = 42):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.random_seed = random_seed
        np.random.seed(random_seed)

        logger.info(f"Output directory: {output_dir}")

    def generate_churn_dataset(
        self,
        n_samples: int = 2000,
        test_split: float = 0.2
    ) -> None:
        """
        Generate churn prediction training and test datasets.

        Creates realistic behavioral feature data with known churn outcomes.
        """
        logger.info(f"Generating churn dataset: {n_samples} samples")

        # Generate features
        data = []

        for i in range(n_samples):
            # Decide if this lead will churn (40% base rate)
            will_churn = np.random.random() < 0.4

            # Generate features that correlate with churn
            if will_churn:
                # Churned leads show declining engagement
                days_since_last_activity = np.random.uniform(15, 45)
                interaction_velocity_7d = np.random.uniform(0, 0.5)
                interaction_velocity_14d = np.random.uniform(0.2, 1.0)
                interaction_velocity_30d = np.random.uniform(0.5, 1.5)
                email_response_rate = np.random.uniform(0, 0.4)
                sms_response_rate = np.random.uniform(0, 0.5)
                avg_response_time = np.random.uniform(300, 2000)
                urgency_score = np.random.uniform(0, 0.3)
                intent_strength = np.random.uniform(0, 0.4)
                property_views = np.random.randint(0, 5)
                search_queries = np.random.randint(0, 3)
            else:
                # Active leads show strong engagement
                days_since_last_activity = np.random.uniform(0, 10)
                interaction_velocity_7d = np.random.uniform(1.5, 5.0)
                interaction_velocity_14d = np.random.uniform(1.2, 4.0)
                interaction_velocity_30d = np.random.uniform(1.0, 3.0)
                email_response_rate = np.random.uniform(0.6, 1.0)
                sms_response_rate = np.random.uniform(0.6, 1.0)
                avg_response_time = np.random.uniform(10, 180)
                urgency_score = np.random.uniform(0.5, 1.0)
                intent_strength = np.random.uniform(0.6, 1.0)
                property_views = np.random.randint(5, 30)
                search_queries = np.random.randint(3, 15)

            # Common features
            days_since_creation = np.random.uniform(7, 90)
            total_interactions = np.random.randint(5, 100)
            unique_interaction_days = min(
                int(total_interactions * np.random.uniform(0.3, 0.8)),
                int(days_since_creation)
            )
            feature_completeness = np.random.uniform(0.7, 1.0)
            data_freshness_hours = np.random.uniform(1, 48)

            data.append({
                'lead_id': f'LEAD_{i:05d}',
                'days_since_last_activity': days_since_last_activity,
                'interaction_velocity_7d': interaction_velocity_7d,
                'interaction_velocity_14d': interaction_velocity_14d,
                'interaction_velocity_30d': interaction_velocity_30d,
                'email_response_rate': email_response_rate,
                'sms_response_rate': sms_response_rate,
                'avg_response_time_minutes': avg_response_time,
                'urgency_score': urgency_score,
                'intent_strength': intent_strength,
                'property_views': property_views,
                'search_queries': search_queries,
                'days_since_creation': days_since_creation,
                'total_interactions': total_interactions,
                'unique_interaction_days': unique_interaction_days,
                'feature_completeness': feature_completeness,
                'data_freshness_hours': data_freshness_hours,
                'churned': int(will_churn)
            })

        df = pd.DataFrame(data)

        # Split into train and test
        n_test = int(n_samples * test_split)
        n_train = n_samples - n_test

        train_df = df.iloc[:n_train]
        test_df = df.iloc[n_train:]

        # Save datasets
        train_file = self.output_dir / 'churn_training_set.csv'
        test_file = self.output_dir / 'churn_test_set.csv'

        train_df.to_csv(train_file, index=False)
        test_df.to_csv(test_file, index=False)

        logger.info(f"✅ Training set: {len(train_df)} samples -> {train_file}")
        logger.info(f"✅ Test set: {len(test_df)} samples -> {test_file}")
        logger.info(f"   Churn rate (train): {train_df['churned'].mean():.2%}")
        logger.info(f"   Churn rate (test): {test_df['churned'].mean():.2%}")

    def generate_lead_scoring_dataset(
        self,
        n_samples: int = 2000,
        test_split: float = 0.2
    ) -> None:
        """
        Generate lead scoring training and test datasets.

        Creates realistic lead data with hot/warm/cold classifications.
        """
        logger.info(f"Generating lead scoring dataset: {n_samples} samples")

        data = []

        for i in range(n_samples):
            # Randomly assign classification (balanced classes)
            classification = np.random.choice(['cold', 'warm', 'hot'], p=[0.3, 0.4, 0.3])

            # Generate features based on classification
            if classification == 'hot':
                # Hot leads: 3+ qualifying questions answered
                budget_provided = 1
                location_specified = 1
                timeline_confirmed = 1
                property_requirements = np.random.choice([0, 1], p=[0.2, 0.8])
                financing_status = np.random.choice([0, 1], p=[0.3, 0.7])
                motivation_shared = np.random.choice([0, 1], p=[0.4, 0.6])
                engagement_score = np.random.uniform(70, 100)
                response_rate = np.random.uniform(0.7, 1.0)
                property_views = np.random.randint(10, 50)
                days_active = np.random.randint(3, 30)
                interaction_frequency = np.random.uniform(2.0, 5.0)

            elif classification == 'warm':
                # Warm leads: 2 qualifying questions answered
                budget_provided = np.random.choice([0, 1], p=[0.3, 0.7])
                location_specified = np.random.choice([0, 1], p=[0.2, 0.8])
                timeline_confirmed = np.random.choice([0, 1], p=[0.5, 0.5])
                property_requirements = np.random.choice([0, 1], p=[0.6, 0.4])
                financing_status = np.random.choice([0, 1], p=[0.7, 0.3])
                motivation_shared = np.random.choice([0, 1], p=[0.7, 0.3])
                engagement_score = np.random.uniform(40, 70)
                response_rate = np.random.uniform(0.4, 0.7)
                property_views = np.random.randint(3, 15)
                days_active = np.random.randint(2, 20)
                interaction_frequency = np.random.uniform(0.8, 2.5)

            else:  # cold
                # Cold leads: 0-1 qualifying questions answered
                budget_provided = np.random.choice([0, 1], p=[0.7, 0.3])
                location_specified = np.random.choice([0, 1], p=[0.6, 0.4])
                timeline_confirmed = 0
                property_requirements = 0
                financing_status = 0
                motivation_shared = 0
                engagement_score = np.random.uniform(0, 40)
                response_rate = np.random.uniform(0, 0.4)
                property_views = np.random.randint(0, 5)
                days_active = np.random.randint(1, 15)
                interaction_frequency = np.random.uniform(0.1, 1.0)

            # Create preferences JSON (convert numpy types to Python types for JSON serialization)
            preferences = {}
            if budget_provided:
                preferences['budget'] = int(np.random.choice([300000, 400000, 500000, 600000]))
            if location_specified:
                preferences['location'] = str(np.random.choice(['Austin', 'Cedar Park', 'Round Rock']))
            if timeline_confirmed:
                preferences['timeline'] = str(np.random.choice(['ASAP', 'next month', '3 months']))
            if property_requirements:
                preferences['bedrooms'] = int(np.random.choice([2, 3, 4]))
            if financing_status:
                preferences['financing'] = str(np.random.choice(['pre-approved', 'getting pre-approved']))
            if motivation_shared:
                preferences['motivation'] = str(np.random.choice(['relocating', 'growing family', 'investment']))

            data.append({
                'lead_id': f'LEAD_{i:05d}',
                'budget_provided': budget_provided,
                'location_specified': location_specified,
                'timeline_confirmed': timeline_confirmed,
                'property_requirements': property_requirements,
                'financing_status': financing_status,
                'motivation_shared': motivation_shared,
                'engagement_score': engagement_score,
                'response_rate': response_rate,
                'property_views': property_views,
                'days_active': days_active,
                'interaction_frequency': interaction_frequency,
                'preferences': json.dumps(preferences),
                'conversation_history': json.dumps([]),
                'created_at': (datetime.now() - timedelta(days=days_active)).isoformat(),
                'actual_classification': classification
            })

        df = pd.DataFrame(data)

        # Split into train and test
        n_test = int(n_samples * test_split)
        n_train = n_samples - n_test

        # Stratified split to maintain class balance
        train_dfs = []
        test_dfs = []

        for classification in ['cold', 'warm', 'hot']:
            class_df = df[df['actual_classification'] == classification]
            n_class_test = int(len(class_df) * test_split)

            test_dfs.append(class_df.iloc[:n_class_test])
            train_dfs.append(class_df.iloc[n_class_test:])

        train_df = pd.concat(train_dfs, ignore_index=True)
        test_df = pd.concat(test_dfs, ignore_index=True)

        # Shuffle
        train_df = train_df.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)
        test_df = test_df.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)

        # Save datasets
        train_file = self.output_dir / 'lead_scoring_training_set.csv'
        test_file = self.output_dir / 'lead_scoring_test_set.csv'

        train_df.to_csv(train_file, index=False)
        test_df.to_csv(test_file, index=False)

        logger.info(f"✅ Training set: {len(train_df)} samples -> {train_file}")
        logger.info(f"✅ Test set: {len(test_df)} samples -> {test_file}")
        logger.info(f"   Class distribution (train):")
        for classification, count in train_df['actual_classification'].value_counts().items():
            logger.info(f"     {classification}: {count} ({count/len(train_df):.2%})")


def main():
    """Main data generation script"""
    parser = argparse.ArgumentParser(description='Generate training/test datasets')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'tests' / 'fixtures' / 'training_data',
        help='Output directory for datasets'
    )
    parser.add_argument(
        '--ml-test-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'tests' / 'fixtures' / 'ml_test_data',
        help='Output directory for ML test data'
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=2000,
        help='Number of samples to generate'
    )
    parser.add_argument(
        '--test-split',
        type=float,
        default=0.2,
        help='Fraction of data for test set'
    )
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    # Create both output directories
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.ml_test_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("GENERATING TRAINING/TEST DATASETS")
    logger.info("=" * 80)

    # Generate training data
    generator = TrainingDataGenerator(args.output_dir, args.random_seed)

    logger.info("\n--- Churn Prediction Dataset ---")
    generator.generate_churn_dataset(args.n_samples, args.test_split)

    logger.info("\n--- Lead Scoring Dataset ---")
    generator.generate_lead_scoring_dataset(args.n_samples, args.test_split)

    # Copy test sets to ml_test_data directory for pytest
    import shutil

    churn_test_src = args.output_dir / 'churn_test_set.csv'
    churn_test_dst = args.ml_test_dir / 'churn_test_set.csv'
    shutil.copy(churn_test_src, churn_test_dst)

    lead_test_src = args.output_dir / 'lead_scoring_test_set.csv'
    lead_test_dst = args.ml_test_dir / 'lead_scoring_test_set.csv'
    shutil.copy(lead_test_src, lead_test_dst)

    logger.info(f"\n✅ Test datasets also copied to: {args.ml_test_dir}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ DATASET GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Run: python scripts/train_production_models.py")
    logger.info("2. Run: pytest ghl_real_estate_ai/tests/test_production_ml_models.py")


if __name__ == "__main__":
    main()
