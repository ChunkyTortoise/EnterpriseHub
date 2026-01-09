"""
Team Management Service for GHL Real Estate AI.

Handles agent profiles, team structure, and lead assignment logic.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TeamManager:
    """
    Manages team members (agents) and their performance within a location.
    """

    def __init__(self, location_id: str):
        """
        Initialize team manager for a specific location.
        """
        self.location_id = location_id
        self.team_dir = Path(__file__).parent.parent / "data" / "teams" / location_id
        self.team_dir.mkdir(parents=True, exist_ok=True)
        self.agents_file = self.team_dir / "agents.json"
        self.assignments_file = self.team_dir / "assignments.json"
        self.agents = self._load_agents()
        self.assignments = self._load_assignments()

    def _load_agents(self) -> Dict[str, Any]:
        """Load agent data from file."""
        if self.agents_file.exists():
            with open(self.agents_file, 'r') as f:
                return json.load(f)
        return {}

    def _load_assignments(self) -> Dict[str, Any]:
        """Load assignment data from file."""
        if self.assignments_file.exists():
            with open(self.assignments_file, 'r') as f:
                return json.load(f)
        return {"last_index": -1, "mapping": {}}

    def _save_agents(self):
        """Save agent data to file."""
        with open(self.agents_file, 'w') as f:
            json.dump(self.agents, f, indent=2)

    def _save_assignments(self):
        """Save assignment data to file."""
        with open(self.assignments_file, 'w') as f:
            json.dump(self.assignments, f, indent=2)

    def add_agent(
        self,
        agent_id: str,
        name: str,
        email: str,
        role: str = "agent",
        specialties: List[str] = None
    ):
        """Add a new agent to the team."""
        self.agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "email": email,
            "role": role,
            "specialties": specialties or [],
            "status": "active",
            "metrics": {
                "total_leads": 0,
                "converted_leads": 0,
                "avg_response_time": 0,
                "rating": 5.0
            },
            "created_at": datetime.utcnow().isoformat()
        }
        self._save_agents()
        logger.info(f"Added agent {name} ({agent_id}) to location {self.location_id}")

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details."""
        return self.agents.get(agent_id)

    def list_agents(self, status: str = "active") -> List[Dict[str, Any]]:
        """List all agents in the location."""
        return [a for a in self.agents.values() if a["status"] == status]

    def assign_lead(self, contact_id: str, criteria: Dict[str, Any] = None) -> Optional[str]:
        """
        Assign a lead to an agent using Round Robin or criteria matching.
        """
        # If already assigned, return current agent
        if contact_id in self.assignments["mapping"]:
            return self.assignments["mapping"][contact_id]

        active_agents = self.list_agents()
        if not active_agents:
            logger.warning(f"No active agents available for assignment in {self.location_id}")
            return None

        # Round Robin Logic
        self.assignments["last_index"] = (self.assignments["last_index"] + 1) % len(active_agents)
        selected_agent = active_agents[self.assignments["last_index"]]
        
        agent_id = selected_agent["id"]
        self.assignments["mapping"][contact_id] = agent_id
        
        # Update agent metrics
        self.agents[agent_id]["metrics"]["total_leads"] += 1
        
        self._save_assignments()
        self._save_agents()
        
        logger.info(f"Assigned lead {contact_id} to agent {selected_agent['name']} ({agent_id})")
        return agent_id

    def update_agent_performance(self, agent_id: str, conversion: bool = False, rating: float = None):
        """Update agent performance metrics."""
        if agent_id not in self.agents:
            return

        metrics = self.agents[agent_id]["metrics"]
        if conversion:
            metrics["converted_leads"] += 1
        
        if rating is not None:
            # Weighted average for rating
            current_rating = metrics.get("rating", 5.0)
            total_leads = metrics.get("total_leads", 1)
            metrics["rating"] = round((current_rating * (total_leads - 1) + rating) / total_leads, 2)

        self._save_agents()

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get team leaderboard based on conversion rate."""
        leaderboard = []
        for agent in self.agents.values():
            metrics = agent["metrics"]
            leads = metrics["total_leads"]
            conv = metrics["converted_leads"]
            rate = (conv / leads * 100) if leads > 0 else 0
            
            leaderboard.append({
                "name": agent["name"],
                "total_leads": leads,
                "conversions": conv,
                "conversion_rate": round(rate, 1),
                "rating": metrics["rating"]
            })
            
        return sorted(leaderboard, key=lambda x: x["conversion_rate"], reverse=True)
