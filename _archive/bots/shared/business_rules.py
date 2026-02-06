#!/usr/bin/env python3
"""
Jorge Business Rules Integration Module

This module provides compatibility and integration patterns for Jorge's 
business rules with the feature engineering pipeline. It bridges existing
Jorge components with the new ML feature extraction system.

Author: Claude Code Assistant
Created: January 23, 2026
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LeadPriority(Enum):
    """Jorge's lead priority classification"""
    URGENT = "urgent"
    HIGH = "high" 
    NORMAL = "normal"
    LOW = "low"
    NURTURE = "nurture"
    DISQUALIFIED = "disqualified"


class ServiceArea(Enum):
    """Jorge's service areas"""
    DALLAS = "dallas"
    PLANO = "plano"
    FRISCO = "frisco"
    MCKINNEY = "mckinney"
    ALLEN = "allen"
    OUT_OF_AREA = "out_of_area"


@dataclass
class JorgeBusinessCriteria:
    """Jorge's core business criteria for lead qualification"""
    
    # Budget criteria
    MIN_BUDGET = 200000  # $200K minimum
    IDEAL_BUDGET_MIN = 400000  # $400K ideal minimum
    IDEAL_BUDGET_MAX = 800000  # $800K ideal maximum
    MAX_BUDGET = 1200000  # $1.2M maximum (above this needs special handling)
    
    # Timeline preferences
    IMMEDIATE_TIMELINE = ["immediate", "1_month"]
    PREFERRED_TIMELINE = ["2_months", "3_months"]
    ACCEPTABLE_TIMELINE = ["6_months"]
    
    # Service areas (in priority order)
    PRIMARY_AREAS = [ServiceArea.PLANO, ServiceArea.FRISCO]
    SECONDARY_AREAS = [ServiceArea.DALLAS, ServiceArea.MCKINNEY, ServiceArea.ALLEN]
    
    # Commission structure
    STANDARD_COMMISSION_RATE = 0.06  # 6%
    MINIMUM_COMMISSION_TARGET = 12000  # $12K minimum
    
    # Lead scoring thresholds
    HOT_LEAD_THRESHOLD = 85
    WARM_LEAD_THRESHOLD = 65
    COLD_LEAD_THRESHOLD = 40


@dataclass 
class JorgeLeadQualification:
    """Comprehensive lead qualification result"""
    
    # Core qualification
    meets_criteria: bool = False
    priority: LeadPriority = LeadPriority.NORMAL
    qualification_score: float = 0.0
    
    # Financial analysis
    budget_fit: str = "unknown"  # excellent, good, marginal, poor
    estimated_commission: float = 0.0
    commission_potential: str = "low"  # high, medium, low
    
    # Geographic fit
    service_area: ServiceArea = ServiceArea.OUT_OF_AREA
    location_priority: str = "low"  # high, medium, low
    
    # Timeline analysis
    timeline_fit: str = "poor"  # excellent, good, fair, poor
    urgency_level: str = "low"  # high, medium, low
    
    # Decision factors
    qualifying_factors: List[str] = field(default_factory=list)
    disqualifying_factors: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)
    
    # Jorge-specific insights
    jorge_notes: str = ""
    recommended_action: str = "assess"
    follow_up_timeline: str = "standard"


