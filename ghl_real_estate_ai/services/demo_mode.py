"""
Live Demo Mode - Data Generator

Generates realistic demo data for impressive client demos
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List


class DemoModeManager:
    """Generate realistic demo data for live demonstrations"""

    def __init__(self):
        self.names = [
            "Sarah Johnson",
            "Mike Chen",
            "Lisa Brown",
            "David Kim",
            "Jennifer Garcia",
            "Robert Taylor",
            "Maria Rodriguez",
            "James Wilson",
            "Amanda Martinez",
            "Chris Anderson",
            "Jessica Thomas",
            "Michael Lee",
        ]

        self.phone_numbers = [
            "512-555-0101",
            "512-555-0102",
            "512-555-0103",
            "512-555-0104",
            "512-555-0105",
            "512-555-0106",
            "512-555-0107",
            "512-555-0108",
        ]

        self.property_interests = [
            "3 bedroom house in downtown",
            "Condo with lake view",
            "Family home with large yard",
            "Modern townhouse near schools",
            "Luxury property in hill country",
            "Starter home for first-time buyer",
            "Investment property",
            "Ranch-style home with acreage",
        ]

    def generate_demo_dataset(self, num_conversations: int = 100, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate complete demo dataset

        Args:
            num_conversations: Number of conversations to generate
            days_back: How many days of history to create

        Returns:
            Complete demo dataset with conversations, metrics, and trends
        """
        conversations = self._generate_conversations(num_conversations, days_back)
        metrics = self._calculate_demo_metrics(conversations)
        trends = self._generate_trends(conversations, days_back)

        return {
            "demo_metadata": {
                "generated_at": datetime.now().isoformat(),
                "scenario": "real_estate_agency",
                "conversations": num_conversations,
                "date_range": {
                    "start": (datetime.now() - timedelta(days=days_back)).isoformat(),
                    "end": datetime.now().isoformat(),
                },
            },
            "conversations": conversations,
            "metrics": metrics,
            "trends": trends,
        }

    def _generate_conversations(self, count: int, days_back: int) -> List[Dict[str, Any]]:
        """Generate realistic conversation data"""
        conversations = []

        for i in range(count):
            # Random timestamp within date range
            days_ago = random.randint(0, days_back)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

            # Random lead quality distribution: 20% hot, 35% warm, 45% cold
            rand = random.random()
            if rand < 0.20:
                lead_score = random.randint(70, 95)
                classification = "hot"
            elif rand < 0.55:
                lead_score = random.randint(40, 69)
                classification = "warm"
            else:
                lead_score = random.randint(10, 39)
                classification = "cold"

            # Generate messages
            num_messages = random.randint(3, 12)
            messages = self._generate_messages(num_messages, classification)

            # Response time (hot leads respond faster)
            if classification == "hot":
                response_time = random.randint(30, 180)  # 30s - 3min
            elif classification == "warm":
                response_time = random.randint(120, 600)  # 2-10min
            else:
                response_time = random.randint(300, 1800)  # 5-30min

            # Appointment set? (hot: 80%, warm: 40%, cold: 5%)
            appointment_set = (
                (classification == "hot" and random.random() < 0.8)
                or (classification == "warm" and random.random() < 0.4)
                or (classification == "cold" and random.random() < 0.05)
            )

            conversation = {
                "conversation_id": f"conv_{i + 1:04d}",
                "contact_id": f"contact_{i + 1:04d}",
                "name": random.choice(self.names),
                "phone": random.choice(self.phone_numbers),
                "timestamp": timestamp.isoformat(),
                "lead_score": lead_score,
                "classification": classification,
                "response_time_minutes": round(response_time / 60, 1),
                "response_time_seconds": response_time,
                "appointment_set": appointment_set,
                "property_interest": random.choice(self.property_interests),
                "messages": messages,
                "budget_range": self._generate_budget(classification),
                "timeline": self._generate_timeline(classification),
            }

            conversations.append(conversation)

        return conversations

    def _generate_messages(self, count: int, classification: str) -> List[Dict[str, Any]]:
        """Generate realistic message exchange"""
        hot_lead_messages = [
            "Hi, I'm interested in viewing properties this weekend",
            "I'm pre-approved for $600K and ready to buy",
            "Can you send me listings for 3-bedroom homes?",
            "What time works for a showing?",
            "I'm relocating for work and need to move quickly",
        ]

        warm_lead_messages = [
            "Looking for information about homes in Austin",
            "What's the market like right now?",
            "I'm thinking about buying in the next few months",
            "Can you tell me more about the area?",
            "What should I expect for price range?",
        ]

        cold_lead_messages = [
            "Just browsing",
            "How much are houses in this area?",
            "Tell me about your services",
            "I might be interested later",
            "Can you send me some info?",
        ]

        if classification == "hot":
            pool = hot_lead_messages
        elif classification == "warm":
            pool = warm_lead_messages
        else:
            pool = cold_lead_messages

        messages = []
        for i in range(min(count, len(pool))):
            messages.append(
                {
                    "message_id": f"msg_{i + 1}",
                    "text": pool[i] if i < len(pool) else "Thanks for the information",
                    "from": "contact" if i % 2 == 0 else "agent",
                    "timestamp": (datetime.now() - timedelta(minutes=count - i)).isoformat(),
                }
            )

        return messages

    def _generate_budget(self, classification: str) -> str:
        """Generate budget based on lead quality"""
        if classification == "hot":
            budgets = ["$500-600K", "$600-700K", "$400-500K", "$700K+"]
        elif classification == "warm":
            budgets = ["$300-400K", "$400-500K", "Not sure yet", "$500K range"]
        else:
            budgets = ["Not specified", "Just looking", "Need to check", "TBD"]

        return random.choice(budgets)

    def _generate_timeline(self, classification: str) -> str:
        """Generate timeline based on lead quality"""
        if classification == "hot":
            timelines = ["ASAP", "1-2 weeks", "This month", "Urgent"]
        elif classification == "warm":
            timelines = ["2-3 months", "Next quarter", "This year", "6 months"]
        else:
            timelines = ["Just exploring", "No rush", "Eventually", "TBD"]

        return random.choice(timelines)

    def _calculate_demo_metrics(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics for demo"""
        total = len(conversations)
        hot = len([c for c in conversations if c["classification"] == "hot"])
        warm = len([c for c in conversations if c["classification"] == "warm"])
        cold = len([c for c in conversations if c["classification"] == "cold"])

        appointments = len([c for c in conversations if c["appointment_set"]])

        response_times = [c["response_time_minutes"] for c in conversations]
        avg_response = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_conversations": total,
            "lead_distribution": {"hot": hot, "warm": warm, "cold": cold},
            "conversion": {
                "appointments_set": appointments,
                "conversion_rate": (round((appointments / total * 100), 1) if total > 0 else 0),
            },
            "response_time": {
                "average_minutes": round(avg_response, 1),
                "meeting_target": avg_response <= 2.0,
            },
            "pipeline_value": hot * 12500,
        }

    def _generate_trends(self, conversations: List[Dict], days: int) -> Dict[str, List]:
        """
        Execute generate trends operation.

        Args:
            conversations: Conversations parameter
            days: Days parameter

        Returns:
            Result of the operation
        """
        """Generate trend data"""
        daily_data = {}

        for conv in conversations:
            date = datetime.fromisoformat(conv["timestamp"]).date()
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(conv)

        trends = []
        for date in sorted(daily_data.keys()):
            day_convos = daily_data[date]
            hot_count = len([c for c in day_convos if c["classification"] == "hot"])

            trends.append(
                {
                    "date": date.isoformat(),
                    "conversations": len(day_convos),
                    "hot_leads": hot_count,
                }
            )

        return {"daily": trends}


class DemoScenario:
    """Pre-configured demo scenario"""

    SCENARIOS = {
        "real_estate_agency": {
            "name": "Real Estate Agency - Jorge's Business",
            "description": "30 days of lead qualification data",
            "conversations": 120,
            "days": 30,
        },
        "property_management": {
            "name": "Property Management Company",
            "description": "Tenant inquiry and leasing",
            "conversations": 200,
            "days": 30,
        },
        "mortgage_brokerage": {
            "name": "Mortgage Brokerage",
            "description": "Loan qualification conversations",
            "conversations": 150,
            "days": 30,
        },
    }

    @classmethod
    def list_scenarios(cls) -> List[Dict[str, str]]:
        """List available demo scenarios"""
        return [
            {
                "id": key,
                "name": scenario["name"],
                "description": scenario["description"],
            }
            for key, scenario in cls.SCENARIOS.items()
        ]

    @classmethod
    def generate_scenario(cls, scenario_id: str) -> Dict[str, Any]:
        """Generate data for specific scenario"""
        if scenario_id not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        scenario = cls.SCENARIOS[scenario_id]
        generator = DemoModeManager()

        return generator.generate_demo_dataset(num_conversations=scenario["conversations"], days_back=scenario["days"])
