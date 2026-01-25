#!/usr/bin/env python3
"""
Jorge's ML Data Collector - Historical Lead Data for Training

Collects and prepares historical lead data for ML model training.
Extracts features and outcomes for predictive lead scoring.

Author: Claude Code Assistant
Created: 2026-01-23
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class LeadOutcome(str, Enum):
    """Lead conversion outcomes"""
    WON = "won"              # Closed deal
    LOST = "lost"            # Lost to competitor or disqualified
    PIPELINE = "pipeline"    # Still in progress
    COLD = "cold"            # Went cold / unresponsive


class LeadQuality(str, Enum):
    """Lead quality levels"""
    HOT = "hot"              # 80+ score
    WARM = "warm"            # 50-79 score
    COLD = "cold"            # <50 score


@dataclass
class HistoricalLeadData:
    """Historical lead record for ML training"""

    # Identifiers
    lead_id: str
    contact_id: Optional[str] = None
    source: str = "ghl"

    # Contact info
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    # Lead intelligence
    message_text: str = ""
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    timeline: str = "unknown"
    location_preferences: List[str] = field(default_factory=list)
    financing_status: str = "unknown"

    # Behavioral features
    response_time_hours: Optional[float] = None
    num_interactions: int = 0
    engagement_score: float = 0.0
    questions_asked: int = 0

    # Temporal features
    created_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    hour_of_day: Optional[int] = None  # 0-23

    # Outcome (TARGET variable for ML)
    outcome: Optional[LeadOutcome] = None
    quality: Optional[LeadQuality] = None
    converted: bool = False
    revenue: Optional[float] = None
    days_to_conversion: Optional[int] = None

    # Metadata
    parsing_errors: List[str] = field(default_factory=list)


class JorgeMLDataCollector:
    """
    Collect and prepare historical lead data for ML model training

    Responsibilities:
    1. Extract historical lead data from GHL/database
    2. Engineer features for ML
    3. Label outcomes (won/lost/pipeline)
    4. Prepare train/test splits
    5. Handle missing data gracefully
    """

    def __init__(self, lookback_days: int = 90):
        """
        Initialize data collector

        Args:
            lookback_days: How many days of historical data to collect
        """
        self.logger = logging.getLogger(__name__)
        self.lookback_days = lookback_days

    async def collect_historical_leads(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Collect historical lead data for ML training

        Args:
            start_date: Start of date range (default: 90 days ago)
            end_date: End of date range (default: today)

        Returns:
            DataFrame with features and target variables
        """

        # Set default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=self.lookback_days)

        self.logger.info(f"Collecting leads from {start_date} to {end_date}")

        try:
            # TODO: Integrate with actual GHL API or database
            # For now, generate synthetic training data
            leads = await self._collect_from_database(start_date, end_date)

            if not leads:
                self.logger.warning("No historical leads found - generating synthetic data")
                leads = self._generate_synthetic_training_data(num_leads=500)

            # Convert to DataFrame
            df = pd.DataFrame([vars(lead) for lead in leads])

            self.logger.info(f"Collected {len(df)} historical leads")

            return df

        except Exception as e:
            self.logger.error(f"Error collecting historical data: {e}")
            raise

    async def _collect_from_database(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalLeadData]:
        """
        Collect leads from database (actual implementation)

        TODO: Integrate with Jorge's actual database
        """

        leads = []

        # Placeholder for actual database query
        # In production, this would:
        # 1. Query PostgreSQL for leads in date range
        # 2. Join with interactions table
        # 3. Join with deals/opportunities for outcomes
        # 4. Calculate derived metrics

        # Example query (pseudo-code):
        """
        SELECT
            l.id,
            l.contact_id,
            l.source,
            l.message_text,
            l.budget_min,
            l.budget_max,
            l.timeline,
            l.created_at,
            COUNT(i.id) as num_interactions,
            AVG(i.response_time_hours) as avg_response_time,
            d.status as outcome,
            d.revenue,
            d.closed_date
        FROM leads l
        LEFT JOIN interactions i ON i.lead_id = l.id
        LEFT JOIN deals d ON d.lead_id = l.id
        WHERE l.created_at BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY l.id
        """

        return leads

    def _generate_synthetic_training_data(self, num_leads: int = 500) -> List[HistoricalLeadData]:
        """
        Generate synthetic training data for initial model development

        This allows us to build and test the ML pipeline before
        we have real historical data.
        """

        np.random.seed(42)  # Reproducible
        leads = []

        # Define realistic distributions based on Jorge's current metrics
        SOURCES = ["ghl", "zillow", "realtor_com", "facebook", "referral"]
        TIMELINES = ["immediate", "1_month", "2_months", "3_months", "flexible"]
        FINANCING = ["cash", "pre_approved", "conventional", "fha", "needs_financing"]

        for i in range(num_leads):
            # Random features
            source = np.random.choice(SOURCES, p=[0.4, 0.25, 0.20, 0.10, 0.05])

            budget_min = np.random.choice([200, 300, 400, 500, 600]) * 1000
            budget_max = budget_min + np.random.choice([100, 150, 200, 300]) * 1000

            timeline = np.random.choice(TIMELINES)
            financing = np.random.choice(FINANCING)

            num_interactions = np.random.poisson(lam=3)  # Average 3 interactions
            response_time = np.random.exponential(scale=2)  # Average 2 hours

            created_at = datetime.now() - timedelta(
                days=np.random.randint(1, self.lookback_days)
            )

            # Create message text with realistic patterns
            message_text = self._generate_synthetic_message(
                budget_max, timeline, financing
            )

            # Determine outcome based on quality indicators
            # Higher quality → higher conversion probability
            quality_score = self._calculate_quality_score({
                'budget_max': budget_max,
                'timeline': timeline,
                'financing': financing,
                'source': source,
                'response_time': response_time
            })

            # Conversion probability based on quality
            conversion_prob = quality_score / 120.0  # Normalize to 0-1

            converted = np.random.random() < conversion_prob

            if converted:
                outcome = LeadOutcome.WON
                revenue = np.random.uniform(8000, 15000)  # Jorge's commission
                days_to_conversion = np.random.randint(7, 60)
            elif np.random.random() < 0.3:
                outcome = LeadOutcome.PIPELINE
                revenue = None
                days_to_conversion = None
            else:
                outcome = LeadOutcome.LOST
                revenue = None
                days_to_conversion = None

            # Determine quality based on score
            if quality_score >= 80:
                quality = LeadQuality.HOT
            elif quality_score >= 50:
                quality = LeadQuality.WARM
            else:
                quality = LeadQuality.COLD

            lead = HistoricalLeadData(
                lead_id=f"lead_{i:04d}",
                contact_id=f"contact_{i:04d}",
                source=source,
                name=f"Lead {i}",
                message_text=message_text,
                budget_min=budget_min,
                budget_max=budget_max,
                timeline=timeline,
                financing_status=financing,
                response_time_hours=response_time,
                num_interactions=num_interactions,
                engagement_score=np.random.uniform(0, 100),
                questions_asked=np.random.poisson(lam=2),
                created_at=created_at,
                day_of_week=created_at.weekday(),
                hour_of_day=created_at.hour,
                outcome=outcome,
                quality=quality,
                converted=converted,
                revenue=revenue,
                days_to_conversion=days_to_conversion
            )

            leads.append(lead)

        self.logger.info(f"Generated {num_leads} synthetic training leads")
        return leads

    def _generate_synthetic_message(
        self,
        budget: int,
        timeline: str,
        financing: str
    ) -> str:
        """Generate realistic lead message text"""

        templates = [
            f"Hi, I'm looking for a home in Rancho Cucamonga. Budget is around ${budget//1000}k. {timeline.replace('_', ' ')} timeline. {financing.replace('_', ' ')}.",
            f"Interested in buying in the Rancho Cucamonga area. Price range ${budget//1000}k. Need help with {financing.replace('_', ' ')}. Timeline: {timeline.replace('_', ' ')}.",
            f"Looking to purchase. Budget ${budget//1000}k. How soon can we start? {timeline.replace('_', ' ')}.",
            f"Want to see homes around ${budget//1000}k in Rancho Cucamonga. {financing.replace('_', ' ')}. {timeline.replace('_', ' ')}."
        ]

        return np.random.choice(templates)

    def _calculate_quality_score(self, features: Dict) -> float:
        """Calculate synthetic quality score for generating realistic data"""

        score = 50  # Base score

        # Budget impact
        if features['budget_max'] >= 700000:
            score += 15
        elif features['budget_max'] >= 400000:
            score += 10
        else:
            score += 5

        # Timeline impact
        timeline_scores = {
            'immediate': 20,
            '1_month': 15,
            '2_months': 10,
            '3_months': 5,
            'flexible': 0
        }
        score += timeline_scores.get(features['timeline'], 0)

        # Financing impact
        financing_scores = {
            'cash': 15,
            'pre_approved': 12,
            'conventional': 8,
            'fha': 5,
            'needs_financing': 0
        }
        score += financing_scores.get(features['financing'], 0)

        # Source quality
        source_scores = {
            'zillow': 10,
            'realtor_com': 8,
            'ghl': 10,
            'facebook': 3,
            'referral': 15
        }
        score += source_scores.get(features['source'], 0)

        # Response time penalty
        if features['response_time'] > 24:
            score -= 10
        elif features['response_time'] > 12:
            score -= 5

        return max(0, min(100, score))

    async def engineer_features(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer ML-ready features from raw lead data

        Args:
            raw_data: DataFrame with historical lead data

        Returns:
            DataFrame with engineered features ready for ML
        """

        df = raw_data.copy()

        try:
            # Text features
            df['message_length'] = df['message_text'].str.len()
            df['word_count'] = df['message_text'].str.split().str.len()
            df['question_marks'] = df['message_text'].str.count(r'\?')
            df['exclamation_marks'] = df['message_text'].str.count(r'!')
            df['has_specific_budget'] = df['budget_max'].notna().astype(int)

            # Budget features
            df['budget_midpoint'] = (df['budget_min'] + df['budget_max']) / 2
            df['budget_range'] = df['budget_max'] - df['budget_min']
            df['budget_specificity'] = np.where(
                df['budget_range'] <= 100000, 1,
                np.where(df['budget_range'] <= 200000, 0.5, 0)
            )

            # Timeline urgency score
            timeline_urgency = {
                'immediate': 1.0,
                '1_month': 0.8,
                '2_months': 0.6,
                '3_months': 0.4,
                '6_months': 0.2,
                'flexible': 0.0,
                'unknown': 0.3
            }
            df['timeline_urgency'] = df['timeline'].map(timeline_urgency).fillna(0.3)

            # Financing readiness score
            financing_readiness = {
                'cash': 1.0,
                'pre_approved': 0.9,
                'conventional': 0.7,
                'fha': 0.6,
                'va': 0.7,
                'jumbo': 0.7,
                'needs_financing': 0.3,
                'unknown': 0.4
            }
            df['financing_readiness'] = df['financing_status'].map(financing_readiness).fillna(0.4)

            # Behavioral features
            df['response_time_hours_log'] = np.log1p(df['response_time_hours'].fillna(24))
            df['interactions_log'] = np.log1p(df['num_interactions'])
            df['engagement_normalized'] = df['engagement_score'] / 100.0

            # Temporal features
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_business_hours'] = df['hour_of_day'].between(9, 17).astype(int)

            # Source quality (one-hot encoding)
            source_dummies = pd.get_dummies(df['source'], prefix='source')
            df = pd.concat([df, source_dummies], axis=1)

            # Target variable
            df['target'] = df['converted'].astype(int)

            # Quality score as target for regression
            df['quality_score'] = df['quality'].map({
                'hot': 90,
                'warm': 65,
                'cold': 30
            }).fillna(50)

            self.logger.info(f"Engineered {len(df.columns)} features")

            return df

        except Exception as e:
            self.logger.error(f"Error engineering features: {e}")
            raise

    def prepare_train_test_split(
        self,
        data: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> tuple:
        """
        Prepare train/test split for ML training

        Args:
            data: Engineered feature DataFrame
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility

        Returns:
            (X_train, X_test, y_train, y_test)
        """

        from sklearn.model_selection import train_test_split

        # Feature columns (exclude metadata and targets)
        feature_cols = [
            'message_length', 'word_count', 'question_marks', 'exclamation_marks',
            'has_specific_budget', 'budget_midpoint', 'budget_range', 'budget_specificity',
            'timeline_urgency', 'financing_readiness', 'response_time_hours_log',
            'interactions_log', 'engagement_normalized', 'is_weekend', 'is_business_hours'
        ]

        # Add source dummies
        source_cols = [col for col in data.columns if col.startswith('source_')]
        feature_cols.extend(source_cols)

        # Handle missing values
        X = data[feature_cols].fillna(0)
        y = data['target']

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y  # Maintain class distribution
        )

        self.logger.info(f"Train set: {len(X_train)} samples")
        self.logger.info(f"Test set: {len(X_test)} samples")
        self.logger.info(f"Positive rate: {y.mean():.2%}")

        return X_train, X_test, y_train, y_test


async def main():
    """Test data collection and feature engineering"""

    logging.basicConfig(level=logging.INFO)

    collector = JorgeMLDataCollector(lookback_days=90)

    # Collect historical data
    print("Collecting historical lead data...")
    raw_data = await collector.collect_historical_leads()

    print(f"\nRaw data shape: {raw_data.shape}")
    print(f"Conversion rate: {raw_data['converted'].mean():.2%}")
    print(f"\nOutcome distribution:")
    print(raw_data['outcome'].value_counts())

    # Engineer features
    print("\nEngineering features...")
    engineered_data = await collector.engineer_features(raw_data)

    print(f"\nEngineered data shape: {engineered_data.shape}")
    print(f"\nFeature columns:")
    print(engineered_data.columns.tolist()[:20], "...")

    # Prepare train/test split
    print("\nPreparing train/test split...")
    X_train, X_test, y_train, y_test = collector.prepare_train_test_split(engineered_data)

    print(f"\n✅ Data collection and feature engineering complete!")
    print(f"Ready for model training with {len(X_train)} training samples")


if __name__ == "__main__":
    asyncio.run(main())
