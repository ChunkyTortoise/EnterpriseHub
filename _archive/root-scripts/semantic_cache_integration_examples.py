"""
Semantic Cache Integration Examples
How to integrate semantic response caching into existing EnterpriseHub services

This shows practical integration patterns for the semantic caching system.
"""

import asyncio
from typing import Dict, Any, List
from ghl_real_estate_ai.services.semantic_response_caching import (
    create_semantic_cache, 
    EmbeddingProvider,
    SemanticCacheIntegration
)

# ============================================================================
# EXAMPLE 1: Claude Assistant Integration
# ============================================================================

class ClaudeAssistantWithSemanticCache:
    """Enhanced Claude Assistant with semantic caching"""
    
    def __init__(self):
        # Initialize semantic cache with 85% similarity threshold
        self.semantic_cache = create_semantic_cache(
            embedding_provider=EmbeddingProvider.SENTENCE_BERT,
            similarity_threshold=0.85,
            max_cache_size=5000,
            default_ttl=3600  # 1 hour
        )
        
        # Initialize existing Claude assistant
        try:
            from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
            self.claude_assistant = ClaudeAssistant()
        except ImportError:
            self.claude_assistant = None
    
    async def explain_match_with_semantic_cache(
        self, 
        property_data: Dict[str, Any], 
        lead_preferences: Dict[str, Any],
        conversation_history: List[str] = None
    ) -> str:
        """
        Enhanced property explanation with semantic caching
        
        This will cache responses for similar property-lead combinations
        """
        # Create cache key from the request parameters
        cache_key_data = {
            "property_price": property_data.get("price"),
            "property_beds": property_data.get("beds"),
            "property_location": property_data.get("city"),
            "lead_budget": lead_preferences.get("max_budget"),
            "lead_preferences": lead_preferences.get("must_haves", [])
        }
        
        query_text = f"Explain property match: {cache_key_data}"
        
        async def compute_explanation():
            """Actual Claude computation - only called on cache miss"""
            if self.claude_assistant:
                return await self.claude_assistant.explain_match_with_claude(
                    property_data, lead_preferences, conversation_history
                )
            else:
                # Mock response for demonstration
                return f"This property matches your preferences because..."
        
        response, was_cached, similarity = await self.semantic_cache.get_or_set(
            query_text=query_text,
            compute_function=compute_explanation,
            context_tags=["property_explanation", lead_preferences.get("type", "buyer")],
            user_id=lead_preferences.get("lead_id"),
            ttl=1800  # 30 minutes for property explanations
        )
        
        return response, {
            "cached": was_cached,
            "similarity_score": similarity,
            "cache_type": "semantic" if was_cached and similarity < 1.0 else "exact"
        }

# ============================================================================
# EXAMPLE 2: Property Matching Integration  
# ============================================================================