class JorgeBusinessRulesEngine:
    """
    Enhanced business rules engine that integrates with feature engineering
    and provides Jorge-specific lead qualification logic.
    """
    
    def __init__(self):
        self.criteria = JorgeBusinessCriteria()
        self.logger = logging.getLogger(__name__)
        
        # Jorge's location keyword mapping
        self.location_mapping = {
            ServiceArea.DALLAS: [
                "dallas", "downtown dallas", "uptown", "deep ellum", "bishop arts",
                "lakewood", "white rock", "oak cliff", "preston center"
            ],
            ServiceArea.PLANO: [
                "plano", "west plano", "east plano", "plano isd", "legacy west",
                "shops at legacy", "willow bend"
            ],
            ServiceArea.FRISCO: [
                "frisco", "frisco isd", "the star", "stonebriar", "legacy west frisco",
                "west frisco", "east frisco"
            ],
            ServiceArea.MCKINNEY: [
                "mckinney", "historic mckinney", "craig ranch", "stonebridge",
                "mckinney isd"
            ],
            ServiceArea.ALLEN: [
                "allen", "allen isd", "watters creek", "twin creeks", 
                "bethany lakes"
            ]
        }
        
        # Jorge's financing preference scoring
        self.financing_scoring = {
            'cash': 1.0,
            'pre_approved': 0.95,
            'conventional': 0.8,
            'jumbo': 0.85,
            'va': 0.9,
            'fha': 0.7,
            'needs_financing': 0.4,
            'unknown': 0.3
        }
    
    def qualify_lead_for_jorge(self, 
                              lead_intelligence: Dict[str, Any],
                              context: Optional[Dict] = None) -> JorgeLeadQualification:
        """
        Comprehensive lead qualification using Jorge's business rules
        
        Args:
            lead_intelligence: Output from enhanced lead intelligence
            context: Additional context (contact history, source, etc.)
            
        Returns:
            Complete qualification assessment
        """
        
        qualification = JorgeLeadQualification()
        
        try:
            # Extract key data points
            budget_max = lead_intelligence.get('budget_max', 0)
            timeline = lead_intelligence.get('timeline_analysis', 'unknown')
            locations = lead_intelligence.get('location_analysis', [])
            financing = lead_intelligence.get('financing_analysis', 'unknown')
            lead_score = lead_intelligence.get('lead_score', 0)
            
            # Assess budget fit
            qualification.budget_fit, budget_score = self._assess_budget_fit(budget_max)
            qualification.estimated_commission = self._calculate_commission(budget_max)
            qualification.commission_potential = self._assess_commission_potential(qualification.estimated_commission)
            
            # Assess geographic fit
            qualification.service_area = self._determine_service_area(locations)
            qualification.location_priority = self._assess_location_priority(qualification.service_area)
            
            # Assess timeline fit
            qualification.timeline_fit, timeline_score = self._assess_timeline_fit(timeline)
            qualification.urgency_level = self._assess_urgency_level(timeline, lead_intelligence)
            
            # Calculate overall qualification score
            qualification.qualification_score = self._calculate_jorge_score(
                budget_score, timeline_score, qualification.service_area, financing, lead_score
            )
            
            # Determine priority and qualification
            qualification.priority = self._determine_priority(qualification.qualification_score, qualification)
            qualification.meets_criteria = qualification.qualification_score >= self.criteria.COLD_LEAD_THRESHOLD
            
            # Identify factors
            qualification.qualifying_factors = self._identify_qualifying_factors(qualification, lead_intelligence)
            qualification.disqualifying_factors = self._identify_disqualifying_factors(qualification, lead_intelligence)
            qualification.improvement_opportunities = self._identify_improvements(qualification, lead_intelligence)
            
            # Jorge-specific recommendations
            qualification.recommended_action = self._recommend_action(qualification)
            qualification.follow_up_timeline = self._recommend_follow_up(qualification)
            qualification.jorge_notes = self._generate_jorge_notes(qualification, lead_intelligence)
            
            return qualification
            
        except Exception as e:
            self.logger.error(f"Error in Jorge lead qualification: {e}")
            # Return default qualification on error
            qualification.meets_criteria = False
            qualification.priority = LeadPriority.DISQUALIFIED
            qualification.disqualifying_factors = [f"System error: {str(e)}"]
            return qualification
    
    def _assess_budget_fit(self, budget_max: Optional[int]) -> Tuple[str, float]:
        """Assess how well budget fits Jorge's criteria"""
        if not budget_max or budget_max <= 0:
            return "unknown", 0.0
        
        if budget_max < self.criteria.MIN_BUDGET:
            return "poor", 0.0
        elif budget_max < self.criteria.IDEAL_BUDGET_MIN:
            return "marginal", 0.4
        elif budget_max <= self.criteria.IDEAL_BUDGET_MAX:
            return "excellent", 1.0
        elif budget_max <= self.criteria.MAX_BUDGET:
            return "good", 0.8
        else:
            return "review_required", 0.6  # Ultra-high budget needs special handling
    
    def _calculate_commission(self, budget_max: Optional[int]) -> float:
        """Calculate estimated commission"""
        if not budget_max:
            return 0.0
        return budget_max * self.criteria.STANDARD_COMMISSION_RATE
    
    def _assess_commission_potential(self, commission: float) -> str:
        """Assess commission potential level"""
        if commission >= 50000:  # $50K+
            return "high"
        elif commission >= 25000:  # $25K+
            return "medium"
        else:
            return "low"
    
    def _determine_service_area(self, locations: List[str]) -> ServiceArea:
        """Determine the primary service area from location preferences"""
        if not locations:
            return ServiceArea.OUT_OF_AREA
        
        # Check locations against Jorge's service areas
        for area, keywords in self.location_mapping.items():
            for location in locations:
                location_lower = location.lower()
                if any(keyword in location_lower for keyword in keywords):
                    return area
        
        return ServiceArea.OUT_OF_AREA
    
    def _assess_location_priority(self, service_area: ServiceArea) -> str:
        """Assess location priority based on Jorge's preferences"""
        if service_area in self.criteria.PRIMARY_AREAS:
            return "high"
        elif service_area in self.criteria.SECONDARY_AREAS:
            return "medium"
        else:
            return "low"
    
    def _assess_timeline_fit(self, timeline: str) -> Tuple[str, float]:
        """Assess timeline fit with Jorge's preferences"""
        if timeline in self.criteria.IMMEDIATE_TIMELINE:
            return "excellent", 1.0
        elif timeline in self.criteria.PREFERRED_TIMELINE:
            return "good", 0.8
        elif timeline in self.criteria.ACCEPTABLE_TIMELINE:
            return "fair", 0.5
        else:
            return "poor", 0.2
    
    def _assess_urgency_level(self, timeline: str, intelligence: Dict) -> str:
        """Assess overall urgency level"""
        urgency_score = intelligence.get('urgency', 0)
        
        if timeline in self.criteria.IMMEDIATE_TIMELINE or urgency_score > 0.8:
            return "high"
        elif timeline in self.criteria.PREFERRED_TIMELINE or urgency_score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _calculate_jorge_score(self, 
                              budget_score: float,
                              timeline_score: float, 
                              service_area: ServiceArea,
                              financing: str,
                              base_lead_score: float) -> float:
        """Calculate Jorge-specific qualification score"""
        
        # Start with base lead score (0-100)
        score = base_lead_score * 0.4  # 40% weight to base intelligence
        
        # Budget scoring (30% weight)
        score += budget_score * 30
        
        # Timeline scoring (15% weight)  
        score += timeline_score * 15
        
        # Location scoring (10% weight)
        if service_area in self.criteria.PRIMARY_AREAS:
            location_bonus = 10
        elif service_area in self.criteria.SECONDARY_AREAS:
            location_bonus = 7
        else:
            location_bonus = 0
        score += location_bonus
        
        # Financing scoring (5% weight)
        financing_multiplier = self.financing_scoring.get(financing, 0.3)
        score += financing_multiplier * 5
        
        return min(100.0, max(0.0, score))
    
    def _determine_priority(self, score: float, qualification: JorgeLeadQualification) -> LeadPriority:
        """Determine lead priority based on score and factors"""
        
        # Disqualify if budget too low
        if qualification.budget_fit == "poor":
            return LeadPriority.DISQUALIFIED
            
        # Urgent priority for excellent fits with high urgency
        if (score >= self.criteria.HOT_LEAD_THRESHOLD and 
            qualification.urgency_level == "high" and
            qualification.location_priority in ["high", "medium"]):
            return LeadPriority.URGENT
            
        # Priority based on score thresholds
        if score >= self.criteria.HOT_LEAD_THRESHOLD:
            return LeadPriority.HIGH
        elif score >= self.criteria.WARM_LEAD_THRESHOLD:
            return LeadPriority.NORMAL
        elif score >= self.criteria.COLD_LEAD_THRESHOLD:
            return LeadPriority.LOW
        else:
            return LeadPriority.NURTURE
    
    def _identify_qualifying_factors(self, 
                                   qualification: JorgeLeadQualification, 
                                   intelligence: Dict) -> List[str]:
        """Identify positive qualifying factors"""
        factors = []
        
        if qualification.budget_fit in ["excellent", "good"]:
            factors.append(f"Budget fits Jorge's target range (${qualification.estimated_commission:,.0f} commission)")
            
        if qualification.location_priority in ["high", "medium"]:
            factors.append(f"Location in Jorge's service area ({qualification.service_area.value})")
            
        if qualification.timeline_fit in ["excellent", "good"]:
            factors.append("Timeline aligns with market conditions")
            
        if intelligence.get('is_pre_approved', False):
            factors.append("Pre-approved financing (ready to move)")
            
        if intelligence.get('financing_analysis') == 'cash':
            factors.append("Cash buyer (no financing contingency)")
            
        if qualification.urgency_level == "high":
            factors.append("High urgency indicators")
            
        return factors
    
    def _identify_disqualifying_factors(self,
                                      qualification: JorgeLeadQualification,
                                      intelligence: Dict) -> List[str]:
        """Identify negative disqualifying factors"""
        factors = []
        
        if qualification.budget_fit == "poor":
            factors.append("Budget below minimum threshold")
            
        if qualification.service_area == ServiceArea.OUT_OF_AREA:
            factors.append("Outside Jorge's service area")
            
        if qualification.timeline_fit == "poor":
            factors.append("Timeline too long or unclear")
            
        if intelligence.get('financing_analysis') == 'needs_financing':
            factors.append("Needs financing approval")
            
        if not intelligence.get('has_specific_budget', False):
            factors.append("No specific budget provided")
            
        return factors
    
    def _identify_improvements(self,
                             qualification: JorgeLeadQualification, 
                             intelligence: Dict) -> List[str]:
        """Identify opportunities for improvement"""
        opportunities = []
        
        if not intelligence.get('has_specific_budget', False):
            opportunities.append("Clarify budget range and pre-approval status")
            
        if not intelligence.get('has_location_preference', False):
            opportunities.append("Identify specific neighborhood preferences")
            
        if qualification.timeline_fit in ["fair", "poor"]:
            opportunities.append("Understand timeline flexibility and motivations")
            
        if intelligence.get('financing_analysis') == 'unknown':
            opportunities.append("Assess financing readiness and options")
            
        if qualification.urgency_level == "low":
            opportunities.append("Identify urgency factors or life events driving move")
            
        return opportunities
    
    def _recommend_action(self, qualification: JorgeLeadQualification) -> str:
        """Recommend specific action for Jorge"""
        
        if qualification.priority == LeadPriority.URGENT:
            return "immediate_contact"
        elif qualification.priority == LeadPriority.HIGH:
            return "priority_follow_up"
        elif qualification.priority == LeadPriority.NORMAL:
            return "standard_follow_up"
        elif qualification.priority == LeadPriority.LOW:
            return "nurture_sequence"
        elif qualification.priority == LeadPriority.NURTURE:
            return "long_term_nurture"
        else:
            return "disqualify"
    
    def _recommend_follow_up(self, qualification: JorgeLeadQualification) -> str:
        """Recommend follow-up timeline"""
        
        if qualification.urgency_level == "high":
            return "within_1_hour"
        elif qualification.priority == LeadPriority.HIGH:
            return "within_4_hours"
        elif qualification.priority == LeadPriority.NORMAL:
            return "same_day"
        elif qualification.priority == LeadPriority.LOW:
            return "within_24_hours"
        else:
            return "weekly_nurture"
    
    def _generate_jorge_notes(self,
                             qualification: JorgeLeadQualification,
                             intelligence: Dict) -> str:
        """Generate Jorge-specific notes and insights"""
        
        notes_parts = []
        
        # Lead quality summary
        notes_parts.append(f"Jorge Score: {qualification.qualification_score:.0f}/100")
        notes_parts.append(f"Priority: {qualification.priority.value.upper()}")
        
        # Key highlights
        if qualification.estimated_commission > 30000:
            notes_parts.append(f"HIGH VALUE: ${qualification.estimated_commission:,.0f} commission potential")
            
        if qualification.urgency_level == "high":
            notes_parts.append("URGENT: High urgency signals detected")
            
        if qualification.service_area in [ServiceArea.PLANO, ServiceArea.FRISCO]:
            notes_parts.append(f"PRIME AREA: {qualification.service_area.value} location")
            
        # Strategic insights
        if intelligence.get('financing_analysis') == 'cash':
            notes_parts.append("CASH BUYER: No financing contingency")
            
        if len(qualification.improvement_opportunities) > 0:
            notes_parts.append(f"OPPORTUNITIES: {', '.join(qualification.improvement_opportunities[:2])}")
        
        return " | ".join(notes_parts)


