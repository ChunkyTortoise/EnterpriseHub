
import sys
import os
sys.path.append(os.getcwd())

def test_enhanced_scorer_type_error():
    from enterprisehub.ghl_real_estate_ai.services.enhanced_lead_scorer import EnhancedLeadScorer
    
    scorer = EnhancedLeadScorer()
    
    # Test case with list in message content
    context = {
        'conversation_history': [
            {'content': ['Hello', 'World']}, # List instead of string
            {'content': 'Normal message'}
        ],
        'extracted_preferences': {}
    }
    
    try:
        # This triggered the error in my hypothesis
        lead_data = scorer._convert_context_to_lead_data(context)
        print("Conversion successful")
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {type(e).__name__}: {e}")

def test_predictive_next_action():
    from enterprisehub.ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
    scorer = PredictiveLeadScorer()
    if hasattr(scorer, 'predict_next_action'):
        print("PredictiveLeadScorer.predict_next_action exists")
    else:
        print("PredictiveLeadScorer.predict_next_action MISSING")

if __name__ == "__main__":
    print("Testing PredictiveLeadScorer...")
    test_predictive_next_action()
    print("\nTesting EnhancedLeadScorer TypeError...")
    test_enhanced_scorer_type_error()
