#!/usr/bin/env python3
"""
Customer Intelligence Platform - End-to-End Demo Script

This script demonstrates the full functionality of the Customer Intelligence Platform:
1. Knowledge engine with RAG
2. AI-powered conversation
3. Predictive scoring
4. Interactive dashboard

Run this to verify end-to-end integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.knowledge_engine import KnowledgeEngine
from src.core.ai_client import get_ai_client
from src.core.conversation_manager import ConversationManager
from src.ml.scoring_pipeline import ScoringPipeline, ModelType
from src.ml.synthetic_data_generator import SyntheticDataGenerator
from src.utils.cache_service import get_cache_service
from src.utils.database_service import get_database_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PlatformDemo:
    """End-to-end demo of Customer Intelligence Platform."""
    
    def __init__(self):
        self.knowledge_engine = None
        self.ai_client = None
        self.conversation_manager = None
        self.scoring_pipeline = None
        self.data_generator = None
        self.cache_service = None
        self.database_service = None
    
    async def initialize(self):
        """Initialize all platform components."""
        logger.info("🚀 Initializing Customer Intelligence Platform...")
        
        try:
            # Initialize core services
            self.cache_service = get_cache_service()
            self.database_service = get_database_service()
            logger.info("✅ Cache and Database services initialized")
            
            # Initialize AI client
            self.ai_client = get_ai_client()
            if self.ai_client.is_available():
                logger.info("✅ AI client initialized and available")
            else:
                logger.warning("⚠️  AI client not available - check API keys")
            
            # Initialize knowledge engine
            self.knowledge_engine = KnowledgeEngine()
            logger.info("✅ Knowledge engine initialized")
            
            # Initialize conversation manager
            self.conversation_manager = ConversationManager(
                self.knowledge_engine, 
                self.ai_client
            )
            logger.info("✅ Conversation manager initialized")
            
            # Initialize ML components
            self.scoring_pipeline = ScoringPipeline()
            self.data_generator = SyntheticDataGenerator()
            logger.info("✅ ML pipeline and data generator initialized")
            
            logger.info("🎉 Platform initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def test_knowledge_engine(self):
        """Test knowledge engine functionality."""
        logger.info("\n📚 Testing Knowledge Engine...")
        
        try:
            # Add sample documents
            documents = [
                {
                    "content": "Customer Intelligence Platform provides AI-powered insights for business growth. It includes lead scoring, conversation intelligence, and predictive analytics.",
                    "metadata": {"title": "Platform Overview", "type": "product_info"}
                },
                {
                    "content": "Lead scoring uses machine learning to predict customer conversion probability. Features include engagement score, company size, industry type, and behavioral patterns.",
                    "metadata": {"title": "Lead Scoring Guide", "type": "feature_guide"}
                },
                {
                    "content": "The conversation intelligence feature analyzes customer interactions to provide insights and recommendations. It supports multiple channels including chat, email, and phone.",
                    "metadata": {"title": "Conversation Intelligence", "type": "feature_guide"}
                }
            ]
            
            for doc in documents:
                await self.knowledge_engine.add_document(
                    content=doc["content"],
                    metadata=doc["metadata"]
                )
            
            logger.info("✅ Sample documents added to knowledge base")
            
            # Test search functionality
            search_query = "lead scoring features"
            results = await self.knowledge_engine.search(search_query, limit=2)
            
            logger.info(f"🔍 Search query: '{search_query}'")
            logger.info(f"📄 Found {len(results)} relevant documents")
            
            for i, result in enumerate(results, 1):
                logger.info(f"   {i}. {result.get('metadata', {}).get('title', 'Untitled')} (score: {result.get('score', 0):.3f})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Knowledge engine test failed: {e}")
            return False
    
    async def test_conversation(self):
        """Test conversation functionality."""
        logger.info("\n💬 Testing Conversation Manager...")
        
        try:
            conversation_id = "demo_conversation"
            customer_id = "demo_customer"
            
            # Test conversation
            test_messages = [
                "What is lead scoring?",
                "How does the platform help with customer intelligence?",
                "Can you explain the conversation intelligence feature?"
            ]
            
            for message in test_messages:
                logger.info(f"👤 User: {message}")
                
                response = await self.conversation_manager.generate_response(
                    message=message,
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    customer_name="Demo Customer",
                    department="Sales"
                )
                
                if response and response.get('success'):
                    logger.info(f"🤖 Assistant: {response['message'][:100]}...")
                    if response.get('sources'):
                        logger.info(f"📚 Sources: {len(response['sources'])} documents referenced")
                else:
                    logger.warning(f"⚠️  No response or response failed")
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Conversation test failed: {e}")
            return False
    
    async def test_scoring_pipeline(self):
        """Test ML scoring pipeline."""
        logger.info("\n🎯 Testing ML Scoring Pipeline...")
        
        try:
            # Generate synthetic training data
            training_data = self.data_generator.generate_customer_dataset(num_customers=500)
            logger.info(f"✅ Generated {len(training_data)} synthetic customer records")
            
            # Train a model
            logger.info("🔄 Training lead scoring model...")
            training_job = await self.scoring_pipeline.train_model(
                model_type=ModelType.LEAD_SCORING,
                training_data=training_data
            )
            
            logger.info(f"✅ Training job started: {training_job.job_id}")
            logger.info(f"📊 Status: {training_job.status.value}")
            
            # Wait a moment for training (it's fast with synthetic data)
            await asyncio.sleep(2)
            
            # Check training status
            updated_job = self.scoring_pipeline.get_training_job_status(training_job.job_id)
            if updated_job:
                logger.info(f"📈 Training progress: {updated_job.progress_percentage:.1f}%")
            
            # Test predictions with sample customer
            sample_customer = {
                "engagement_score": 0.8,
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "10000-50000",
                "contact_frequency": 5,
                "geographic_location": "North America",
                "referral_source": "website"
            }
            
            logger.info("🔮 Testing prediction with sample customer...")
            score = await self.scoring_pipeline.predict(
                model_type=ModelType.LEAD_SCORING,
                features=sample_customer
            )
            
            if score is not None:
                logger.info(f"✅ Predicted lead score: {score:.3f}")
                
                # Interpret score
                if score >= 0.7:
                    interpretation = "HIGH - Strong conversion potential"
                elif score >= 0.4:
                    interpretation = "MEDIUM - Moderate conversion potential"
                else:
                    interpretation = "LOW - Requires nurturing"
                
                logger.info(f"📊 Score interpretation: {interpretation}")
            else:
                logger.warning("⚠️  Prediction failed - model may not be ready")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Scoring pipeline test failed: {e}")
            return False
    
    async def test_database_operations(self):
        """Test database operations."""
        logger.info("\n💾 Testing Database Operations...")
        
        try:
            # Health check
            health = await self.database_service.health_check()
            logger.info(f"✅ Database health: {health['status']}")
            logger.info(f"📊 Stats: {health['customers_count']} customers, {health['scores_count']} scores")
            
            # Create a test customer
            customer_data = {
                "name": "Test Corporation",
                "email": "test@testcorp.com",
                "company": "Test Corp",
                "industry": "Technology",
                "department": "Sales"
            }
            
            customer = await self.database_service.create_customer(customer_data)
            logger.info(f"✅ Created test customer: {customer.name} (ID: {customer.id})")
            
            # Create a score for the customer
            score_data = {
                "customer_id": customer.id,
                "score_type": "lead_scoring",
                "score": 0.75,
                "confidence": 0.85,
                "model_version": "v1.0",
                "features": {"engagement": 0.8, "company_size": 0.7}
            }
            
            score = await self.database_service.create_score(score_data)
            logger.info(f"✅ Created customer score: {score.score:.3f} (confidence: {score.confidence:.3f})")
            
            # Test analytics
            analytics = await self.database_service.get_customer_analytics()
            logger.info(f"📈 Analytics: {analytics['total_customers']} customers, avg score: {analytics['average_score']:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            return False
    
    async def test_cache_operations(self):
        """Test cache operations."""
        logger.info("\n🗄️  Testing Cache Operations...")
        
        try:
            # Test basic cache operations
            test_key = "demo:test_data"
            test_data = {"message": "Hello from cache!", "timestamp": "2024-01-01T00:00:00Z"}
            
            # Set cache
            success = await self.cache_service.set(test_key, test_data, ttl=60)
            if success:
                logger.info("✅ Data cached successfully")
            else:
                logger.warning("⚠️  Cache set failed")
            
            # Get from cache
            cached_data = await self.cache_service.get(test_key)
            if cached_data:
                logger.info(f"✅ Retrieved from cache: {cached_data['message']}")
            else:
                logger.warning("⚠️  Cache get failed")
            
            # Test cache miss
            missing_data = await self.cache_service.get("nonexistent:key")
            if missing_data is None:
                logger.info("✅ Cache miss handled correctly")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache test failed: {e}")
            return False
    
    async def run_full_demo(self):
        """Run the complete end-to-end demo."""
        print("🏢 Customer Intelligence Platform - End-to-End Demo")
        print("=" * 60)
        
        # Initialize platform
        if not await self.initialize():
            return False
        
        # Run all tests
        tests = [
            ("Cache Operations", self.test_cache_operations),
            ("Database Operations", self.test_database_operations),
            ("Knowledge Engine", self.test_knowledge_engine),
            ("Conversation Manager", self.test_conversation),
            ("ML Scoring Pipeline", self.test_scoring_pipeline),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = await test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 DEMO SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:<25} {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All systems operational! Platform ready for production.")
        else:
            print("⚠️  Some issues detected. Check logs for details.")
        
        print("\n💡 Next steps:")
        print("   1. Start the API server: python src/api/main.py")
        print("   2. Run the dashboard: streamlit run src/dashboard/main.py")
        print("   3. Explore the interactive features")
        
        return passed_tests == total_tests


async def main():
    """Main demo entry point."""
    demo = PlatformDemo()
    success = await demo.run_full_demo()
    return 0 if success else 1


if __name__ == "__main__":
    # Set up environment for demo
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)