def integrate_with_feature_engineering(jorge_qualification: JorgeLeadQualification) -> Dict[str, Any]:
    """
    Convert Jorge qualification results to feature engineering compatible format
    
    This function bridges Jorge's business rules with the ML feature pipeline.
    """
    
    return {
        # Numerical features from Jorge analysis
        'jorge_qualification_score': jorge_qualification.qualification_score,
        'jorge_commission_potential': jorge_qualification.estimated_commission,
        'jorge_location_priority_score': _convert_location_priority_to_score(jorge_qualification.location_priority),
        'jorge_timeline_fit_score': _convert_timeline_fit_to_score(jorge_qualification.timeline_fit),
        
        # Categorical features
        'jorge_priority_category': jorge_qualification.priority.value,
        'jorge_service_area': jorge_qualification.service_area.value,
        'jorge_budget_fit_category': jorge_qualification.budget_fit,
        'jorge_recommended_action': jorge_qualification.recommended_action,
        
        # Boolean features
        'meets_jorge_criteria': jorge_qualification.meets_criteria,
        'jorge_high_commission': qualification.commission_potential == "high",
        'jorge_primary_area': jorge_qualification.service_area in [ServiceArea.PLANO, ServiceArea.FRISCO],
        'jorge_immediate_action': jorge_qualification.recommended_action in ["immediate_contact", "priority_follow_up"],
        
        # Additional context
        'jorge_qualifying_factors_count': len(jorge_qualification.qualifying_factors),
        'jorge_disqualifying_factors_count': len(jorge_qualification.disqualifying_factors),
        'jorge_notes': jorge_qualification.jorge_notes
    }