class PropertyMatcherWithSemanticCache:
    """Enhanced property matcher with semantic caching"""
    
    def __init__(self):
        # Initialize semantic cache optimized for property searches
        self.semantic_cache = create_semantic_cache(
            embedding_provider=EmbeddingProvider.SENTENCE_BERT,
            similarity_threshold=0.90,  # Higher threshold for property matching
            max_cache_size=10000,
            default_ttl=7200  # 2 hours
        )
        
        try:
            from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
            self.property_matcher = PropertyMatcher()
        except ImportError:
            self.property_matcher = None
    
    async def find_properties_with_semantic_cache(
        self,
        search_criteria: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Find properties with semantic caching for similar searches
        
        Examples of similar searches that would hit the cache:
        - "3 bedroom house under $500k" vs "3 br home below 500000"
        - "Downtown Rancho Cucamonga condo" vs "Rancho Cucamonga city center apartment"
        """
        
        # Normalize search criteria for better cache hits
        normalized_criteria = self._normalize_search_criteria(search_criteria)
        query_text = self._create_search_query_text(normalized_criteria)
        
        async def compute_property_search():
            """Actual property search - only called on cache miss"""
            if self.property_matcher:
                return await self.property_matcher.find_matches(normalized_criteria)
            else:
                # Mock response
                return {
                    "properties": [],
                    "total_found": 0,
                    "search_criteria": normalized_criteria
                }
        
        result, was_cached, similarity = await self.semantic_cache.get_or_set(
            query_text=query_text,
            compute_function=compute_property_search,
            context_tags=["property_search", normalized_criteria.get("location", "general")],
            user_id=user_id,
            ttl=3600  # 1 hour for property searches
        )
        
        # Add cache metadata to result
        result["cache_info"] = {
            "was_cached": was_cached,
            "similarity_score": similarity,
            "query_text": query_text
        }
        
        return result
    
    def _normalize_search_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize search criteria for better cache matching"""
        normalized = {}
        
        # Standardize price ranges
        if "max_price" in criteria:
            # Round to nearest 10k for better cache hits
            normalized["max_price"] = round(criteria["max_price"] / 10000) * 10000
        
        # Standardize bedroom counts
        if "bedrooms" in criteria:
            normalized["bedrooms"] = criteria["bedrooms"]
        
        # Standardize location
        if "location" in criteria:
            normalized["location"] = criteria["location"].lower().strip()
        
        # Standardize property type
        if "property_type" in criteria:
            type_mapping = {
                "house": "single_family",
                "home": "single_family", 
                "condo": "condominium",
                "apartment": "condominium"
            }
            prop_type = criteria["property_type"].lower()
            normalized["property_type"] = type_mapping.get(prop_type, prop_type)
        
        return normalized
    
    def _create_search_query_text(self, criteria: Dict[str, Any]) -> str:
        """Create standardized query text for semantic matching"""
        parts = []
        
        if "bedrooms" in criteria:
            parts.append(f"{criteria['bedrooms']} bedrooms")
            
        if "property_type" in criteria:
            parts.append(criteria["property_type"])
            
        if "max_price" in criteria:
            parts.append(f"under ${criteria['max_price']:,}")
            
        if "location" in criteria:
            parts.append(f"in {criteria['location']}")
        
        return " ".join(parts)

# ============================================================================
# EXAMPLE 3: Lead Intelligence Integration
# ============================================================================

class LeadIntelligenceWithSemanticCache:
    """Enhanced lead intelligence with semantic caching"""
    
    def __init__(self):
        self.semantic_cache = create_semantic_cache(
            embedding_provider=EmbeddingProvider.SENTENCE_BERT,
            similarity_threshold=0.88,
            max_cache_size=3000,
            default_ttl=1800  # 30 minutes
        )
        
        try:
            from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
            self.lead_intelligence = EnhancedLeadIntelligence()
        except ImportError:
            self.lead_intelligence = None
    
    async def analyze_lead_with_semantic_cache(
        self,
        lead_data: Dict[str, Any],
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Analyze lead with semantic caching for similar profiles
        
        Similar leads that would hit cache:
        - First-time buyers with similar budgets and preferences
        - Investors looking for similar property types
        - Families with comparable demographics
        """
        
        # Create semantic query based on lead characteristics
        query_components = []
        
        if lead_data.get("budget_range"):
            budget = lead_data["budget_range"]
            query_components.append(f"budget {budget}")
        
        if lead_data.get("family_status"):
            query_components.append(f"family status {lead_data['family_status']}")
        
        if lead_data.get("buyer_type"):
            query_components.append(f"buyer type {lead_data['buyer_type']}")
        
        if lead_data.get("location_preferences"):
            locations = ", ".join(lead_data["location_preferences"])
            query_components.append(f"interested in {locations}")
        
        query_text = f"Lead analysis for: {' '.join(query_components)}"
        
        async def compute_lead_analysis():
            """Actual lead analysis - only called on cache miss"""
            if self.lead_intelligence:
                return await self.lead_intelligence.analyze_lead(lead_data, analysis_type)
            else:
                # Mock response
                return {
                    "lead_score": 75,
                    "recommendations": ["Schedule showing", "Send market report"],
                    "risk_factors": [],
                    "predicted_value": "$450,000"
                }
        
        result, was_cached, similarity = await self.semantic_cache.get_or_set(
            query_text=query_text,
            compute_function=compute_lead_analysis,
            context_tags=["lead_analysis", lead_data.get("buyer_type", "general")],
            user_id=lead_data.get("lead_id"),
            ttl=900  # 15 minutes for lead analysis
        )
        
        # Add cache performance info
        result["semantic_cache_info"] = {
            "cached": was_cached,
            "similarity": similarity,
            "query_matched": query_text
        }
        
        return result

# ============================================================================
# EXAMPLE 4: Integration with Conversation Manager
# ============================================================================

async def integrate_semantic_cache_with_conversation_manager():
    """Example of integrating semantic cache with conversation management"""
    
    semantic_cache = create_semantic_cache(
        embedding_provider=EmbeddingProvider.SENTENCE_BERT,
        similarity_threshold=0.85,
        max_cache_size=2000,
        default_ttl=1800
    )
    
    # Mock conversation manager for example
    class MockConversationManager:
        async def get_response(self, query: str, context: Dict) -> str:
            return f"AI response to: {query}"
    
    conversation_manager = MockConversationManager()
    
    # Create cached version using integration helper
    cached_conversation = await SemanticCacheIntegration.integrate_with_conversation_manager(
        conversation_manager, semantic_cache
    )
    
    # Example usage
    context = {"user_id": "lead_123", "type": "property_inquiry"}
    
    # These queries are semantically similar and would hit cache:
    queries = [
        "What houses do you have under $400k?",
        "Show me homes below 400000 dollars",
        "Any properties available under four hundred thousand?",
        "Houses for sale under $400k"
    ]
    
    results = []
    for query in queries:
        response, was_cached, similarity = await cached_conversation(query, context)
        results.append({
            "query": query,
            "response": response,
            "cached": was_cached, 
            "similarity": similarity
        })
    
    return results

# ============================================================================
# EXAMPLE 5: Performance Monitoring Integration
# ============================================================================

class SemanticCacheMonitor:
    """Monitor semantic cache performance and provide insights"""
    
    def __init__(self, semantic_cache):
        self.semantic_cache = semantic_cache
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        stats = await self.semantic_cache.get_cache_stats()
        
        # Calculate additional metrics
        hit_rate = stats.cache_hits / max(stats.total_queries, 1) * 100
        semantic_hit_rate = stats.semantic_hits / max(stats.cache_hits, 1) * 100
        
        return {
            "overview": {
                "total_queries": stats.total_queries,
                "cache_hit_rate": f"{hit_rate:.1f}%",
                "semantic_hit_rate": f"{semantic_hit_rate:.1f}%",
                "avg_similarity_score": f"{stats.avg_similarity_score:.3f}",
                "estimated_cost_saved": f"${stats.total_cost_saved:.2f}",
                "avg_response_time": f"{stats.avg_response_time_ms:.1f}ms"
            },
            "recommendations": self._generate_recommendations(stats, hit_rate, semantic_hit_rate),
            "raw_stats": stats
        }
    
    def _generate_recommendations(self, stats, hit_rate: float, semantic_hit_rate: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if hit_rate < 50:
            recommendations.append("Consider increasing cache TTL or adjusting similarity threshold")
        
        if semantic_hit_rate < 20:
            recommendations.append("Similarity threshold might be too high - consider lowering to 0.80-0.85")
        
        if stats.avg_response_time_ms > 100:
            recommendations.append("Consider using a faster embedding model or optimizing similarity search")
        
        if stats.avg_similarity_score < 0.90:
            recommendations.append("Review query normalization to improve semantic matching quality")
        
        return recommendations

# ============================================================================
# EXAMPLE 6: Testing and Validation
# ============================================================================

async def test_semantic_cache_integration():
    """Comprehensive test of semantic cache integration"""
    
    print("Testing Semantic Cache Integration")
    print("=" * 50)
    
    # Test 1: Basic functionality
    print("1. Testing basic semantic cache...")
    cache = create_semantic_cache()
    
    async def mock_expensive_operation():
        await asyncio.sleep(0.1)  # Simulate processing time
        return "Expensive operation result"
    
    # First call - cache miss
    result1, cached1, similarity1 = await cache.get_or_set(
        "What is the weather like?",
        mock_expensive_operation
    )
    print(f"   First call: cached={cached1}, similarity={similarity1:.3f}")
    
    # Second call - exact match
    result2, cached2, similarity2 = await cache.get_or_set(
        "What is the weather like?",
        mock_expensive_operation
    )
    print(f"   Exact match: cached={cached2}, similarity={similarity2:.3f}")
    
    # Third call - semantic match
    result3, cached3, similarity3 = await cache.get_or_set(
        "How is the weather today?",
        mock_expensive_operation
    )
    print(f"   Semantic match: cached={cached3}, similarity={similarity3:.3f}")
    
    # Test 2: Property matching integration
    print("\n2. Testing property matching integration...")
    property_matcher = PropertyMatcherWithSemanticCache()
    
    search1 = {"bedrooms": 3, "max_price": 500000, "location": "Rancho Cucamonga"}
    result1 = await property_matcher.find_properties_with_semantic_cache(search1)
    print(f"   First search: cached={result1['cache_info']['was_cached']}")
    
    search2 = {"bedrooms": 3, "max_price": 495000, "location": "rancho_cucamonga"}  # Similar search
    result2 = await property_matcher.find_properties_with_semantic_cache(search2)
    print(f"   Similar search: cached={result2['cache_info']['was_cached']}, similarity={result2['cache_info']['similarity_score']:.3f}")
    
    # Test 3: Performance monitoring
    print("\n3. Testing performance monitoring...")
    monitor = SemanticCacheMonitor(cache)
    report = await monitor.get_performance_report()
    print(f"   Cache hit rate: {report['overview']['cache_hit_rate']}")
    print(f"   Recommendations: {len(report['recommendations'])}")
    
    print("\nSemantic cache integration test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_semantic_cache_integration())