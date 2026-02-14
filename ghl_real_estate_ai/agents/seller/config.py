"""
Configuration and dataclasses for Jorge Seller Bot.

This module contains configuration classes and result types used throughout
the seller bot ecosystem.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JorgeFeatureConfig:
    """Configuration for Jorge's enhanced features"""

    enable_progressive_skills: bool = False
    enable_agent_mesh: bool = False
    enable_mcp_integration: bool = False
    enable_adaptive_questioning: bool = False
    enable_track3_intelligence: bool = True  # Default enabled
    enable_bot_intelligence: bool = True  # Phase 3.3 Intelligence Integration
    jorge_handoff_enabled: bool = True

    # Performance settings
    max_concurrent_tasks: int = 5
    sla_response_time: int = 15  # seconds
    cost_per_token: float = 0.000015

    # Jorge-specific settings
    commission_rate: float = 0.06
    friendly_approach_enabled: bool = True
    temperature_thresholds: Optional[Dict[str, int]] = None

    def __post_init__(self):
        if self.temperature_thresholds is None:
            self.temperature_thresholds = {"hot": 75, "warm": 50, "lukewarm": 25}


@dataclass
class QualificationResult:
    """Comprehensive qualification result with all enhancement metadata"""

    lead_id: str
    qualification_score: float
    frs_score: float
    pcs_score: float
    temperature: str
    next_actions: List[str]
    confidence: float
    tokens_used: int
    cost_incurred: float

    # Enhancement metadata
    progressive_skills_applied: bool = False
    mesh_task_id: Optional[str] = None
    orchestrated_tasks: List[str] = field(default_factory=list)
    mcp_enrichment_applied: bool = False
    adaptive_questioning_used: bool = False
    timeline_ms: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.orchestrated_tasks is None:
            self.orchestrated_tasks = []
        if self.timeline_ms is None:
            self.timeline_ms = {}