def _convert_location_priority_to_score(priority: str) -> float:
    """Convert location priority to numerical score"""
    mapping = {"high": 1.0, "medium": 0.6, "low": 0.2}
    return mapping.get(priority, 0.0)


def _convert_timeline_fit_to_score(fit: str) -> float:
    """Convert timeline fit to numerical score"""
    mapping = {"excellent": 1.0, "good": 0.8, "fair": 0.5, "poor": 0.2}
    return mapping.get(fit, 0.0)


def create_jorge_business_rules_factory():
    """Factory function to create Jorge business rules engine"""
    return JorgeBusinessRulesEngine()


# Example usage and testing
if __name__ == '__main__':
    # Demo Jorge business rules integration
    print("🏢 Jorge Business Rules Integration Demo")
    print("=" * 50)
    
    # Sample lead intelligence data
    sample_intelligence = {
        'lead_score': 78.5,
        'budget_max': 550000,
        'timeline_analysis': '2_months',
        'location_analysis': ['Plano', 'Frisco'],
        'financing_analysis': 'pre_approved',
        'has_specific_budget': True,
        'has_location_preference': True,
        'is_pre_approved': True,
        'urgency': 0.7
    }
    
    # Initialize rules engine
    rules_engine = JorgeBusinessRulesEngine()
    
    # Qualify the lead
    qualification = rules_engine.qualify_lead_for_jorge(sample_intelligence)
    
    print(f"\n📊 Lead Qualification Results:")
    print(f"   - Meets Criteria: {'✅' if qualification.meets_criteria else '❌'}")
    print(f"   - Priority: {qualification.priority.value.upper()}")
    print(f"   - Jorge Score: {qualification.qualification_score:.1f}/100")
    print(f"   - Commission Potential: ${qualification.estimated_commission:,.0f}")
    print(f"   - Service Area: {qualification.service_area.value}")
    print(f"   - Recommended Action: {qualification.recommended_action}")
    
    print(f"\n✅ Qualifying Factors:")
    for factor in qualification.qualifying_factors:
        print(f"   - {factor}")
    
    if qualification.disqualifying_factors:
        print(f"\n❌ Disqualifying Factors:")
        for factor in qualification.disqualifying_factors:
            print(f"   - {factor}")
    
    if qualification.improvement_opportunities:
        print(f"\n🔄 Improvement Opportunities:")
        for opportunity in qualification.improvement_opportunities:
            print(f"   - {opportunity}")
    
    print(f"\n📝 Jorge Notes: {qualification.jorge_notes}")
    
    print(f"\n🔗 Feature Engineering Integration:")
    feature_data = integrate_with_feature_engineering(qualification)
    for key, value in feature_data.items():
        if isinstance(value, float):
            print(f"   - {key}: {value:.2f}")
        else:
            print(f"   - {key}: {value}")