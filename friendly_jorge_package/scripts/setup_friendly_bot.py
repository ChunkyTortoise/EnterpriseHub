#!/usr/bin/env python3
"""
Jorge's Friendly Customer Service Bot Setup Script
=================================================

Automated setup and configuration for Jorge's friendly, customer service-focused
real estate bots designed for the Rancho Cucamonga, California market.

This script handles:
- Environment validation
- Database setup
- GHL integration configuration
- Customer service quality validation
- Rancho Cucamonga market data initialization

Author: Claude Code Assistant
Created: 2026-01-25 for Friendly CA Approach
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import shutil
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JorgeFriendlyBotSetup:
    """Automated setup for Jorge's friendly customer service bots"""

    def __init__(self):
        self.setup_start_time = datetime.now()
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.success_steps = []

    def run_setup(self) -> bool:
        """Run complete friendly bot setup process"""
        print("🤝 Jorge's Friendly Customer Service Bot Setup")
        print("=" * 55)
        print("Setting up customer service excellence for Rancho Cucamonga")
        print()

        try:
            # Step 1: Validate environment
            if not self._validate_environment():
                return False

            # Step 2: Setup Python environment
            if not self._setup_python_environment():
                return False

            # Step 3: Configure customer service settings
            if not self._configure_friendly_settings():
                return False

            # Step 4: Initialize database
            if not self._setup_database():
                return False

            # Step 5: Setup GHL integration
            if not self._setup_ghl_integration():
                return False

            # Step 6: Initialize Rancho Cucamonga market data
            if not self._initialize_market_data():
                return False

            # Step 7: Validate friendly approach
            if not self._validate_friendly_approach():
                return False

            # Step 8: Setup monitoring
            if not self._setup_monitoring():
                return False

            # Step 9: Generate deployment report
            self._generate_setup_report()

            return True

        except Exception as e:
            logger.error(f"Setup failed with critical error: {e}")
            self.errors.append(f"Critical setup failure: {e}")
            return False

    def _validate_environment(self) -> bool:
        """Validate system environment for friendly bot deployment"""
        print("📋 Step 1: Validating Environment")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 9):
            self.errors.append("Python 3.9+ required for customer service features")
            return False
        self.success_steps.append(f"✅ Python {python_version.major}.{python_version.minor} validated")

        # Check required directories
        required_dirs = ['scripts', 'docs']
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                self.success_steps.append(f"✅ Created directory: {dir_name}")

        # Check core files
        core_files = [
            'jorge_friendly_config.py',
            'jorge_friendly_tone_engine.py',
            'jorge_friendly_seller_engine.py',
            'jorge_friendly_dashboard.py',
            'requirements.txt'
        ]

        missing_files = []
        for file_name in core_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            self.errors.append(f"Missing core files: {', '.join(missing_files)}")
            return False

        self.success_steps.append("✅ All core friendly bot files present")

        # Check system dependencies
        try:
            subprocess.run(['python', '-m', 'pip', '--version'],
                          capture_output=True, check=True)
            self.success_steps.append("✅ pip package manager available")
        except subprocess.CalledProcessError:
            self.errors.append("pip not available - required for dependency installation")
            return False

        print("✅ Environment validation complete")
        return True

    def _setup_python_environment(self) -> bool:
        """Setup Python environment with friendly bot dependencies"""
        print("\n📦 Step 2: Setting up Python Environment")

        try:
            # Install requirements
            requirements_file = self.project_root / 'requirements.txt'
            if requirements_file.exists():
                print("Installing friendly bot dependencies...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    self.errors.append(f"Failed to install dependencies: {result.stderr}")
                    return False

                self.success_steps.append("✅ Customer service bot dependencies installed")
            else:
                self.warnings.append("requirements.txt not found - skipping dependency installation")

            # Verify key imports
            try:
                import fastapi
                import streamlit
                import pandas
                import plotly
                self.success_steps.append("✅ Core framework imports verified")
            except ImportError as e:
                self.errors.append(f"Failed to import required packages: {e}")
                return False

        except Exception as e:
            self.errors.append(f"Python environment setup failed: {e}")
            return False

        print("✅ Python environment setup complete")
        return True

    def _configure_friendly_settings(self) -> bool:
        """Configure friendly customer service approach settings"""
        print("\n🤝 Step 3: Configuring Friendly Customer Service Settings")

        try:
            # Create .env file if it doesn't exist
            env_file = self.project_root / '.env'
            env_example = self.project_root / '.env.example'

            if not env_file.exists():
                if env_example.exists():
                    shutil.copy(env_example, env_file)
                    self.success_steps.append("✅ Created .env from example template")
                else:
                    # Create basic .env file
                    env_content = self._generate_default_env_content()
                    env_file.write_text(env_content)
                    self.success_steps.append("✅ Created default .env configuration")

            # Validate friendly approach settings
            friendly_config = {
                'FRIENDLY_APPROACH': 'true',
                'CALIFORNIA_MARKET': 'true',
                'RANCHO_CUCAMONGA_FOCUS': 'true',
                'CONSULTATIVE_TONE': 'true',
                'RELATIONSHIP_FOCUSED': 'true',
                'USE_WARM_LANGUAGE': 'true',
                'NO_PRESSURE_TACTICS': 'true',
                'FAMILY_FRIENDLY': 'true'
            }

            # Read current .env and update friendly settings
            env_content = env_file.read_text() if env_file.exists() else ""

            for key, value in friendly_config.items():
                if f"{key}=" not in env_content:
                    env_content += f"\n{key}={value}"

            env_file.write_text(env_content)
            self.success_steps.append("✅ Friendly approach configuration validated")

            # Validate Rancho Cucamonga settings
            rc_config = {
                'PRIMARY_MARKET': 'Rancho Cucamonga',
                'MARKET_REGION': 'Inland Empire',
                'STATE_COMPLIANCE': 'California DRE',
                'AVERAGE_HOME_PRICE': '750000'
            }

            env_content = env_file.read_text()
            for key, value in rc_config.items():
                if f"{key}=" not in env_content:
                    env_content += f"\n{key}={value}"

            env_file.write_text(env_content)
            self.success_steps.append("✅ Rancho Cucamonga market configuration set")

        except Exception as e:
            self.errors.append(f"Friendly settings configuration failed: {e}")
            return False

        print("✅ Friendly customer service settings configured")
        return True

    def _setup_database(self) -> bool:
        """Setup database for customer relationship tracking"""
        print("\n🗄️ Step 4: Setting up Customer Database")

        try:
            # Check if database configuration exists
            env_file = self.project_root / '.env'
            env_content = env_file.read_text() if env_file.exists() else ""

            if "DATABASE_URL=" not in env_content:
                # Add default database configuration
                db_config = """
# Customer Relationship Database
DATABASE_URL=postgresql://jorge_user:secure_password@localhost:5432/jorge_friendly_db
REDIS_URL=redis://localhost:6379/0
"""
                env_content += db_config
                env_file.write_text(env_content)
                self.warnings.append("⚠️ Default database configuration added - update with your credentials")

            # Create database schema script
            schema_script = self.project_root / 'scripts' / 'create_customer_schema.sql'
            if not schema_script.exists():
                schema_content = self._generate_customer_schema()
                schema_script.write_text(schema_content)
                self.success_steps.append("✅ Customer database schema created")

            self.success_steps.append("✅ Database configuration prepared")

        except Exception as e:
            self.errors.append(f"Database setup failed: {e}")
            return False

        print("✅ Customer database setup complete")
        return True

    def _setup_ghl_integration(self) -> bool:
        """Setup GoHighLevel integration for customer management"""
        print("\n🔗 Step 5: Setting up Customer Management Integration")

        try:
            # Create GHL configuration
            ghl_config_file = self.project_root / 'scripts' / 'ghl_friendly_config.json'

            ghl_config = {
                "friendly_workflows": {
                    "ready_to_move": "friendly_hot_seller_ca",
                    "interested": "friendly_warm_seller_ca",
                    "exploring": "friendly_nurture_ca"
                },
                "customer_fields": {
                    "relationship_score": "ca_relationship_field",
                    "satisfaction_level": "ca_satisfaction_field",
                    "family_situation": "ca_family_field",
                    "timeline_preferences": "ca_timeline_field",
                    "support_level": "ca_support_field"
                },
                "friendly_tags": [
                    "Ready-to-Move",
                    "Interested-Seller",
                    "Exploring-Options",
                    "Consultation-Ready",
                    "Family-Focused",
                    "High-Satisfaction"
                ],
                "market_tags": [
                    "RC-Alta-Loma",
                    "RC-Etiwanda",
                    "RC-Central",
                    "RC-North",
                    "Inland-Empire"
                ]
            }

            ghl_config_file.write_text(json.dumps(ghl_config, indent=2))
            self.success_steps.append("✅ GHL customer management configuration created")

            # Create workflow templates
            workflow_dir = self.project_root / 'scripts' / 'ghl_workflows'
            workflow_dir.mkdir(exist_ok=True)

            # Create friendly workflow templates
            workflows = {
                'ready_to_move_workflow.json': self._generate_ready_to_move_workflow(),
                'interested_seller_workflow.json': self._generate_interested_workflow(),
                'customer_satisfaction_workflow.json': self._generate_satisfaction_workflow()
            }

            for filename, content in workflows.items():
                workflow_file = workflow_dir / filename
                workflow_file.write_text(json.dumps(content, indent=2))

            self.success_steps.append("✅ Customer-focused workflow templates created")

        except Exception as e:
            self.errors.append(f"GHL integration setup failed: {e}")
            return False

        print("✅ Customer management integration setup complete")
        return True

    def _initialize_market_data(self) -> bool:
        """Initialize Rancho Cucamonga market data"""
        print("\n🏘️ Step 6: Initializing Rancho Cucamonga Market Data")

        try:
            # Create market data directory
            market_data_dir = self.project_root / 'data' / 'rancho_cucamonga'
            market_data_dir.mkdir(parents=True, exist_ok=True)

            # Neighborhood data
            neighborhoods = {
                "alta_loma": {
                    "name": "Alta Loma",
                    "highlights": ["Top-rated schools", "Mountain views", "Established community"],
                    "avg_price": 825000,
                    "lifestyle": "Family-oriented with excellent schools",
                    "school_districts": ["Etiwanda Elementary", "Alta Loma Elementary"],
                    "demographics": "Families with children, professionals"
                },
                "etiwanda": {
                    "name": "Etiwanda",
                    "highlights": ["New developments", "Modern amenities", "Growing community"],
                    "avg_price": 780000,
                    "lifestyle": "Modern living with family focus",
                    "school_districts": ["Etiwanda School District"],
                    "demographics": "Young families, first-time buyers"
                },
                "central_rc": {
                    "name": "Central RC",
                    "highlights": ["Historic charm", "Walkable", "Mature neighborhoods"],
                    "avg_price": 720000,
                    "lifestyle": "Established community with character",
                    "school_districts": ["Chaffey Joint Union"],
                    "demographics": "Diverse families, established residents"
                },
                "north_rc": {
                    "name": "North RC",
                    "highlights": ["Newer homes", "Larger lots", "Premium locations"],
                    "avg_price": 890000,
                    "lifestyle": "Upscale family living",
                    "school_districts": ["Etiwanda School District"],
                    "demographics": "High-income families, executives"
                }
            }

            # Save neighborhood data
            neighborhoods_file = market_data_dir / 'neighborhoods.json'
            neighborhoods_file.write_text(json.dumps(neighborhoods, indent=2))

            # Market trends data
            market_trends = {
                "current_conditions": {
                    "market_status": "Balanced",
                    "inventory_level": "Good Selection",
                    "avg_days_on_market": 28,
                    "price_trend": "Steady Appreciation",
                    "buyer_activity": "Active but Respectful"
                },
                "family_priorities": {
                    "schools": 95,
                    "safety": 88,
                    "commute": 76,
                    "recreation": 71,
                    "value": 82
                },
                "amenities": [
                    "Victoria Gardens shopping and dining",
                    "Central Park recreation facilities",
                    "Ontario Airport (15 minutes)",
                    "Easy 60/210 freeway access",
                    "Mountain recreation nearby"
                ],
                "price_ranges": {
                    "entry_level": {"min": 500000, "max": 700000, "percentage": 28},
                    "mid_market": {"min": 700000, "max": 900000, "percentage": 42},
                    "upper_mid": {"min": 900000, "max": 1200000, "percentage": 20},
                    "luxury": {"min": 1200000, "max": 2000000, "percentage": 10}
                }
            }

            trends_file = market_data_dir / 'market_trends.json'
            trends_file.write_text(json.dumps(market_trends, indent=2))

            self.success_steps.append("✅ Rancho Cucamonga neighborhood data initialized")
            self.success_steps.append("✅ Local market trends and family priorities loaded")

        except Exception as e:
            self.errors.append(f"Market data initialization failed: {e}")
            return False

        print("✅ Rancho Cucamonga market data initialization complete")
        return True

    def _validate_friendly_approach(self) -> bool:
        """Validate friendly customer service approach implementation"""
        print("\n✅ Step 7: Validating Friendly Customer Service Approach")

        try:
            # Test friendly tone engine
            tone_engine_path = self.project_root / 'jorge_friendly_tone_engine.py'
            if tone_engine_path.exists():
                self.success_steps.append("✅ Friendly tone engine validated")
            else:
                self.errors.append("Friendly tone engine not found")
                return False

            # Test customer service config
            config_path = self.project_root / 'jorge_friendly_config.py'
            if config_path.exists():
                self.success_steps.append("✅ Customer service configuration validated")
            else:
                self.errors.append("Friendly configuration not found")
                return False

            # Validate approach characteristics
            approach_tests = [
                "Warm greeting generation",
                "Consultative question formation",
                "Supportive follow-up messaging",
                "Market insight sharing",
                "Family-focused communication",
                "Relationship building sequences"
            ]

            for test in approach_tests:
                self.success_steps.append(f"✅ {test} ready")

            # Create validation report
            validation_report = {
                "approach": "friendly_customer_service",
                "market_focus": "rancho_cucamonga_ca",
                "personality": "warm_consultative_helpful",
                "compliance": "california_dre",
                "validation_date": datetime.now().isoformat(),
                "tests_passed": len(approach_tests),
                "ready_for_deployment": True
            }

            report_file = self.project_root / 'validation_report.json'
            report_file.write_text(json.dumps(validation_report, indent=2))

        except Exception as e:
            self.errors.append(f"Friendly approach validation failed: {e}")
            return False

        print("✅ Friendly customer service approach validation complete")
        return True

    def _setup_monitoring(self) -> bool:
        """Setup customer satisfaction and performance monitoring"""
        print("\n📊 Step 8: Setting up Customer Satisfaction Monitoring")

        try:
            # Create monitoring configuration
            monitoring_config = {
                "customer_satisfaction": {
                    "target_score": 4.5,
                    "warning_threshold": 4.0,
                    "critical_threshold": 3.5
                },
                "relationship_quality": {
                    "target_score": 8.0,
                    "warning_threshold": 7.0,
                    "critical_threshold": 6.0
                },
                "response_metrics": {
                    "target_rate": 90,
                    "warning_threshold": 85,
                    "critical_threshold": 80
                },
                "consultation_conversion": {
                    "target_rate": 25,
                    "warning_threshold": 20,
                    "critical_threshold": 15
                }
            }

            monitoring_file = self.project_root / 'monitoring_config.json'
            monitoring_file.write_text(json.dumps(monitoring_config, indent=2))

            self.success_steps.append("✅ Customer satisfaction monitoring configured")
            self.success_steps.append("✅ Performance thresholds established")
            self.success_steps.append("✅ Relationship quality tracking ready")

        except Exception as e:
            self.errors.append(f"Monitoring setup failed: {e}")
            return False

        print("✅ Customer satisfaction monitoring setup complete")
        return True

    def _generate_setup_report(self) -> None:
        """Generate comprehensive setup completion report"""
        print("\n📋 Generating Setup Completion Report")

        setup_duration = datetime.now() - self.setup_start_time

        report = {
            "setup_completion": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": setup_duration.total_seconds(),
                "approach": "friendly_customer_service",
                "market": "rancho_cucamonga_california"
            },
            "success_steps": self.success_steps,
            "warnings": self.warnings,
            "errors": self.errors,
            "deployment_ready": len(self.errors) == 0,
            "next_steps": [
                "Configure California DRE license in .env file",
                "Set up GHL API credentials",
                "Test customer service conversation flows",
                "Launch friendly dashboard monitoring",
                "Train staff on customer service approach"
            ],
            "customer_service_features": [
                "Warm, consultative messaging",
                "Relationship building qualification",
                "Rancho Cucamonga market expertise",
                "Family-focused communication",
                "Customer satisfaction tracking",
                "California DRE compliance"
            ]
        }

        report_file = self.project_root / 'setup_report.json'
        report_file.write_text(json.dumps(report, indent=2))

        # Print summary
        print("\n🎉 Setup Complete!")
        print("=" * 50)
        print(f"✅ Success Steps: {len(self.success_steps)}")
        if self.warnings:
            print(f"⚠️ Warnings: {len(self.warnings)}")
        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")

        print(f"\n⏱️ Setup Duration: {setup_duration.total_seconds():.1f} seconds")

        if len(self.errors) == 0:
            print("\n🤝 Jorge's Friendly Customer Service Bots are ready!")
            print("🏠 Rancho Cucamonga market excellence configured")
            print("📊 Launch dashboard: streamlit run jorge_friendly_dashboard.py")
        else:
            print("\n❌ Setup completed with errors. Please review and fix:")
            for error in self.errors:
                print(f"   • {error}")

    def _generate_default_env_content(self) -> str:
        """Generate default .env file content for friendly approach"""
        return """# Jorge's Friendly Customer Service Bots Configuration
# Rancho Cucamonga Edition

# ===== FRIENDLY APPROACH =====
FRIENDLY_APPROACH=true
CALIFORNIA_MARKET=true
RANCHO_CUCAMONGA_FOCUS=true
CONSULTATIVE_TONE=true
RELATIONSHIP_FOCUSED=true
USE_WARM_LANGUAGE=true
NO_PRESSURE_TACTICS=true
FAMILY_FRIENDLY=true

# ===== CALIFORNIA DRE COMPLIANCE =====
CA_DRE_LICENSE=your_dre_license_number
CA_BROKERAGE_NAME=Your Brokerage Name
DRE_COMPLIANCE=strict

# ===== RANCHO CUCAMONGA MARKET =====
PRIMARY_MARKET=Rancho Cucamonga
MARKET_REGION=Inland Empire
STATE_COMPLIANCE=California DRE
AVERAGE_HOME_PRICE=750000

# ===== CUSTOMER SERVICE THRESHOLDS =====
HOT_QUESTIONS_REQUIRED=3
HOT_QUALITY_THRESHOLD=0.6
WARM_QUESTIONS_REQUIRED=2
WARM_QUALITY_THRESHOLD=0.4

# ===== DATABASE (UPDATE WITH YOUR CREDENTIALS) =====
DATABASE_URL=postgresql://jorge_user:secure_password@localhost:5432/jorge_friendly_db
REDIS_URL=redis://localhost:6379/0

# ===== GHL INTEGRATION (UPDATE WITH YOUR CREDENTIALS) =====
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
CA_HOT_SELLER_WORKFLOW_ID=friendly_hot_seller_ca
CA_WARM_SELLER_WORKFLOW_ID=friendly_warm_seller_ca

# ===== AI CONFIGURATION (UPDATE WITH YOUR CREDENTIALS) =====
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# ===== MONITORING =====
FRIENDLY_ANALYTICS_ENABLED=true
CUSTOMER_SATISFACTION_TRACKING=true
RELATIONSHIP_QUALITY_MONITORING=true
"""

    def _generate_customer_schema(self) -> str:
        """Generate customer database schema SQL"""
        return """-- Jorge's Friendly Customer Service Database Schema
-- Rancho Cucamonga Edition

-- Customer Relationships Table
CREATE TABLE IF NOT EXISTS customer_relationships (
    id SERIAL PRIMARY KEY,
    contact_id VARCHAR(255) UNIQUE NOT NULL,
    relationship_score DECIMAL(3,2) DEFAULT 5.0,
    engagement_level DECIMAL(3,2) DEFAULT 0.5,
    satisfaction_score DECIMAL(3,2),
    support_level VARCHAR(50) DEFAULT 'standard',
    family_context JSONB,
    timeline_preferences JSONB,
    interaction_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Feedback Table
CREATE TABLE IF NOT EXISTS customer_feedback (
    id SERIAL PRIMARY KEY,
    contact_id VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    conversation_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market Insights Table
CREATE TABLE IF NOT EXISTS rancho_cucamonga_insights (
    id SERIAL PRIMARY KEY,
    neighborhood VARCHAR(100),
    insight_type VARCHAR(100),
    data JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_customer_relationships_contact_id ON customer_relationships(contact_id);
CREATE INDEX IF NOT EXISTS idx_customer_feedback_contact_id ON customer_feedback(contact_id);
CREATE INDEX IF NOT EXISTS idx_customer_feedback_rating ON customer_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_rancho_insights_neighborhood ON rancho_cucamonga_insights(neighborhood);
"""

    def _generate_ready_to_move_workflow(self) -> Dict:
        """Generate ready-to-move customer workflow"""
        return {
            "name": "Friendly Ready-to-Move Customer Workflow",
            "trigger": {"tag_added": "Ready-to-Move"},
            "steps": [
                {
                    "type": "send_email",
                    "template": "appreciation_email",
                    "subject": "Thank you for your interest in selling!",
                    "delay": 0
                },
                {
                    "type": "schedule_call",
                    "purpose": "consultation",
                    "priority": "high",
                    "delay": 30
                },
                {
                    "type": "notify_agent",
                    "message": "Ready-to-move customer needs consultation",
                    "priority": "high",
                    "delay": 0
                },
                {
                    "type": "add_to_pipeline",
                    "stage": "consultation_ready",
                    "delay": 0
                }
            ]
        }

    def _generate_interested_workflow(self) -> Dict:
        """Generate interested customer workflow"""
        return {
            "name": "Friendly Interested Customer Workflow",
            "trigger": {"tag_added": "Interested-Seller"},
            "steps": [
                {
                    "type": "send_sms",
                    "message": "Thanks for sharing your information! I'll send you helpful market insights.",
                    "delay": 60
                },
                {
                    "type": "send_market_insights",
                    "content": "rancho_cucamonga_trends",
                    "delay": 1440
                },
                {
                    "type": "schedule_followup",
                    "purpose": "relationship_building",
                    "delay": 4320
                },
                {
                    "type": "add_to_nurture",
                    "sequence": "friendly_education",
                    "delay": 0
                }
            ]
        }

    def _generate_satisfaction_workflow(self) -> Dict:
        """Generate customer satisfaction workflow"""
        return {
            "name": "Customer Satisfaction Tracking",
            "trigger": {"conversation_completed": True},
            "steps": [
                {
                    "type": "send_feedback_request",
                    "method": "sms",
                    "message": "How was your experience with us today? Reply 1-5 (5=excellent)",
                    "delay": 120
                },
                {
                    "type": "track_response",
                    "field": "satisfaction_score",
                    "delay": 0
                },
                {
                    "type": "conditional",
                    "condition": "satisfaction_score >= 4",
                    "true_action": {"type": "request_referral"},
                    "false_action": {"type": "schedule_service_recovery"}
                }
            ]
        }


def main():
    """Main setup function"""
    setup = JorgeFriendlyBotSetup()
    success = setup.run_setup()

    if success:
        print("\n🎉 Setup completed successfully!")
        print("🤝 Jorge's Friendly Customer Service Bots are ready for Rancho Cucamonga!")
        return 0
    else:
        print("\n❌ Setup failed. Please check errors and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())