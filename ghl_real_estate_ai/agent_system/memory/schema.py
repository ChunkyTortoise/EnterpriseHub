"""
Graphiti Schema Definition for Real Estate AI.
Reference: AGENT_MEMORY_STRATEGY.md
"""

from typing import Dict

# Entity Types
ENTITY_LEAD = "Lead"
ENTITY_AGENT = "Agent"
ENTITY_PROPERTY = "Property"
ENTITY_LOCATION = "Location"
ENTITY_CRITERION = "Criterion"

ENTITY_TYPES = [ENTITY_LEAD, ENTITY_AGENT, ENTITY_PROPERTY, ENTITY_LOCATION, ENTITY_CRITERION]

# Relation Types
REL_INTERESTED_IN = "INTERESTED_IN"  # Lead -> Property
REL_LOCATED_IN = "LOCATED_IN"  # Property -> Location
REL_HAS_BUDGET = "HAS_BUDGET"  # Lead -> Criterion
REL_DISLIKES = "DISLIKES"  # Lead -> Criterion/Property (implied by "REJECTED" or "Strong Opinions")
REL_REJECTED = "REJECTED"  # Lead -> Property
REL_WORKS_WITH = "WORKS_WITH"  # Lead -> Agent
REL_HAS_TIMELINE = "HAS_TIMELINE"  # Lead -> Event/Date (generalized)
REL_OFFERING_ON = "OFFERING_ON"  # Lead -> Property

RELATION_TYPES = [
    REL_INTERESTED_IN,
    REL_LOCATED_IN,
    REL_HAS_BUDGET,
    REL_DISLIKES,
    REL_REJECTED,
    REL_WORKS_WITH,
    REL_HAS_TIMELINE,
    REL_OFFERING_ON,
]


def get_schema_config() -> Dict:
    """Returns the schema configuration for Graphiti initialization."""
    return {"entities": ENTITY_TYPES, "relations": RELATION_TYPES}
