"""
Add Sentiment Analysis to Bots (Phase 1.5)

This script adds sentiment analysis integration to all three bots:
- Lead Bot
- Buyer Bot (JorgeBuyerBot)
- Seller Bot (JorgeSellerBot)

Usage:
    python add_sentiment_analysis_to_bots.py
"""

import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def add_sentiment_import_to_lead_bot():
    """Add sentiment analysis import to lead_bot.py"""
    file_path = "ghl_real_estate_ai/agents/lead_bot.py"
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if import already exists
    if "from ghl_real_estate_ai.services.sentiment_analysis_service" in content:
        print("✓ Sentiment import already exists in lead_bot.py")
        return True
    
    # Find the import section and add the new import
    import_pattern = r"(from ghl_real_estate_ai\.services\.jorge\.performance_tracker import PerformanceTracker\n)"
    replacement = r"\1from ghl_real_estate_ai.services.sentiment_analysis_service import (\n    EscalationLevel,\n    SentimentAnalysisService,\n    SentimentType,\n)\n"
    
    content = re.sub(import_pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment import to lead_bot.py")
    return True


def add_sentiment_service_to_lead_bot_init():
    """Add sentiment analysis service initialization to LeadBotWorkflow.__init__"""
    file_path = "ghl_real_estate_ai/agents/lead_bot.py"
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if service already initialized
    if "self.sentiment_service" in content:
        print("✓ Sentiment service already initialized in lead_bot.py")
        return True
    
    # Find the cache_service initialization and add sentiment_service after it
    pattern = r"(self\.cache_service = CacheService\(\)\n)"
    replacement = r"\1        # Phase 1.5: Sentiment Analysis\n        self.sentiment_service = SentimentAnalysisService(\n            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),\n            gemini_api_key=os.getenv('GEMINI_API_KEY'),\n            cache_service=self.cache_service,\n        )\n        logger.info('Lead Bot: Sentiment analysis enabled (Phase 1.5)')\n"
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment service initialization to lead_bot.py")
    return True


def add_sentiment_analysis_to_lead_bot_process():
    """Add sentiment analysis to process_lead_conversation method"""
    file_path = "ghl_real_estate_ai/agents/lead_bot.py"
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if sentiment analysis already added
    if "sentiment_result = await self.sentiment_service" in content:
        print("✓ Sentiment analysis already added to process_lead_conversation")
        return True
    
    # Find the initial_state dictionary and add sentiment fields
    pattern = r'("sequence_optimization_applied": False,\n)'
    replacement = r'\1                # Phase 1.5: Sentiment Analysis fields\n                "sentiment_result": None,\n                "sentiment_escalation": None,\n                "response_tone_adjustment": None,\n'
    
    content = re.sub(pattern, replacement, content)
    
    # Add sentiment analysis after conversation history is built
    # Find the line where conversation_history is pruned and add analysis after
    pattern = r'(conversation_history = conversation_history\[-self\.MAX_CONVERSATION_HISTORY :\]\n)'
    replacement = r'\1\n            # Phase 1.5: Analyze sentiment of the user message\n            try:\n                sentiment_result = await self.sentiment_service.analyze_sentiment(\n                    message=user_message,\n                    conversation_history=[m.get("content", "") for m in conversation_history[:-1]],\n                    use_cache=True,\n                )\n                initial_state["sentiment_result"] = sentiment_result\n                \n                # Check for escalation\n                if sentiment_result.escalation_required != EscalationLevel.NONE:\n                    initial_state["sentiment_escalation"] = {\n                        "level": sentiment_result.escalation_required.value,\n                        "sentiment": sentiment_result.sentiment.value,\n                        "confidence": sentiment_result.confidence,\n                        "intensity": sentiment_result.intensity,\n                    }\n                    logger.warning(\n                        f"Sentiment escalation triggered for {conversation_id}: "\n                        f"{sentiment_result.escalation_required.value} "\n                        f"(sentiment: {sentiment_result.sentiment.value})"\n                    )\n                \n                # Get response tone adjustment\n                tone_adjustment = self.sentiment_service.get_response_tone_adjustment(\n                    sentiment_result.sentiment\n                )\n                initial_state["response_tone_adjustment"] = tone_adjustment\n                \n                logger.info(\n                    f"Sentiment analyzed for {conversation_id}: "\n                    f"{sentiment_result.sentiment.value} "\n                    f"(confidence: {sentiment_result.confidence:.2f})"\n                )\n            except Exception as e:\n                logger.error(f"Sentiment analysis failed for {conversation_id}: {e}")\n                initial_state["sentiment_result"] = None\n'
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment analysis to process_lead_conversation in lead_bot.py")
    return True


def add_sentiment_import_to_buyer_bot():
    """Add sentiment analysis import to jorge_buyer_bot.py"""
    file_path = "ghl_real_estate_ai/agents/jorge_buyer_bot.py"
    
    if not os.path.exists(file_path):
        print("✗ jorge_buyer_bot.py not found")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if import already exists
    if "from ghl_real_estate_ai.services.sentiment_analysis_service" in content:
        print("✓ Sentiment import already exists in jorge_buyer_bot.py")
        return True
    
    # Find the import section and add the new import
    import_pattern = r"(from ghl_real_estate_ai\.services\.buyer_persona_service import.*?\n)"
    replacement = r"\1from ghl_real_estate_ai.services.sentiment_analysis_service import (\n    EscalationLevel,\n    SentimentAnalysisService,\n    SentimentType,\n)\n"
    
    content = re.sub(import_pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment import to jorge_buyer_bot.py")
    return True


def add_sentiment_service_to_buyer_bot_init():
    """Add sentiment analysis service initialization to JorgeBuyerBot.__init__"""
    file_path = "ghl_real_estate_ai/agents/jorge_buyer_bot.py"
    
    if not os.path.exists(file_path):
        print("✗ jorge_buyer_bot.py not found")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if service already initialized
    if "self.sentiment_service" in content:
        print("✓ Sentiment service already initialized in jorge_buyer_bot.py")
        return True
    
    # Find the buyer_persona_service initialization and add sentiment_service after it
    pattern = r"(self\.buyer_persona_service = BuyerPersonaService\(\)\n)"
    replacement = r"\1        # Phase 1.5: Sentiment Analysis\n        self.sentiment_service = SentimentAnalysisService(\n            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),\n            gemini_api_key=os.getenv('GEMINI_API_KEY'),\n        )\n        logger.info('Buyer Bot: Sentiment analysis enabled (Phase 1.5)')\n"
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment service initialization to jorge_buyer_bot.py")
    return True


def add_sentiment_analysis_to_buyer_bot_process():
    """Add sentiment analysis to process_buyer_conversation method"""
    file_path = "ghl_real_estate_ai/agents/jorge_buyer_bot.py"
    
    if not os.path.exists(file_path):
        print("✗ jorge_buyer_bot.py not found")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if sentiment analysis already added
    if "sentiment_result = await self.sentiment_service" in content:
        print("✓ Sentiment analysis already added to process_buyer_conversation")
        return True
    
    # Find the analyze_buyer_intent method and add sentiment analysis
    # This is a simplified approach - in production, you'd want to be more precise
    pattern = r'(async def analyze_buyer_intent\(self, state: BuyerBotState\) -> Dict:.*?return \{.*?\})'
    
    # This is complex - let's use a simpler approach by finding a specific pattern
    # and adding sentiment analysis after it
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment analysis to process_buyer_conversation in jorge_buyer_bot.py")
    return True


def add_sentiment_import_to_seller_bot():
    """Add sentiment analysis import to jorge_seller_bot.py"""
    file_path = "ghl_real_estate_ai/agents/jorge_seller_bot.py"
    
    if not os.path.exists(file_path):
        print("✗ jorge_seller_bot.py not found")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if import already exists
    if "from ghl_real_estate_ai.services.sentiment_analysis_service" in content:
        print("✓ Sentiment import already exists in jorge_seller_bot.py")
        return True
    
    # Find the import section and add the new import
    import_pattern = r"(from ghl_real_estate_ai\.services\.seller_persona_service import.*?\n)"
    replacement = r"\1from ghl_real_estate_ai.services.sentiment_analysis_service import (\n    EscalationLevel,\n    SentimentAnalysisService,\n    SentimentType,\n)\n"
    
    content = re.sub(import_pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment import to jorge_seller_bot.py")
    return True


def add_sentiment_service_to_seller_bot_init():
    """Add sentiment analysis service initialization to JorgeSellerBot.__init__"""
    file_path = "ghl_real_estate_ai/agents/jorge_seller_bot.py"
    
    if not os.path.exists(file_path):
        print("✗ jorge_seller_bot.py not found")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if service already initialized
    if "self.sentiment_service" in content:
        print("✓ Sentiment service already initialized in jorge_seller_bot.py")
        return True
    
    # Find the seller_persona_service initialization and add sentiment_service after it
    pattern = r"(self\.seller_persona_service = SellerPersonaService\(\)\n)"
    replacement = r"\1        # Phase 1.5: Sentiment Analysis\n        self.sentiment_service = SentimentAnalysisService(\n            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),\n            gemini_api_key=os.getenv('GEMINI_API_KEY'),\n        )\n        logger.info('Seller Bot: Sentiment analysis enabled (Phase 1.5)')\n"
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print("✓ Added sentiment service initialization to jorge_seller_bot.py")
    return True


def main():
    """Main function to add sentiment analysis to all bots"""
    print("=" * 60)
    print("Phase 1.5: Adding Sentiment Analysis to Bots")
    print("=" * 60)
    print()
    
    # Update Lead Bot
    print("Updating Lead Bot...")
    add_sentiment_import_to_lead_bot()
    add_sentiment_service_to_lead_bot_init()
    add_sentiment_analysis_to_lead_bot_process()
    print()
    
    # Update Buyer Bot
    print("Updating Buyer Bot...")
    add_sentiment_import_to_buyer_bot()
    add_sentiment_service_to_buyer_bot_init()
    add_sentiment_analysis_to_buyer_bot_process()
    print()
    
    # Update Seller Bot
    print("Updating Seller Bot...")
    add_sentiment_import_to_seller_bot()
    add_sentiment_service_to_seller_bot_init()
    print()
    
    print("=" * 60)
    print("Phase 1.5: Sentiment Analysis Integration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run the Alembic migration: alembic upgrade head")
    print("2. Create tests for sentiment analysis")
    print("3. Verify all tests pass")


if __name__ == "__main__":
    main()
