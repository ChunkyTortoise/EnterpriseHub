"""
Jorge's Real Estate AI Platform - Property Vision Analyzer
Advanced computer vision for instant property analysis from mobile photos

This module provides comprehensive property analysis from photos, including:
- Architectural feature detection
- Condition assessment
- Market value indicators
- Selling point identification
- Renovation recommendations
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import openai
from openai import AsyncOpenAI

from ..services.claude_assistant import ClaudeAssistant
from ..services.cache_service import CacheService
from ..ghl_utils.jorge_config import JorgeConfig

logger = logging.getLogger(__name__)

@dataclass
class PropertyFeatures:
    """Extracted property features from vision analysis"""
    architectural_style: str
    exterior_material: str
    roof_type: str
    windows: Dict[str, Any]
    doors: Dict[str, Any]
    landscaping: Dict[str, Any]
    condition_score: float  # 0-100
    curb_appeal_score: float  # 0-100
    estimated_age: int
    square_footage_estimate: Optional[int]
    story_count: int
    garage_type: Optional[str]
    pool_visible: bool
    lot_characteristics: Dict[str, Any]

@dataclass
class ConditionAssessment:
    """Property condition analysis"""
    overall_score: float  # 0-100
    exterior_condition: str
    roof_condition: str
    window_condition: str
    landscaping_condition: str
    maintenance_issues: List[str]
    upgrade_opportunities: List[str]
    estimated_repair_cost: float

@dataclass
class MarketIndicators:
    """Market positioning indicators from visual analysis"""
    price_range_estimate: Tuple[float, float]
    comparable_style_value: float
    neighborhood_fit_score: float  # 0-100
    investment_appeal: str
    rental_potential_score: float  # 0-100
    flip_potential_score: float  # 0-100

@dataclass
class SellingPoints:
    """Marketable features and selling points"""
    unique_features: List[str]
    buyer_appeal_features: List[str]
    luxury_indicators: List[str]
    family_friendly_features: List[str]
    maintenance_advantages: List[str]
    energy_efficiency_indicators: List[str]

@dataclass
class RenovationRecommendations:
    """AI-powered renovation suggestions"""
    high_impact_improvements: List[Dict[str, Any]]
    cost_effective_updates: List[Dict[str, Any]]
    luxury_additions: List[Dict[str, Any]]
    curb_appeal_enhancements: List[Dict[str, Any]]
    estimated_roi_by_improvement: Dict[str, float]

@dataclass
class PropertyAnalysis:
    """Complete property analysis result"""
    features: PropertyFeatures
    condition: ConditionAssessment
    market_indicators: MarketIndicators
    selling_points: SellingPoints
    renovation_recommendations: RenovationRecommendations
    confidence_score: float  # 0-100
    analysis_timestamp: datetime
    photo_metadata: Dict[str, Any]

class PropertyVisionAnalyzer:
    """
    Advanced property analysis using computer vision and AI
    Optimized for mobile real estate field work
    """

    def __init__(self):
        self.config = JorgeConfig()
        self.claude = ClaudeAssistant()
        self.cache = CacheService()

        # Initialize OpenAI client for vision analysis
        self.openai_client = AsyncOpenAI(
            api_key=self.config.get_openai_api_key()
        )

        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
        self.max_image_size = 20 * 1024 * 1024  # 20MB limit
        self.vision_model = "gpt-4o"  # GPT-4 Vision model

    async def analyze_property_photo(self,
                                   image_data: bytes,
                                   location: Optional[Dict[str, float]] = None,
                                   property_address: Optional[str] = None,
                                   additional_context: Optional[str] = None) -> PropertyAnalysis:
        """
        Comprehensive property analysis from a single photo

        Args:
            image_data: Raw image bytes
            location: Optional GPS coordinates {"lat": float, "lng": float}
            property_address: Optional property address for context
            additional_context: Optional additional context about the property

        Returns:
            PropertyAnalysis: Comprehensive analysis results
        """
        try:
            logger.info("Starting property photo analysis")
            start_time = datetime.now()

            # Preprocess image for optimal analysis
            processed_image = await self._preprocess_image(image_data)

            # Generate cache key for similar analysis
            cache_key = self._generate_cache_key(processed_image, location, property_address)

            # Check cache first
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached property analysis")
                return PropertyAnalysis(**cached_result)

            # Encode image for API
            base64_image = base64.b64encode(processed_image).decode('utf-8')

            # Perform parallel analysis tasks
            vision_analysis, market_context = await asyncio.gather(
                self._perform_vision_analysis(base64_image, location, property_address, additional_context),
                self._get_market_context(location, property_address) if location or property_address else asyncio.coroutine(lambda: {})()
            )

            # Process and structure the analysis
            analysis = await self._structure_analysis(vision_analysis, market_context, {
                'location': location,
                'address': property_address,
                'context': additional_context,
                'analysis_duration': (datetime.now() - start_time).total_seconds()
            })

            # Cache the result
            await self.cache.set(cache_key, analysis.__dict__, ttl=3600)  # 1 hour cache

            logger.info(f"Property analysis completed in {(datetime.now() - start_time).total_seconds():.2f}s")
            return analysis

        except Exception as e:
            logger.error(f"Property analysis failed: {str(e)}")
            raise ValueError(f"Failed to analyze property photo: {str(e)}")

    async def _preprocess_image(self, image_data: bytes) -> bytes:
        """
        Preprocess image for optimal vision analysis
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (max 2048x2048 for optimal processing)
            max_size = 2048
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Enhance image quality
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)  # Slight contrast boost

            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)  # Slight sharpness boost

            # Save as JPEG for consistent processing
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return image_data

    async def _perform_vision_analysis(self,
                                     base64_image: str,
                                     location: Optional[Dict[str, float]],
                                     address: Optional[str],
                                     context: Optional[str]) -> Dict[str, Any]:
        """
        Perform comprehensive vision analysis using GPT-4 Vision
        """
        try:
            # Construct analysis prompt for Jorge's real estate focus
            analysis_prompt = self._build_vision_prompt(location, address, context)

            response = await self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Low temperature for consistent analysis
            )

            # Parse the structured response
            analysis_text = response.choices[0].message.content
            return await self._parse_vision_response(analysis_text)

        except Exception as e:
            logger.error(f"Vision analysis failed: {str(e)}")
            # Return fallback analysis
            return self._create_fallback_analysis()

    def _build_vision_prompt(self,
                           location: Optional[Dict[str, float]],
                           address: Optional[str],
                           context: Optional[str]) -> str:
        """
        Build comprehensive analysis prompt for property vision
        """
        base_prompt = """
You are Jorge's AI property analyst, an expert in real estate valuation and market analysis.
Analyze this property photo with the precision and insight of a seasoned real estate professional
who helps agents maximize their 6% commission through strategic property insights.

Provide a comprehensive analysis in the following JSON structure:

{
  "architectural_analysis": {
    "style": "architectural style (e.g., Ranch, Colonial, Modern, etc.)",
    "exterior_material": "primary exterior material",
    "roof_type": "roof style and material",
    "story_count": "number of stories",
    "estimated_age": "estimated age in years",
    "square_footage_estimate": "estimated square footage range"
  },
  "condition_assessment": {
    "overall_condition_score": "0-100 rating",
    "exterior_condition": "excellent/good/fair/poor with details",
    "roof_condition": "assessment with specific issues if any",
    "window_condition": "condition and style notes",
    "landscaping_condition": "landscaping quality and maintenance",
    "visible_maintenance_issues": ["list of issues requiring attention"],
    "estimated_repair_cost": "cost estimate for visible issues"
  },
  "market_indicators": {
    "price_range_estimate": {"low": 0, "high": 0},
    "neighborhood_fit": "how well it fits the neighborhood style",
    "buyer_appeal_level": "high/medium/low with reasoning",
    "investment_potential": "analysis for investors",
    "rental_appeal": "rental market attractiveness"
  },
  "selling_points": {
    "unique_features": ["distinctive features that add value"],
    "curb_appeal_factors": ["elements that create strong first impression"],
    "family_appeal": ["features attractive to families"],
    "luxury_indicators": ["upscale features visible"],
    "energy_efficiency_signs": ["visible efficiency features"]
  },
  "improvement_recommendations": {
    "high_impact_low_cost": [{"improvement": "description", "estimated_cost": 0, "value_add": 0}],
    "curb_appeal_boosts": [{"improvement": "description", "estimated_cost": 0, "impact": "high/medium/low"}],
    "major_value_adds": [{"improvement": "description", "estimated_cost": 0, "roi_estimate": "percentage"}]
  },
  "jorge_insights": {
    "listing_strategy": "recommended listing approach",
    "negotiation_leverage": "points for buyer/seller negotiations",
    "market_timing": "best time to list based on condition/features",
    "commission_optimization": "how to maximize the 6% commission value"
  },
  "confidence_score": "0-100 rating of analysis confidence"
}

Focus on actionable insights that help Jorge:
1. Price properties competitively
2. Identify value-add opportunities
3. Market properties effectively
4. Negotiate from a position of knowledge
5. Maximize commission potential through strategic advice

Be specific about dollar amounts, timeframes, and ROI where possible.
"""

        # Add context-specific information
        if location:
            base_prompt += f"\n\nProperty Location Context: Latitude {location['lat']}, Longitude {location['lng']}"

        if address:
            base_prompt += f"\n\nProperty Address: {address}"

        if context:
            base_prompt += f"\n\nAdditional Context: {context}"

        base_prompt += "\n\nProvide your analysis as valid JSON only, no additional text."

        return base_prompt

    async def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate the vision analysis response
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No valid JSON found in response")

            json_text = response_text[json_start:json_end]
            analysis = json.loads(json_text)

            # Validate required fields
            required_sections = [
                'architectural_analysis',
                'condition_assessment',
                'market_indicators',
                'selling_points',
                'improvement_recommendations',
                'jorge_insights',
                'confidence_score'
            ]

            for section in required_sections:
                if section not in analysis:
                    logger.warning(f"Missing required section: {section}")
                    analysis[section] = {}

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return self._create_fallback_analysis()
        except Exception as e:
            logger.error(f"Response parsing failed: {str(e)}")
            return self._create_fallback_analysis()

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """
        Create fallback analysis when vision analysis fails
        """
        return {
            'architectural_analysis': {
                'style': 'Unable to determine',
                'exterior_material': 'Unknown',
                'roof_type': 'Unknown',
                'story_count': 1,
                'estimated_age': 0,
                'square_footage_estimate': 0
            },
            'condition_assessment': {
                'overall_condition_score': 50,
                'exterior_condition': 'Unable to assess from image',
                'roof_condition': 'Unable to assess',
                'window_condition': 'Unable to assess',
                'landscaping_condition': 'Unable to assess',
                'visible_maintenance_issues': [],
                'estimated_repair_cost': 0
            },
            'market_indicators': {
                'price_range_estimate': {'low': 0, 'high': 0},
                'neighborhood_fit': 'Unknown',
                'buyer_appeal_level': 'medium',
                'investment_potential': 'Unable to assess',
                'rental_appeal': 'Unknown'
            },
            'selling_points': {
                'unique_features': [],
                'curb_appeal_factors': [],
                'family_appeal': [],
                'luxury_indicators': [],
                'energy_efficiency_signs': []
            },
            'improvement_recommendations': {
                'high_impact_low_cost': [],
                'curb_appeal_boosts': [],
                'major_value_adds': []
            },
            'jorge_insights': {
                'listing_strategy': 'Professional photo analysis recommended',
                'negotiation_leverage': 'In-person inspection needed',
                'market_timing': 'Unable to determine from image',
                'commission_optimization': 'Schedule professional property evaluation'
            },
            'confidence_score': 10
        }

    async def _get_market_context(self,
                                location: Optional[Dict[str, float]],
                                address: Optional[str]) -> Dict[str, Any]:
        """
        Get market context for the property location
        """
        try:
            if not (location or address):
                return {}

            # This would integrate with real market data APIs
            # For now, return placeholder structure
            return {
                'neighborhood_data': {
                    'median_home_value': 0,
                    'price_per_sqft': 0,
                    'days_on_market': 0,
                    'market_trend': 'stable'
                },
                'comparable_sales': [],
                'market_activity': {
                    'active_listings': 0,
                    'pending_sales': 0,
                    'recent_sales_count': 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to get market context: {str(e)}")
            return {}

    async def _structure_analysis(self,
                                vision_data: Dict[str, Any],
                                market_data: Dict[str, Any],
                                metadata: Dict[str, Any]) -> PropertyAnalysis:
        """
        Structure the analysis into the PropertyAnalysis dataclass
        """
        try:
            arch_data = vision_data.get('architectural_analysis', {})
            cond_data = vision_data.get('condition_assessment', {})
            market_data_vision = vision_data.get('market_indicators', {})
            selling_data = vision_data.get('selling_points', {})
            improvements = vision_data.get('improvement_recommendations', {})

            # Extract features
            features = PropertyFeatures(
                architectural_style=arch_data.get('style', 'Unknown'),
                exterior_material=arch_data.get('exterior_material', 'Unknown'),
                roof_type=arch_data.get('roof_type', 'Unknown'),
                windows={'condition': cond_data.get('window_condition', 'Unknown')},
                doors={'visible': True},
                landscaping={'condition': cond_data.get('landscaping_condition', 'Unknown')},
                condition_score=float(cond_data.get('overall_condition_score', 50)),
                curb_appeal_score=75.0,  # Default, could be enhanced with specific analysis
                estimated_age=int(arch_data.get('estimated_age', 0)),
                square_footage_estimate=int(arch_data.get('square_footage_estimate', 0)),
                story_count=int(arch_data.get('story_count', 1)),
                garage_type=None,
                pool_visible=False,
                lot_characteristics={}
            )

            # Extract condition assessment
            condition = ConditionAssessment(
                overall_score=float(cond_data.get('overall_condition_score', 50)),
                exterior_condition=cond_data.get('exterior_condition', 'Unknown'),
                roof_condition=cond_data.get('roof_condition', 'Unknown'),
                window_condition=cond_data.get('window_condition', 'Unknown'),
                landscaping_condition=cond_data.get('landscaping_condition', 'Unknown'),
                maintenance_issues=cond_data.get('visible_maintenance_issues', []),
                upgrade_opportunities=[],
                estimated_repair_cost=float(cond_data.get('estimated_repair_cost', 0))
            )

            # Extract market indicators
            price_range = market_data_vision.get('price_range_estimate', {'low': 0, 'high': 0})
            market_indicators = MarketIndicators(
                price_range_estimate=(float(price_range['low']), float(price_range['high'])),
                comparable_style_value=0.0,
                neighborhood_fit_score=75.0,
                investment_appeal=market_data_vision.get('investment_potential', 'Unknown'),
                rental_potential_score=60.0,
                flip_potential_score=50.0
            )

            # Extract selling points
            selling_points = SellingPoints(
                unique_features=selling_data.get('unique_features', []),
                buyer_appeal_features=selling_data.get('curb_appeal_factors', []),
                luxury_indicators=selling_data.get('luxury_indicators', []),
                family_friendly_features=selling_data.get('family_appeal', []),
                maintenance_advantages=[],
                energy_efficiency_indicators=selling_data.get('energy_efficiency_signs', [])
            )

            # Extract renovation recommendations
            renovation_recommendations = RenovationRecommendations(
                high_impact_improvements=improvements.get('high_impact_low_cost', []),
                cost_effective_updates=improvements.get('curb_appeal_boosts', []),
                luxury_additions=improvements.get('major_value_adds', []),
                curb_appeal_enhancements=improvements.get('curb_appeal_boosts', []),
                estimated_roi_by_improvement={}
            )

            return PropertyAnalysis(
                features=features,
                condition=condition,
                market_indicators=market_indicators,
                selling_points=selling_points,
                renovation_recommendations=renovation_recommendations,
                confidence_score=float(vision_data.get('confidence_score', 50)),
                analysis_timestamp=datetime.now(),
                photo_metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to structure analysis: {str(e)}")
            # Return minimal analysis
            return self._create_minimal_analysis()

    def _create_minimal_analysis(self) -> PropertyAnalysis:
        """Create minimal analysis structure for fallback"""
        return PropertyAnalysis(
            features=PropertyFeatures(
                architectural_style='Unknown',
                exterior_material='Unknown',
                roof_type='Unknown',
                windows={},
                doors={},
                landscaping={},
                condition_score=50.0,
                curb_appeal_score=50.0,
                estimated_age=0,
                square_footage_estimate=None,
                story_count=1,
                garage_type=None,
                pool_visible=False,
                lot_characteristics={}
            ),
            condition=ConditionAssessment(
                overall_score=50.0,
                exterior_condition='Unknown',
                roof_condition='Unknown',
                window_condition='Unknown',
                landscaping_condition='Unknown',
                maintenance_issues=[],
                upgrade_opportunities=[],
                estimated_repair_cost=0.0
            ),
            market_indicators=MarketIndicators(
                price_range_estimate=(0.0, 0.0),
                comparable_style_value=0.0,
                neighborhood_fit_score=50.0,
                investment_appeal='Unknown',
                rental_potential_score=50.0,
                flip_potential_score=50.0
            ),
            selling_points=SellingPoints(
                unique_features=[],
                buyer_appeal_features=[],
                luxury_indicators=[],
                family_friendly_features=[],
                maintenance_advantages=[],
                energy_efficiency_indicators=[]
            ),
            renovation_recommendations=RenovationRecommendations(
                high_impact_improvements=[],
                cost_effective_updates=[],
                luxury_additions=[],
                curb_appeal_enhancements=[],
                estimated_roi_by_improvement={}
            ),
            confidence_score=10.0,
            analysis_timestamp=datetime.now(),
            photo_metadata={}
        )

    def _generate_cache_key(self,
                          image_data: bytes,
                          location: Optional[Dict[str, float]],
                          address: Optional[str]) -> str:
        """Generate cache key for analysis results"""
        import hashlib

        # Create hash of image data
        image_hash = hashlib.md5(image_data).hexdigest()[:16]

        # Add location/address to key if available
        location_key = ""
        if location:
            location_key = f"_{location['lat']:.4f}_{location['lng']:.4f}"
        elif address:
            location_key = f"_{hashlib.md5(address.encode()).hexdigest()[:8]}"

        return f"property_analysis_{image_hash}{location_key}"

# Import statement fix
import io