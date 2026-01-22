import unittest
from datetime import datetime
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

class TestLeadIntentDecoder(unittest.TestCase):
    
    def setUp(self):
        self.decoder = LeadIntentDecoder()

    def test_high_intent_lead(self):
        # Mock conversation for a motivated seller
        conversation = [
            {"role": "user", "content": "I need to sell fast because I'm relocating for a job transfer."}, 
            {"role": "assistant", "content": "I understand. When do you need to move?"},
            {"role": "user", "content": "In 30 days. It's a deadline."}, 
            {"role": "assistant", "content": "Okay. How is the condition?"},
            {"role": "user", "content": "It needs work, I'm selling as-is. I know it's not perfect."}, 
            {"role": "assistant", "content": "And price?"},
            {"role": "user", "content": "I saw the Zestimate but I'm open to offers. I just need it sold."} 
        ]
        
        result = self.decoder.analyze_lead("lead_123", conversation, last_interaction_time=datetime.utcnow())
        
        print(f"\n--- High Intent Test Result ---")
        print(f"FRS Score: {result.frs.total_score} ({result.frs.classification})")
        print(f"Details: {result.frs.dict()}")
        
        self.assertGreaterEqual(result.frs.total_score, 75)
        self.assertEqual(result.frs.classification, "Hot Lead")
        self.assertEqual(result.frs.motivation.category, "High Intent")

    def test_low_intent_lead(self):
        conversation = [
            {"role": "user", "content": "Just browsing really. Not sure if I want to sell."}, 
            {"role": "assistant", "content": "No problem."}, 
            {"role": "user", "content": "Maybe next year if rates drop."}
        ]
        
        result = self.decoder.analyze_lead("lead_456", conversation)
        
        print(f"\n--- Low Intent Test Result ---")
        print(f"FRS Score: {result.frs.total_score} ({result.frs.classification})")
        
        self.assertLess(result.frs.total_score, 50)
        self.assertEqual(result.frs.classification, "Lukewarm")

if __name__ == '__main__':
    unittest.main()
