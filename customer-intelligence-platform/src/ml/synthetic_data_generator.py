"""
Synthetic Data Generator for Customer Intelligence Platform.

Generates realistic synthetic customer data for:
- Model training and testing
- Demo purposes
- Performance benchmarking
- A/B testing scenarios

Features:
- Realistic customer behavior patterns
- Industry-specific scenarios
- Temporal data generation
- Configurable data distribution
- Privacy-preserving synthetic data
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)


class IndustryType(Enum):
    """Industry types for customer segmentation."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    CONSULTING = "consulting"
    EDUCATION = "education"


class CompanySize(Enum):
    """Company size categories."""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    ENTERPRISE = "enterprise"


@dataclass
class CustomerProfile:
    """Template for customer profile generation."""
    industry: IndustryType
    company_size: CompanySize
    budget_range: Tuple[int, int]
    engagement_probability: float
    conversion_probability: float
    churn_probability: float
    ltv_range: Tuple[int, int]
    typical_features: Dict[str, Any]


class SyntheticDataGenerator:
    """Generator for realistic synthetic customer data."""

    def __init__(self, random_seed: int = 42):
        """Initialize the synthetic data generator."""
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Customer profiles for different segments
        self.customer_profiles = self._initialize_customer_profiles()

        # Common feature distributions
        self.feature_distributions = self._initialize_feature_distributions()

        logger.info("SyntheticDataGenerator initialized")

    def _initialize_customer_profiles(self) -> Dict[str, CustomerProfile]:
        """Initialize customer profile templates."""

        profiles = {
            "high_value_tech": CustomerProfile(
                industry=IndustryType.TECHNOLOGY,
                company_size=CompanySize.ENTERPRISE,
                budget_range=(50000, 500000),
                engagement_probability=0.8,
                conversion_probability=0.6,
                churn_probability=0.1,
                ltv_range=(100000, 1000000),
                typical_features={
                    "message_count_mean": 15,
                    "response_time_mean": 30,
                    "session_duration_mean": 45,
                    "support_tickets_mean": 2
                }
            ),

            "medium_value_healthcare": CustomerProfile(
                industry=IndustryType.HEALTHCARE,
                company_size=CompanySize.MEDIUM,
                budget_range=(20000, 200000),
                engagement_probability=0.6,
                conversion_probability=0.4,
                churn_probability=0.2,
                ltv_range=(50000, 300000),
                typical_features={
                    "message_count_mean": 10,
                    "response_time_mean": 60,
                    "session_duration_mean": 30,
                    "support_tickets_mean": 3
                }
            ),

            "low_value_retail": CustomerProfile(
                industry=IndustryType.RETAIL,
                company_size=CompanySize.SMALL,
                budget_range=(5000, 50000),
                engagement_probability=0.4,
                conversion_probability=0.2,
                churn_probability=0.3,
                ltv_range=(10000, 80000),
                typical_features={
                    "message_count_mean": 5,
                    "response_time_mean": 120,
                    "session_duration_mean": 15,
                    "support_tickets_mean": 1
                }
            ),

            "startup_disruptor": CustomerProfile(
                industry=IndustryType.TECHNOLOGY,
                company_size=CompanySize.STARTUP,
                budget_range=(10000, 100000),
                engagement_probability=0.9,
                conversion_probability=0.3,
                churn_probability=0.4,
                ltv_range=(20000, 200000),
                typical_features={
                    "message_count_mean": 20,
                    "response_time_mean": 15,
                    "session_duration_mean": 60,
                    "support_tickets_mean": 5
                }
            ),

            "enterprise_finance": CustomerProfile(
                industry=IndustryType.FINANCE,
                company_size=CompanySize.ENTERPRISE,
                budget_range=(100000, 1000000),
                engagement_probability=0.5,
                conversion_probability=0.7,
                churn_probability=0.05,
                ltv_range=(500000, 5000000),
                typical_features={
                    "message_count_mean": 8,
                    "response_time_mean": 180,
                    "session_duration_mean": 25,
                    "support_tickets_mean": 1
                }
            )
        }

        return profiles

    def _initialize_feature_distributions(self) -> Dict[str, Dict]:
        """Initialize feature distribution parameters."""

        distributions = {
            "hour_of_day": {
                "business_hours": [9, 10, 11, 13, 14, 15, 16, 17],  # Higher probability
                "off_hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 18, 19, 20, 21, 22, 23]
            },
            "day_of_week": {
                "weekdays": [0, 1, 2, 3, 4],  # Monday-Friday
                "weekends": [5, 6]  # Saturday-Sunday
            },
            "response_sentiment": {
                "positive": ["enthusiastic", "interested", "engaged", "optimistic"],
                "neutral": ["professional", "inquiring", "factual", "standard"],
                "negative": ["skeptical", "hesitant", "concerned", "uninterested"]
            },
            "channel_preferences": ["email", "phone", "chat", "in_person", "video_call"],
            "service_interests": [
                "consulting", "implementation", "support", "training",
                "integration", "customization", "maintenance", "analytics"
            ]
        }

        return distributions

    def generate_customer_dataset(
        self,
        num_customers: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_churn: bool = True
    ) -> pd.DataFrame:
        """Generate a comprehensive customer dataset."""

        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()

        customers = []

        # Profile distribution weights
        profile_weights = [0.3, 0.25, 0.25, 0.1, 0.1]  # Favor common profiles
        profile_names = list(self.customer_profiles.keys())

        for i in range(num_customers):
            # Select customer profile
            profile_name = np.random.choice(profile_names, p=profile_weights)
            profile = self.customer_profiles[profile_name]

            # Generate customer
            customer = self._generate_single_customer(
                customer_id=f"customer_{i+1:06d}",
                profile=profile,
                start_date=start_date,
                end_date=end_date,
                include_churn=include_churn
            )

            customers.append(customer)

        df = pd.DataFrame(customers)

        # Add derived features
        df = self._add_derived_features(df)

        logger.info(f"Generated dataset with {len(df)} customers")
        return df

    def _generate_single_customer(
        self,
        customer_id: str,
        profile: CustomerProfile,
        start_date: datetime,
        end_date: datetime,
        include_churn: bool
    ) -> Dict[str, Any]:
        """Generate a single customer record."""

        # Basic customer info
        creation_date = self._random_date(start_date, end_date - timedelta(days=30))

        customer = {
            "customer_id": customer_id,
            "industry": profile.industry.value,
            "company_size": profile.company_size.value,
            "created_at": creation_date,
            "department_id": self._random_department(),
        }

        # Budget and financial features
        budget_min, budget_max = profile.budget_range
        customer["budget"] = int(np.random.lognormal(
            np.log(budget_min + budget_max) / 2,
            0.5
        ))
        customer["budget"] = max(budget_min, min(budget_max, customer["budget"]))

        # Engagement features
        features = profile.typical_features
        customer["message_count"] = max(1, int(np.random.poisson(features["message_count_mean"])))
        customer["response_time"] = max(1, int(np.random.exponential(features["response_time_mean"])))
        customer["session_duration"] = max(1, int(np.random.gamma(2, features["session_duration_mean"] / 2)))
        customer["support_tickets"] = int(np.random.poisson(features["support_tickets_mean"]))

        # Behavioral features
        customer["hour_of_day"] = self._generate_hour_preference()
        customer["day_of_week"] = np.random.choice([0, 1, 2, 3, 4, 5, 6])
        customer["is_weekend"] = 1 if customer["day_of_week"] in [5, 6] else 0

        # Communication preferences
        customer["contact_preference"] = np.random.choice(
            self.feature_distributions["channel_preferences"],
            p=[0.4, 0.2, 0.2, 0.1, 0.1]
        )

        # Service interests
        num_interests = np.random.randint(1, 4)
        customer["service_interest"] = np.random.choice(
            self.feature_distributions["service_interests"],
            size=num_interests,
            replace=False
        ).tolist()

        # Time-based features
        customer["account_age_days"] = (end_date - creation_date).days
        customer["last_activity_date"] = self._random_date(
            creation_date + timedelta(days=1),
            end_date
        )
        customer["days_since_last_activity"] = (end_date - customer["last_activity_date"]).days

        # Engagement quality indicators
        customer["engagement_score"] = self._calculate_engagement_score(customer, profile)
        customer["priority_level"] = self._determine_priority_level(customer)

        # Target variables
        customer["converted"] = self._determine_conversion(customer, profile)
        customer["high_engagement"] = 1 if customer["engagement_score"] > 0.7 else 0

        if include_churn:
            customer["churned"] = self._determine_churn(customer, profile)

        # LTV estimation
        ltv_min, ltv_max = profile.ltv_range
        if customer["converted"]:
            customer["customer_ltv"] = np.random.uniform(ltv_min * 0.7, ltv_max)
        else:
            customer["customer_ltv"] = np.random.uniform(0, ltv_min * 0.3)

        return customer

    def _calculate_engagement_score(self, customer: Dict, profile: CustomerProfile) -> float:
        """Calculate engagement score based on customer behavior."""

        # Normalize factors
        message_factor = min(1.0, customer["message_count"] / (profile.typical_features["message_count_mean"] * 2))
        response_factor = max(0.1, 1.0 - customer["response_time"] / 1440)  # Faster response = higher score
        session_factor = min(1.0, customer["session_duration"] / (profile.typical_features["session_duration_mean"] * 2))

        # Weight factors
        engagement_score = (
            0.4 * message_factor +
            0.3 * response_factor +
            0.3 * session_factor
        )

        # Add noise
        engagement_score += np.random.normal(0, 0.1)

        return max(0.0, min(1.0, engagement_score))

    def _determine_conversion(self, customer: Dict, profile: CustomerProfile) -> int:
        """Determine if customer converted based on profile and behavior."""

        base_probability = profile.conversion_probability

        # Adjust based on engagement
        engagement_bonus = customer["engagement_score"] * 0.3

        # Budget influence
        budget_factor = 1.0
        if customer["budget"] > 100000:
            budget_factor = 1.2
        elif customer["budget"] < 10000:
            budget_factor = 0.8

        # Industry influence
        industry_factor = 1.0
        if customer["industry"] in ["technology", "finance"]:
            industry_factor = 1.1
        elif customer["industry"] == "retail":
            industry_factor = 0.9

        final_probability = base_probability + engagement_bonus
        final_probability *= budget_factor * industry_factor
        final_probability = max(0.0, min(1.0, final_probability))

        return 1 if np.random.random() < final_probability else 0

    def _determine_churn(self, customer: Dict, profile: CustomerProfile) -> int:
        """Determine if customer churned."""

        base_probability = profile.churn_probability

        # Recent activity reduces churn probability
        if customer["days_since_last_activity"] < 7:
            activity_factor = 0.5
        elif customer["days_since_last_activity"] < 30:
            activity_factor = 0.8
        else:
            activity_factor = 1.5

        # Support tickets increase churn probability
        support_factor = 1.0 + (customer["support_tickets"] * 0.1)

        # Engagement reduces churn
        engagement_factor = 1.0 - (customer["engagement_score"] * 0.5)

        final_probability = base_probability * activity_factor * support_factor * engagement_factor
        final_probability = max(0.0, min(1.0, final_probability))

        return 1 if np.random.random() < final_probability else 0

    def _determine_priority_level(self, customer: Dict) -> str:
        """Determine customer priority level."""

        score = 0

        # Budget influence
        if customer["budget"] > 100000:
            score += 3
        elif customer["budget"] > 50000:
            score += 2
        elif customer["budget"] > 20000:
            score += 1

        # Engagement influence
        if customer["engagement_score"] > 0.8:
            score += 2
        elif customer["engagement_score"] > 0.6:
            score += 1

        # Response time influence (faster = higher priority)
        if customer["response_time"] < 30:
            score += 1

        if score >= 4:
            return "urgent"
        elif score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_hour_preference(self) -> int:
        """Generate hour of day with business hours bias."""

        business_hours = self.feature_distributions["hour_of_day"]["business_hours"]
        off_hours = self.feature_distributions["hour_of_day"]["off_hours"]

        # 70% chance of business hours, 30% off hours
        if np.random.random() < 0.7:
            return np.random.choice(business_hours)
        else:
            return np.random.choice(off_hours)

    def _random_department(self) -> str:
        """Generate random department ID."""
        departments = ["sales", "marketing", "support", "product", "engineering", "finance"]
        return np.random.choice(departments)

    def _random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate random date between start and end."""
        time_delta = end_date - start_date
        random_days = np.random.randint(0, time_delta.days + 1)
        return start_date + timedelta(days=random_days)

    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to the dataset."""

        # Log transformations
        df["budget_log"] = np.log1p(df["budget"])
        df["message_count_log"] = np.log1p(df["message_count"])
        df["response_time_log"] = np.log1p(df["response_time"])

        # Ratio features
        df["message_per_day"] = df["message_count"] / (df["account_age_days"] + 1)
        df["support_ticket_rate"] = df["support_tickets"] / (df["account_age_days"] + 1) * 30

        # Engagement ratios
        mean_engagement = df["engagement_score"].mean()
        df["engagement_ratio"] = df["engagement_score"] / (mean_engagement + 1e-6)

        # Contact recency
        df["contact_recency"] = 1 / (df["days_since_last_activity"] + 1)

        # Categorical encodings
        df["industry_encoded"] = pd.Categorical(df["industry"]).codes
        df["company_size_encoded"] = pd.Categorical(df["company_size"]).codes
        df["contact_preference_encoded"] = pd.Categorical(df["contact_preference"]).codes
        df["priority_level_encoded"] = pd.Categorical(df["priority_level"]).codes

        return df

    def generate_time_series_data(
        self,
        customer_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        frequency: str = "D"
    ) -> pd.DataFrame:
        """Generate time series data for customer activity tracking."""

        date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
        time_series_data = []

        for customer_id in customer_ids:
            for date in date_range:
                # Simulate daily activity with some randomness
                activity_score = np.random.beta(2, 5)  # Skewed toward lower activity
                message_count = np.random.poisson(activity_score * 5)
                session_count = np.random.poisson(activity_score * 2)

                record = {
                    "customer_id": customer_id,
                    "date": date,
                    "activity_score": activity_score,
                    "daily_message_count": message_count,
                    "daily_session_count": session_count,
                    "cumulative_messages": 0,  # Would be calculated in real system
                    "trend_direction": np.random.choice(["up", "down", "stable"], p=[0.3, 0.2, 0.5])
                }

                time_series_data.append(record)

        df = pd.DataFrame(time_series_data)

        # Calculate cumulative metrics
        df["cumulative_messages"] = df.groupby("customer_id")["daily_message_count"].cumsum()

        return df


def create_demo_dataset(save_path: Optional[str] = None) -> pd.DataFrame:
    """Create a demo dataset for the Customer Intelligence Platform."""

    generator = SyntheticDataGenerator(random_seed=42)

    # Generate main customer dataset
    df = generator.generate_customer_dataset(
        num_customers=1000,
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        include_churn=True
    )

    # Save if path provided
    if save_path:
        df.to_csv(save_path, index=False)
        logger.info(f"Demo dataset saved to {save_path}")

    # Log dataset summary
    logger.info(f"Demo dataset created with {len(df)} customers")
    logger.info(f"Conversion rate: {df['converted'].mean():.2%}")
    logger.info(f"High engagement rate: {df['high_engagement'].mean():.2%}")
    logger.info(f"Churn rate: {df['churned'].mean():.2%}")

    return df


if __name__ == "__main__":
    # Generate demo dataset when run directly
    demo_data = create_demo_dataset("demo_customers.csv")
    print("Demo dataset generation complete!")
    print(f"Shape: {demo_data.shape}")
    print(f"Columns: {demo_data.columns.tolist()}")
    print("\nSample records:")
    print(demo_data.head())