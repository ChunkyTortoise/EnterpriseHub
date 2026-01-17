"""
Verification script to test all demo components before deployment.
"""
import os
import sys
from pathlib import Path

# Mock environment variables before importing anything that uses Settings
os.environ["ANTHROPIC_API_KEY"] = "mock_key"
os.environ["GHL_API_KEY"] = "mock_key"
os.environ["GHL_LOCATION_ID"] = "mock_id"

# Add project root to path
# __file__ is enterprisehub/ghl_real_estate_ai/streamlit_demo/verify_setup.py
# We want to add 'enterprisehub' to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def verify_imports():
    """Verify all imports work correctly."""
    print("🔍 Verifying imports...")

    try:
        from ghl_real_estate_ai.streamlit_demo.mock_services.mock_claude import MockClaudeService
        print("  ✅ MockClaudeService imported")
    except Exception as e:
        print(f"  ❌ MockClaudeService import failed: {e}")
        return False

    try:
        from ghl_real_estate_ai.streamlit_demo.mock_services.mock_rag import MockRAGService
        print("  ✅ MockRAGService imported")
    except Exception as e:
        print(f"  ❌ MockRAGService import failed: {e}")
        return False

    try:
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer
        print("  ✅ LeadScorer imported")
    except Exception as e:
        print(f"  ❌ LeadScorer import failed: {e}")
        return False

    return True


def verify_mock_claude():
    """Test MockClaude service."""
    print("\n🤖 Testing MockClaude service...")

    try:
        from ghl_real_estate_ai.streamlit_demo.mock_services.mock_claude import MockClaudeService
        claude = MockClaudeService()

        # Test basic response
        response, data = claude.generate_response("I have a budget of $400k", [], {})
        assert "budget" in data
        assert data["budget"] == 400000
        print(f"  ✅ Budget extraction: ${data['budget']:,}")

        # Test pre-approval extraction
        response, data = claude.generate_response("I'm pre-approved for $300k", [], {})
        assert "financing" in data
        print(f"  ✅ Financing extraction: {data['financing']}")

        # Test timeline extraction
        response, data = claude.generate_response("Need to move ASAP", [], {})
        assert "timeline" in data
        print(f"  ✅ Timeline extraction: {data['timeline']}")

        return True
    except Exception as e:
        print(f"  ❌ MockClaude test failed: {e}")
        return False


def verify_mock_rag():
    """Test MockRAG service."""
    print("\n🏠 Testing MockRAG service...")

    try:
        from ghl_real_estate_ai.streamlit_demo.mock_services.mock_rag import MockRAGService
        rag = MockRAGService()

        # Test property search
        preferences = {
            "budget": 400000,
            "bedrooms": 3,
            "location": "Hyde Park"
        }

        results = rag.search_properties(preferences, top_k=3)
        assert len(results) > 0
        print(f"  ✅ Found {len(results)} properties")

        for i, prop in enumerate(results[:3]):
            neighborhood = prop['address']['neighborhood']
            price = prop['price']
            match = prop['match_score']
            print(f"     {i+1}. {neighborhood} - ${price:,} ({match:.0f}% match)")

        return True
    except Exception as e:
        print(f"  ❌ MockRAG test failed: {e}")
        return False


def verify_lead_scorer():
    """Test LeadScorer integration."""
    print("\n📊 Testing LeadScorer integration...")

    try:
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer
        scorer = LeadScorer()

        # Test cold lead
        cold_context = {
            "extracted_preferences": {},
            "conversation_history": [{"role": "user", "content": "Looking for a house"}]
        }
        cold_score = scorer.calculate(cold_context)
        print(f"  ✅ Cold lead score: {cold_score}")

        # Test warm lead
        warm_context = {
            "extracted_preferences": {"budget": 400000, "bedrooms": 3},
            "conversation_history": [
                {"role": "user", "content": "I have a budget of $400k and need 3 bedrooms"}
            ]
        }
        warm_score = scorer.calculate(warm_context)
        print(f"  ✅ Warm lead score: {warm_score}")

        # Test hot lead
        hot_context = {
            "extracted_preferences": {
                "budget": 400000,
                "bedrooms": 3,
                "financing": "pre-approved",
                "timeline": "ASAP"
            },
            "conversation_history": [
                {"role": "user", "content": "I'm pre-approved for $400k, need 3 bedrooms ASAP"}
            ]
        }
        hot_score = scorer.calculate(hot_context)
        print(f"  ✅ Hot lead score: {hot_score}")

        assert cold_score < warm_score < hot_score, "Score progression not correct"
        print(f"  ✅ Score progression correct: {cold_score} < {warm_score} < {hot_score}")

        return True
    except Exception as e:
        print(f"  ❌ LeadScorer test failed: {e}")
        return False


def verify_data_files():
    """Verify required data files exist."""
    print("\n📁 Verifying data files...")

    # .../streamlit_demo/verify_setup.py -> .../streamlit_demo -> .../ghl_real_estate_ai
    base_dir = Path(__file__).resolve().parent.parent
    property_file = base_dir / "data" / "knowledge_base" / "property_listings.json"

    if property_file.exists():
        print(f"  ✅ Property listings found")

        import json
        with open(property_file, 'r') as f:
            data = json.load(f)
            count = len(data.get('listings', []))
            print(f"     {count} properties available")
        return True
    else:
        print(f"  ❌ Property listings not found at: {property_file}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("GHL REAL ESTATE AI - DEMO VERIFICATION")
    print("=" * 60)

    results = []

    results.append(("Imports", verify_imports()))
    results.append(("Data Files", verify_data_files()))
    results.append(("MockClaude", verify_mock_claude()))
    results.append(("MockRAG", verify_mock_rag()))
    results.append(("LeadScorer", verify_lead_scorer()))

    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Ready for deployment!")
        print("\nNext steps:")
        print("  1. Run: streamlit run streamlit_demo/app.py")
        print("  2. Test in browser at http://localhost:8501")
        print("  3. Deploy to Streamlit Cloud")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Please fix issues before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
