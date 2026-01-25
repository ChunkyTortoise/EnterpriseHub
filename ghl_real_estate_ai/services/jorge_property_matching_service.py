"""
Jorge's Property Matching Service - Hybrid Neural + Rules Engine

Intelligent property-lead matching using neural networks combined with
Rancho Cucamonga market-specific business rules for optimal recommendations.

Features:
- Hybrid neural + rule-based scoring (60/40 blend)
- Real-time matching with <500ms response time
- Integration with Enhanced Lead Scorer for context
- Jorge-specific talking points and explanations
- Performance caching with Redis TTL
- Market intelligence integration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.enhanced_smart_lead_scorer import (
    EnhancedSmartLeadScorer, LeadScoreBreakdown, LeadPriority, BuyingStage
)
from ghl_real_estate_ai.ml.neural_property_matcher import NeuralPropertyMatcher
from ghl_real_estate_ai.models.jorge_property_models import (
    Property, PropertyMatch, PropertyMatchRequest, PropertyMatchResponse,
    LeadPropertyPreferences, MatchReasoning, ConfidenceLevel, MatchingAlgorithm,
    PropertyFilters, MatchingPerformanceMetrics
)

logger = get_logger(__name__)
cache_service = get_cache_service()

# Performance constants
NEURAL_WEIGHT = 0.6  # 60% neural, 40% rules for Jorge's optimized algorithm
RULES_WEIGHT = 0.4
CACHE_TTL_MATCHES = 300  # 5 minutes for match results
CACHE_TTL_PREFERENCES = 3600  # 1 hour for lead preferences
CACHE_TTL_INVENTORY = 1800  # 30 minutes for property inventory


class JorgePropertyMatchingService:
    """
    Advanced property matching service combining neural networks with
    Jorge's market-specific business intelligence.
    """

    def __init__(self,
                 enhanced_scorer: Optional[EnhancedSmartLeadScorer] = None,
                 neural_matcher: Optional[NeuralPropertyMatcher] = None,
                 claude_assistant: Optional[ClaudeAssistant] = None):
        """Initialize the property matching service."""
        self.enhanced_scorer = enhanced_scorer or EnhancedSmartLeadScorer()
        self.neural_matcher = neural_matcher  # Will be initialized lazily if available
        self.claude_assistant = claude_assistant or ClaudeAssistant()

        # Performance tracking
        self.performance_metrics = {
            'total_matches_generated': 0,
            'avg_processing_time_ms': 0,
            'neural_inference_time_ms': 0,
            'rules_processing_time_ms': 0,
            'cache_hit_rate': 0.0
        }

        # Rancho Cucamonga market intelligence
        self.market_data = self._load_rancho_cucamonga_intelligence()

    def _load_rancho_cucamonga_intelligence(self) -> Dict[str, Any]:
        """Load Jorge's market-specific intelligence."""
        return {
            # Neighborhood priorities (Jorge's expertise)
            "premium_neighborhoods": [
                "Alta Loma", "North Rancho Cucamonga", "Victoria Arbors",
                "Red Hill Country Club", "Etiwanda Heights"
            ],
            "emerging_neighborhoods": [
                "Central Rancho", "South Rancho", "Terra Vista"
            ],
            "family_neighborhoods": [
                "Deer Creek", "Los Osos", "Victoria Gardens Area"
            ],

            # School district insights
            "top_school_districts": {
                "Chaffey Joint Union": {"rating": 8, "premium": 1.15},
                "Cucamonga Elementary": {"rating": 9, "premium": 1.25},
                "Central Elementary": {"rating": 7, "premium": 1.05}
            },

            # Property type preferences by price range
            "price_segment_preferences": {
                "luxury": {"min": 900000, "types": ["single_family", "luxury_home"]},
                "upper": {"min": 650000, "max": 899999, "types": ["single_family", "townhome"]},
                "middle": {"min": 450000, "max": 649999, "types": ["single_family", "townhome", "condo"]},
                "starter": {"max": 449999, "types": ["townhome", "condo"]}
            },

            # Market timing factors
            "seasonal_factors": {
                "spring": 1.2,  # High demand
                "summer": 1.1,  # Good demand
                "fall": 0.9,    # Cooling
                "winter": 0.8   # Slower market
            },

            # Jorge's negotiation insights
            "negotiation_factors": {
                "days_on_market_advantage": {15: "strong", 30: "good", 60: "opportunity", 90: "motivated"},
                "inventory_level_impact": {"low": 1.1, "normal": 1.0, "high": 0.9}
            }
        }

    async def find_matches_for_lead(self,
                                   request: PropertyMatchRequest) -> PropertyMatchResponse:
        """
        Find optimal property matches for a lead using hybrid AI approach.

        Args:
            request: Property matching request with lead data and preferences

        Returns:
            PropertyMatchResponse with ranked matches and explanations
        """
        start_time = time.time()
        tenant_id = request.tenant_id
        cache_key = f"jorge:tenant:{tenant_id}:matches:{request.lead_id}:{hash(str(request.dict()))}"

        try:
            # Check cache first
            cached_response = await self._get_cached_matches(cache_key)
            if cached_response:
                logger.info(f"Cache hit for lead {request.lead_id} (Tenant: {tenant_id})")
                return cached_response

            # Step 1: Get lead context from Enhanced Scorer
            lead_context = await self._get_lead_context(request.lead_id, request.lead_data)

            # Step 2: Extract/update property preferences
            preferences = await self._extract_property_preferences(
                request.lead_id, tenant_id, request.lead_data, lead_context, request.preferences
            )

            # Step 3: Get filtered property inventory
            properties = await self._get_filtered_inventory(tenant_id, preferences)

            if not properties:
                logger.warning(f"No properties found for lead {request.lead_id}")
                return self._create_empty_response(request, start_time)

            # Step 4: Generate hybrid matches (neural + rules)
            matches = await self._generate_hybrid_matches(
                request.lead_id, request.lead_data, lead_context,
                preferences, properties, request.algorithm
            )

            # Step 5: Rank and limit results
            top_matches = await self._rank_and_limit_matches(matches, request.max_results)

            # Step 6: Generate AI explanations for top matches
            enhanced_matches = await self._enhance_matches_with_explanations(
                top_matches, lead_context, preferences
            )

            # Step 7: Create response
            response = await self._create_match_response(
                enhanced_matches, len(properties), request.algorithm, start_time
            )

            # Cache result
            await self._cache_matches(cache_key, response)

            # Update performance metrics
            self._update_performance_metrics(start_time, False)

            logger.info(f"Generated {len(enhanced_matches)} matches for lead {request.lead_id} in {response.processing_time_ms}ms")
            return response

        except Exception as e:
            logger.error(f"Error in find_matches_for_lead for {request.lead_id}: {e}")
            # Return fallback response
            return await self._create_fallback_response(request, start_time, str(e))

    async def _get_lead_context(self, lead_id: str, lead_data: Dict[str, Any]) -> LeadScoreBreakdown:
        """Get lead context from Enhanced Scorer."""
        try:
            return await self.enhanced_scorer.calculate_comprehensive_score(lead_data)
        except Exception as e:
            logger.warning(f"Enhanced scorer failed for lead {lead_id}: {e}")
            # Return minimal context
            return LeadScoreBreakdown(
                intent_score=50.0, financial_readiness=50.0, timeline_urgency=50.0,
                engagement_quality=50.0, referral_potential=50.0, local_connection=50.0,
                overall_score=50.0, priority_level=LeadPriority.MEDIUM,
                buying_stage=BuyingStage.GETTING_SERIOUS,
                recommended_actions=["Schedule consultation"],
                jorge_talking_points=["Discuss property preferences"],
                risk_factors=["Limited lead data available"]
            )

    async def _extract_property_preferences(self,
                                          lead_id: str,
                                          tenant_id: str,
                                          lead_data: Dict[str, Any],
                                          lead_context: LeadScoreBreakdown,
                                          explicit_preferences: Optional[LeadPropertyPreferences] = None) -> LeadPropertyPreferences:
        """Extract property preferences from lead data and context."""
        cache_key = f"jorge:tenant:{tenant_id}:preferences:{lead_id}"

        # Check cache first
        cached = await cache_service.get(cache_key)
        if cached:
            return LeadPropertyPreferences.parse_raw(cached)

        # Use explicit preferences if provided
        if explicit_preferences:
            prefs = explicit_preferences
        else:
            # Extract from lead data using AI
            prefs = await self._ai_extract_preferences(lead_data, lead_context)

        # Cache preferences
        await cache_service.set(cache_key, prefs.json(), ttl=CACHE_TTL_PREFERENCES)

        return prefs

    async def _ai_extract_preferences(self,
                                    lead_data: Dict[str, Any],
                                    lead_context: LeadScoreBreakdown) -> LeadPropertyPreferences:
        """Use AI to extract preferences from conversation history and lead data."""
        try:
            # Create prompt for preference extraction
            prompt = self._build_preference_extraction_prompt(lead_data, lead_context)

            # Use Claude to extract preferences
            response = await self.claude_assistant.generate_response(prompt)

            # Parse response into structured preferences
            return self._parse_ai_preferences(response, lead_context)

        except Exception as e:
            logger.warning(f"AI preference extraction failed: {e}")
            return self._create_fallback_preferences(lead_context)

    def _build_preference_extraction_prompt(self,
                                           lead_data: Dict[str, Any],
                                           lead_context: LeadScoreBreakdown) -> str:
        """Build prompt for AI preference extraction."""
        return f"""
        Extract property preferences for this Rancho Cucamonga home buyer:

        Lead Information:
        - Score: {lead_context.overall_score}/100
        - Priority: {lead_context.priority_level.value}
        - Buying Stage: {lead_context.buying_stage.value}
        - Financial Readiness: {lead_context.financial_readiness}/100
        - Timeline Urgency: {lead_context.timeline_urgency}/100

        Conversation History: {lead_data.get('conversation_history', 'No conversation data')}
        Search Behavior: {lead_data.get('search_behavior', {})}
        Budget Hints: {lead_data.get('budget_hints', 'Not specified')}

        Extract preferences in this JSON format:
        {{
            "budget_min": <number or null>,
            "budget_max": <number or null>,
            "preferred_bedrooms": <number or null>,
            "min_bedrooms": <number or null>,
            "preferred_bathrooms": <number or null>,
            "preferred_neighborhoods": [<list of neighborhoods>],
            "must_have_features": [<list of features>],
            "nice_to_have_features": [<list of features>],
            "timeline_urgency": <"immediate"|"30d"|"60d"|"90d"|"flexible">
        }}

        Focus on Rancho Cucamonga neighborhoods: Alta Loma, North Rancho Cucamonga,
        Victoria Arbors, Red Hill Country Club, Central Rancho, South Rancho.
        """

    def _parse_ai_preferences(self,
                             ai_response: str,
                             lead_context: LeadScoreBreakdown) -> LeadPropertyPreferences:
        """Parse AI response into LeadPropertyPreferences."""
        try:
            # Extract JSON from AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                prefs_data = json.loads(json_match.group())
                return LeadPropertyPreferences(**prefs_data)
        except Exception as e:
            logger.warning(f"Failed to parse AI preferences: {e}")

        return self._create_fallback_preferences(lead_context)

    def _create_fallback_preferences(self, lead_context: LeadScoreBreakdown) -> LeadPropertyPreferences:
        """Create fallback preferences based on lead context."""
        # Estimate budget from financial readiness
        if lead_context.financial_readiness >= 80:
            budget_max = 850000  # High-end Rancho Cucamonga
        elif lead_context.financial_readiness >= 60:
            budget_max = 650000  # Mid-range
        else:
            budget_max = 700000  # Entry-level

        # Set urgency from timeline score
        if lead_context.timeline_urgency >= 80:
            urgency = "immediate"
        elif lead_context.timeline_urgency >= 60:
            urgency = "30d"
        else:
            urgency = "flexible"

        return LeadPropertyPreferences(
            budget_max=budget_max,
            budget_min=budget_max * 0.8,  # 80% of max
            min_bedrooms=2,
            preferred_bedrooms=3,
            min_bathrooms=2.0,
            preferred_neighborhoods=["Alta Loma", "North Rancho Cucamonga"],
            timeline_urgency=urgency
        )

    async def _get_filtered_inventory(self, tenant_id: str, preferences: LeadPropertyPreferences) -> List[Property]:
        """Get filtered property inventory based on preferences and tenant context."""
        cache_key = f"jorge:tenant:{tenant_id}:inventory:{hash(str(preferences.dict()))}"

        # Check cache
        cached = await cache_service.get(cache_key)
        if cached:
            return [Property.parse_obj(p) for p in json.loads(cached)]

        # TODO: In production, this would query MLS API or tenant's internal database
        # For now, use mock data filtered by tenant context
        properties = await self._get_mock_inventory(tenant_id, preferences)

        # Cache filtered inventory
        await cache_service.set(
            cache_key,
            json.dumps([p.dict() for p in properties]),
            ttl=CACHE_TTL_INVENTORY
        )

        return properties

    async def _get_mock_inventory(self, tenant_id: str, preferences: LeadPropertyPreferences) -> List[Property]:
        """Get mock inventory for development/demo."""
        from ghl_real_estate_ai.models.jorge_property_models import (
            PropertyAddress, PropertyFeatures, PropertyType, SchoolInfo
        )

        # Mock properties in Rancho Cucamonga
        mock_properties = [
            Property(
                id="prop_001",
                tenant_id=tenant_id,
                address=PropertyAddress(
                    street="4512 Duval Street",
                    zip_code="91737",
                    neighborhood="Alta Loma"
                ),
                price=825000,
                features=PropertyFeatures(
                    bedrooms=4, bathrooms=3.0, sqft=2650, lot_size_sqft=8500,
                    garage_spaces=2, year_built=2018, has_pool=True,
                    updated_kitchen=True, granite_counters=True
                ),
                property_type=PropertyType.SINGLE_FAMILY,
                days_on_market=12,
                price_per_sqft=311.32,
                schools=[
                    SchoolInfo(name="Banyan Elementary", type="elementary",
                              rating=9, distance_miles=0.5, district="Cucamonga Elementary"),
                    SchoolInfo(name="Ayala High School", type="high",
                              rating=8, distance_miles=1.2, district="Chaffey Joint Union")
                ],
                commute_to_la=45,
                walkability_score=72,
                listing_date=datetime.now() - timedelta(days=12),
                images=["https://example.com/prop1_1.jpg"],
                virtual_tour_url="https://example.com/tour1"
            ),
            Property(
                id="prop_002",
                tenant_id=tenant_id,
                address=PropertyAddress(
                    street="8765 Victoria Avenue",
                    zip_code="91739",
                    neighborhood="Victoria Arbors"
                ),
                price=695000,
                features=PropertyFeatures(
                    bedrooms=3, bathrooms=2.5, sqft=2200, lot_size_sqft=7000,
                    garage_spaces=2, year_built=2015, has_spa=True,
                    fireplace=True, hardwood_floors=True
                ),
                property_type=PropertyType.SINGLE_FAMILY,
                days_on_market=25,
                price_per_sqft=315.91,
                schools=[
                    SchoolInfo(name="Victoria Elementary", type="elementary",
                              rating=8, distance_miles=0.3, district="Central Elementary"),
                    SchoolInfo(name="Los Osos High School", type="high",
                              rating=7, distance_miles=0.8, district="Chaffey Joint Union")
                ],
                commute_to_la=50,
                walkability_score=65,
                listing_date=datetime.now() - timedelta(days=25),
                images=["https://example.com/prop2_1.jpg"]
            ),
            Property(
                id="prop_003",
                tenant_id=tenant_id,
                address=PropertyAddress(
                    street="1234 Terra Vista Drive",
                    zip_code="91737",
                    neighborhood="Terra Vista"
                ),
                price=575000,
                features=PropertyFeatures(
                    bedrooms=3, bathrooms=2.0, sqft=1850, lot_size_sqft=6000,
                    garage_spaces=2, year_built=2010, has_pool=False,
                    updated_bathrooms=True, stainless_appliances=True
                ),
                property_type=PropertyType.TOWNHOME,
                days_on_market=8,
                price_per_sqft=310.81,
                schools=[
                    SchoolInfo(name="Terra Vista Elementary", type="elementary",
                              rating=7, distance_miles=0.4, district="Central Elementary")
                ],
                commute_to_la=55,
                walkability_score=70,
                listing_date=datetime.now() - timedelta(days=8),
                images=["https://example.com/prop3_1.jpg"]
            )
        ]

        # Apply preference filters
        filtered_properties = []
        for prop in mock_properties:
            if self._property_matches_filters(prop, preferences):
                filtered_properties.append(prop)

        return filtered_properties

    def _property_matches_filters(self, property: Property, preferences: LeadPropertyPreferences) -> bool:
        """Check if property matches preference filters."""
        # Budget filter
        if preferences.budget_min and property.price < preferences.budget_min:
            return False
        if preferences.budget_max and property.price > preferences.budget_max:
            return False

        # Bedroom filter
        if preferences.min_bedrooms and property.features.bedrooms < preferences.min_bedrooms:
            return False

        # Bathroom filter
        if preferences.min_bathrooms and property.features.bathrooms < preferences.min_bathrooms:
            return False

        # Neighborhood filter
        if (preferences.preferred_neighborhoods and
            property.address.neighborhood not in preferences.preferred_neighborhoods):
            # Allow some flexibility - don't filter out completely
            pass

        # Size filter
        if preferences.min_sqft and property.features.sqft < preferences.min_sqft:
            return False
        if preferences.max_sqft and property.features.sqft > preferences.max_sqft:
            return False

        return True

    async def _generate_hybrid_matches(self,
                                      lead_id: str,
                                      lead_data: Dict[str, Any],
                                      lead_context: LeadScoreBreakdown,
                                      preferences: LeadPropertyPreferences,
                                      properties: List[Property],
                                      algorithm: MatchingAlgorithm) -> List[PropertyMatch]:
        """Generate matches using hybrid neural + rules approach."""
        matches = []

        for i, property in enumerate(properties):
            try:
                # Calculate neural score (if available)
                neural_score = await self._calculate_neural_score(
                    property, lead_data, lead_context, preferences
                )

                # Calculate rule-based score
                rule_score = self._calculate_rule_score(
                    property, lead_context, preferences
                )

                # Combine scores based on algorithm
                final_score = self._combine_scores(neural_score, rule_score, algorithm)

                # Determine confidence
                confidence = self._determine_confidence(final_score, neural_score, rule_score)

                # Create match object
                match = PropertyMatch(
                    property=property,
                    lead_id=lead_id,
                    match_score=final_score,
                    neural_score=neural_score,
                    rule_score=rule_score,
                    confidence=confidence,
                    recommendation_rank=i + 1,  # Temporary ranking
                    reasoning=MatchReasoning(
                        primary_reasons=["Preliminary match"],
                        financial_fit="TBD",
                        lifestyle_fit="TBD",
                        market_timing="TBD",
                        jorge_talking_points=[]
                    ),
                    algorithm_used=algorithm,
                    processing_time_ms=0  # Will be updated
                )

                matches.append(match)

            except Exception as e:
                logger.warning(f"Failed to score property {property.id}: {e}")
                continue

        return matches

    async def _calculate_neural_score(self,
                                     property: Property,
                                     lead_data: Dict[str, Any],
                                     lead_context: LeadScoreBreakdown,
                                     preferences: LeadPropertyPreferences) -> float:
        """Calculate neural network-based matching score."""
        try:
            # TODO: Integrate with actual neural matcher when available
            if self.neural_matcher:
                # Use neural matcher for sophisticated scoring
                score = await self.neural_matcher.predict_match_score(property.dict(), lead_data)
                return min(100.0, max(0.0, score * 100))  # Normalize to 0-100
            else:
                # Fallback: sophisticated rule-based neural simulation
                return self._simulate_neural_score(property, lead_context, preferences)

        except Exception as e:
            logger.warning(f"Neural scoring failed: {e}")
            return self._simulate_neural_score(property, lead_context, preferences)

    def _simulate_neural_score(self,
                              property: Property,
                              lead_context: LeadScoreBreakdown,
                              preferences: LeadPropertyPreferences) -> float:
        """Simulate neural network scoring using sophisticated rules."""
        score = 0.0

        # Price alignment (30% weight)
        if preferences.budget_max:
            price_ratio = property.price / preferences.budget_max
            if price_ratio <= 0.9:  # Under budget
                score += 30.0 * (1.0 - price_ratio) * 0.5
            elif price_ratio <= 1.1:  # Within 10% of budget
                score += 25.0
            else:  # Over budget
                score += max(0, 15.0 - (price_ratio - 1.1) * 20)
        else:
            score += 15.0  # Default if no budget info

        # Location desirability (25% weight)
        neighborhood_score = self._score_neighborhood(property.address.neighborhood)
        score += 25.0 * neighborhood_score

        # School quality (20% weight) - Important for families
        if property.schools:
            avg_school_rating = sum(s.rating for s in property.schools) / len(property.schools)
            score += 20.0 * (avg_school_rating / 10.0)
        else:
            score += 10.0  # Default

        # Size and features alignment (15% weight)
        if preferences.preferred_bedrooms:
            bedroom_diff = abs(property.features.bedrooms - preferences.preferred_bedrooms)
            score += 15.0 * max(0, (3 - bedroom_diff) / 3)
        else:
            score += 10.0

        # Market timing advantage (10% weight)
        if property.days_on_market >= 30:  # Potential for negotiation
            score += 10.0
        elif property.days_on_market <= 7:  # Hot property
            score += 8.0
        else:
            score += 6.0

        return min(100.0, max(0.0, score))

    def _score_neighborhood(self, neighborhood: Optional[str]) -> float:
        """Score neighborhood desirability (0-1)."""
        if not neighborhood:
            return 0.5

        if neighborhood in self.market_data["premium_neighborhoods"]:
            return 1.0
        elif neighborhood in self.market_data["emerging_neighborhoods"]:
            return 0.8
        elif neighborhood in self.market_data["family_neighborhoods"]:
            return 0.9
        else:
            return 0.6  # Default for other neighborhoods

    def _calculate_rule_score(self,
                             property: Property,
                             lead_context: LeadScoreBreakdown,
                             preferences: LeadPropertyPreferences) -> float:
        """Calculate rule-based matching score using Jorge's expertise."""
        score = 0.0

        # Financial alignment (35% weight)
        score += 35.0 * self._score_financial_fit(property, lead_context, preferences)

        # Lifestyle fit (25% weight)
        score += 25.0 * self._score_lifestyle_fit(property, lead_context, preferences)

        # Market opportunity (20% weight)
        score += 20.0 * self._score_market_opportunity(property, lead_context)

        # Timeline alignment (10% weight)
        score += 10.0 * self._score_timeline_fit(property, lead_context, preferences)

        # Jorge's special insights (10% weight)
        score += 10.0 * self._score_jorge_insights(property, lead_context)

        return min(100.0, max(0.0, score))

    def _score_financial_fit(self,
                            property: Property,
                            lead_context: LeadScoreBreakdown,
                            preferences: LeadPropertyPreferences) -> float:
        """Score financial fit (0-1)."""
        score = 0.0

        # Budget alignment
        if preferences.budget_max:
            budget_utilization = property.price / preferences.budget_max
            if 0.8 <= budget_utilization <= 0.95:  # Sweet spot
                score += 0.6
            elif budget_utilization <= 1.0:  # Within budget
                score += 0.4
            elif budget_utilization <= 1.1:  # Slightly over
                score += 0.2
        else:
            score += 0.3  # Default if no budget

        # Financial readiness alignment
        readiness_factor = lead_context.financial_readiness / 100.0
        if property.price >= 700000 and readiness_factor < 0.7:
            score *= 0.7  # Penalize if financial readiness is low for expensive properties

        return min(1.0, score)

    def _score_lifestyle_fit(self,
                            property: Property,
                            lead_context: LeadScoreBreakdown,
                            preferences: LeadPropertyPreferences) -> float:
        """Score lifestyle alignment (0-1)."""
        score = 0.0

        # Bedroom/bathroom alignment
        if preferences.preferred_bedrooms:
            bedroom_match = 1.0 - (abs(property.features.bedrooms - preferences.preferred_bedrooms) / 3.0)
            score += 0.3 * max(0, bedroom_match)

        # Feature preferences
        if preferences.must_have_features:
            # TODO: Check property features against must-haves
            score += 0.2

        # Neighborhood preference
        if (preferences.preferred_neighborhoods and
            property.address.neighborhood in preferences.preferred_neighborhoods):
            score += 0.3
        elif property.address.neighborhood in self.market_data["premium_neighborhoods"]:
            score += 0.2  # Still good even if not explicitly preferred

        # Property type fit
        if preferences.property_type_preference:
            if property.property_type == preferences.property_type_preference:
                score += 0.2
            else:
                score += 0.1  # Partial credit

        return min(1.0, score)

    def _score_market_opportunity(self,
                                 property: Property,
                                 lead_context: LeadScoreBreakdown) -> float:
        """Score market opportunity and timing (0-1)."""
        score = 0.0

        # Days on market opportunity
        dom_factor = self.market_data["negotiation_factors"]["days_on_market_advantage"]
        if property.days_on_market >= 90:
            score += 0.4  # Motivated seller
        elif property.days_on_market >= 60:
            score += 0.3  # Good opportunity
        elif property.days_on_market >= 30:
            score += 0.2  # Some opportunity
        elif property.days_on_market <= 7:
            score += 0.1  # Hot property, less negotiation

        # Price per sqft value
        if property.price_per_sqft < 300:  # Good value in Rancho Cucamonga
            score += 0.3
        elif property.price_per_sqft < 350:
            score += 0.2
        else:
            score += 0.1

        # School premium justification
        if property.schools:
            avg_rating = sum(s.rating for s in property.schools) / len(property.schools)
            if avg_rating >= 8.5:
                score += 0.3  # Premium justified by excellent schools
            elif avg_rating >= 7.5:
                score += 0.2

        return min(1.0, score)

    def _score_timeline_fit(self,
                           property: Property,
                           lead_context: LeadScoreBreakdown,
                           preferences: LeadPropertyPreferences) -> float:
        """Score timeline alignment (0-1)."""
        urgency_score = lead_context.timeline_urgency / 100.0

        if preferences.timeline_urgency == "immediate":
            if property.status == "active" and property.days_on_market < 30:
                return 1.0  # Perfect for quick move
            else:
                return 0.6
        elif preferences.timeline_urgency in ["30d", "60d"]:
            return 0.8  # Most properties work for moderate timeline
        else:
            return 0.9  # Flexible timeline allows for any property

    def _score_jorge_insights(self,
                             property: Property,
                             lead_context: LeadScoreBreakdown) -> float:
        """Apply Jorge's special market insights (0-1)."""
        score = 0.0

        # Referral potential bonus
        if lead_context.referral_potential >= 75:
            # High referral leads get premium neighborhoods
            if property.address.neighborhood in self.market_data["premium_neighborhoods"]:
                score += 0.4

        # Local connection bonus
        if lead_context.local_connection >= 80:
            # Local connections know the market - show them great value
            if property.days_on_market >= 30 and property.price_per_sqft < 320:
                score += 0.3

        # Engagement quality consideration
        if lead_context.engagement_quality >= 80:
            # Highly engaged leads can appreciate premium features
            if (property.features.has_pool or property.features.updated_kitchen or
                property.features.granite_counters):
                score += 0.3

        return min(1.0, score)

    def _combine_scores(self, neural_score: float, rule_score: float, algorithm: MatchingAlgorithm) -> float:
        """Combine neural and rule scores based on algorithm."""
        if algorithm == MatchingAlgorithm.NEURAL_ONLY:
            return neural_score
        elif algorithm == MatchingAlgorithm.RULES_ONLY:
            return rule_score
        elif algorithm == MatchingAlgorithm.JORGE_OPTIMIZED:
            # Jorge's optimized blend: 60% neural, 40% rules
            return (NEURAL_WEIGHT * neural_score) + (RULES_WEIGHT * rule_score)
        else:  # HYBRID default
            return 0.5 * neural_score + 0.5 * rule_score

    def _determine_confidence(self, final_score: float, neural_score: float, rule_score: float) -> ConfidenceLevel:
        """Determine confidence level based on scores."""
        score_agreement = 1.0 - abs(neural_score - rule_score) / 100.0

        if final_score >= 90 and score_agreement >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif final_score >= 75 and score_agreement >= 0.7:
            return ConfidenceLevel.HIGH
        elif final_score >= 50 and score_agreement >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif final_score >= 25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    async def _rank_and_limit_matches(self, matches: List[PropertyMatch], max_results: int) -> List[PropertyMatch]:
        """Rank matches by score and limit results."""
        # Sort by match score (descending)
        ranked_matches = sorted(matches, key=lambda m: m.match_score, reverse=True)

        # Update ranking
        for i, match in enumerate(ranked_matches[:max_results]):
            match.recommendation_rank = i + 1

        return ranked_matches[:max_results]

    async def _enhance_matches_with_explanations(self,
                                               matches: List[PropertyMatch],
                                               lead_context: LeadScoreBreakdown,
                                               preferences: LeadPropertyPreferences) -> List[PropertyMatch]:
        """Generate AI-powered explanations for matches."""
        enhanced_matches = []

        for match in matches:
            try:
                reasoning = await self._generate_match_reasoning(match, lead_context, preferences)
                match.reasoning = reasoning
                enhanced_matches.append(match)
            except Exception as e:
                logger.warning(f"Failed to generate reasoning for property {match.property.id}: {e}")
                # Use fallback reasoning
                match.reasoning = self._create_fallback_reasoning(match, lead_context)
                enhanced_matches.append(match)

        return enhanced_matches

    async def _generate_match_reasoning(self,
                                      match: PropertyMatch,
                                      lead_context: LeadScoreBreakdown,
                                      preferences: LeadPropertyPreferences) -> MatchReasoning:
        """Generate AI-powered match reasoning."""
        try:
            prompt = self._build_reasoning_prompt(match, lead_context, preferences)
            response = await self.claude_assistant.generate_response(prompt)
            return self._parse_reasoning_response(response, match)
        except Exception as e:
            logger.warning(f"AI reasoning generation failed: {e}")
            return self._create_fallback_reasoning(match, lead_context)

    def _build_reasoning_prompt(self,
                               match: PropertyMatch,
                               lead_context: LeadScoreBreakdown,
                               preferences: LeadPropertyPreferences) -> str:
        """Build prompt for AI reasoning generation."""
        prop = match.property
        return f"""
        Generate a compelling explanation for why this property matches this Rancho Cucamonga home buyer:

        PROPERTY:
        - {prop.address.street}, {prop.address.neighborhood}
        - ${prop.price:,} | {prop.features.bedrooms}br/{prop.features.bathrooms}ba | {prop.features.sqft:,} sqft
        - Days on market: {prop.days_on_market}
        - Schools: {[s.name + f' (Rating: {s.rating})' for s in prop.schools[:2]]}
        - Features: Pool: {prop.features.has_pool}, Updated Kitchen: {prop.features.updated_kitchen}

        BUYER PROFILE:
        - Lead Score: {lead_context.overall_score}/100 ({lead_context.priority_level.value})
        - Buying Stage: {lead_context.buying_stage.value}
        - Financial Readiness: {lead_context.financial_readiness}/100
        - Timeline: {lead_context.timeline_urgency}/100 urgency
        - Budget: ${preferences.budget_min or 'flexible'} - ${preferences.budget_max or 'open'}
        - Preferred Areas: {preferences.preferred_neighborhoods or 'flexible'}

        MATCH SCORES:
        - Overall: {match.match_score:.1f}/100
        - Neural AI: {match.neural_score:.1f}/100
        - Jorge's Rules: {match.rule_score:.1f}/100

        Provide response in this JSON format:
        {{
            "primary_reasons": ["Reason 1", "Reason 2", "Reason 3"],
            "financial_fit": "Why the price works for this buyer",
            "lifestyle_fit": "How property matches their lifestyle needs",
            "market_timing": "Why now is good timing for this property",
            "potential_concerns": ["Any concerns to address"],
            "jorge_talking_points": ["What Jorge should emphasize in conversation"],
            "client_script_suggestions": ["Specific things to say to client"]
        }}

        Focus on Jorge's expertise in Rancho Cucamonga market and specific buyer psychology.
        """

    def _parse_reasoning_response(self, response: str, match: PropertyMatch) -> MatchReasoning:
        """Parse AI reasoning response."""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                reasoning_data = json.loads(json_match.group())
                return MatchReasoning(**reasoning_data)
        except Exception as e:
            logger.warning(f"Failed to parse reasoning response: {e}")

        return self._create_fallback_reasoning(match, None)

    def _create_fallback_reasoning(self, match: PropertyMatch, lead_context: Optional[LeadScoreBreakdown]) -> MatchReasoning:
        """Create fallback reasoning when AI generation fails."""
        prop = match.property

        primary_reasons = []

        # Price reasoning
        if match.match_score >= 80:
            primary_reasons.append(f"Excellent value at ${prop.price:,} in {prop.address.neighborhood}")
        elif match.match_score >= 60:
            primary_reasons.append(f"Good value at ${prop.price:,} for {prop.features.bedrooms}br/{prop.features.bathrooms}ba")

        # Location reasoning
        if prop.address.neighborhood in self.market_data["premium_neighborhoods"]:
            primary_reasons.append(f"Premium {prop.address.neighborhood} location with top schools")

        # Market timing
        if prop.days_on_market >= 30:
            primary_reasons.append(f"{prop.days_on_market} days on market creates negotiation opportunity")

        return MatchReasoning(
            primary_reasons=primary_reasons[:3],
            financial_fit=f"Property is priced competitively at ${prop.price_per_sqft:.0f}/sqft",
            lifestyle_fit=f"{prop.features.bedrooms}br/{prop.features.bathrooms}ba layout perfect for growing families",
            market_timing="Strong Rancho Cucamonga market with good appreciation potential",
            potential_concerns=["Schedule showing quickly in this competitive market"],
            jorge_talking_points=[
                f"I know this {prop.address.neighborhood} neighborhood very well",
                f"This property offers exceptional value at ${prop.price:,}"
            ],
            client_script_suggestions=[
                "Let me show you why this property is perfect for your family",
                "I have insider knowledge of this neighborhood's market trends"
            ]
        )

    async def _create_match_response(self,
                                   matches: List[PropertyMatch],
                                   total_considered: int,
                                   algorithm: MatchingAlgorithm,
                                   start_time: float) -> PropertyMatchResponse:
        """Create the final match response."""
        processing_time_ms = int((time.time() - start_time) * 1000)

        if not matches:
            avg_score = 0.0
            best_score = 0.0
            summary = "No suitable properties found matching criteria"
        else:
            avg_score = sum(m.match_score for m in matches) / len(matches)
            best_score = matches[0].match_score
            summary = f"Found {len(matches)} excellent matches with {avg_score:.1f}% average score"

        return PropertyMatchResponse(
            matches=matches,
            total_considered=total_considered,
            processing_time_ms=processing_time_ms,
            algorithm_used=algorithm,
            avg_match_score=avg_score,
            best_match_score=best_score,
            recommendation_summary=summary,
            model_version="jorge-hybrid-v1.0"
        )

    async def _get_cached_matches(self, cache_key: str) -> Optional[PropertyMatchResponse]:
        """Get cached matches."""
        try:
            cached = await cache_service.get(cache_key)
            if cached:
                return PropertyMatchResponse.parse_raw(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_matches(self, cache_key: str, response: PropertyMatchResponse) -> None:
        """Cache match response."""
        try:
            # Mark as cache hit for next time
            response_dict = response.dict()
            response_dict['cache_hit'] = True
            cached_response = PropertyMatchResponse(**response_dict)

            await cache_service.set(cache_key, cached_response.json(), ttl=CACHE_TTL_MATCHES)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _create_empty_response(self, request: PropertyMatchRequest, start_time: float) -> PropertyMatchResponse:
        """Create empty response when no properties found."""
        return PropertyMatchResponse(
            matches=[],
            total_considered=0,
            processing_time_ms=int((time.time() - start_time) * 1000),
            algorithm_used=request.algorithm,
            avg_match_score=0.0,
            best_match_score=0.0,
            recommendation_summary="No properties found matching criteria",
            model_version="jorge-hybrid-v1.0"
        )

    async def _create_fallback_response(self,
                                      request: PropertyMatchRequest,
                                      start_time: float,
                                      error: str) -> PropertyMatchResponse:
        """Create fallback response when matching fails."""
        logger.error(f"Property matching failed for lead {request.lead_id}: {error}")

        return PropertyMatchResponse(
            matches=[],
            total_considered=0,
            processing_time_ms=int((time.time() - start_time) * 1000),
            algorithm_used=request.algorithm,
            avg_match_score=0.0,
            best_match_score=0.0,
            recommendation_summary=f"Matching temporarily unavailable. Please try again.",
            model_version="jorge-hybrid-v1.0"
        )

    def _update_performance_metrics(self, start_time: float, cache_hit: bool) -> None:
        """Update service performance metrics."""
        processing_time = (time.time() - start_time) * 1000

        self.performance_metrics['total_matches_generated'] += 1

        # Update rolling average processing time
        current_avg = self.performance_metrics['avg_processing_time_ms']
        total_requests = self.performance_metrics['total_matches_generated']
        self.performance_metrics['avg_processing_time_ms'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )

        # Update cache hit rate
        if cache_hit:
            # Cache hit rate calculation would need more sophisticated tracking
            pass

    def get_performance_metrics(self) -> MatchingPerformanceMetrics:
        """Get current performance metrics."""
        return MatchingPerformanceMetrics(
            avg_processing_time_ms=self.performance_metrics['avg_processing_time_ms'],
            cache_hit_rate=self.performance_metrics['cache_hit_rate'],
            neural_inference_time_ms=self.performance_metrics['neural_inference_time_ms'],
            rules_processing_time_ms=self.performance_metrics['rules_processing_time_ms'],
            total_properties_evaluated=0,  # Would track this
            matches_generated=self.performance_metrics['total_matches_generated']
        )

    async def explain_specific_match(self, property_id: str, lead_id: str) -> Optional[MatchReasoning]:
        """Generate detailed explanation for a specific property-lead match."""
        # This would be called when user wants detailed explanation
        # Implementation would fetch property, lead data, and generate explanation
        pass

    async def update_lead_preferences(self,
                                    lead_id: str,
                                    preferences: LeadPropertyPreferences) -> None:
        """Update cached lead preferences."""
        cache_key = f"jorge:preferences:{lead_id}"
        await cache_service.set(cache_key, preferences.json(), ttl=CACHE_TTL_PREFERENCES)
        logger.info(f"Updated preferences for lead {lead_id}")

    async def get_market_inventory_stats(self) -> Dict[str, Any]:
        """Get current market inventory statistics."""
        # This would return stats about current inventory
        # For demo purposes, return mock stats
        return {
            "total_active_listings": 145,
            "avg_price": 675000,
            "median_price": 625000,
            "avg_days_on_market": 28,
            "inventory_by_neighborhood": {
                "Alta Loma": 35,
                "Victoria Arbors": 28,
                "North Rancho Cucamonga": 22,
                "Terra Vista": 18,
                "Central Rancho": 15
            }
        }