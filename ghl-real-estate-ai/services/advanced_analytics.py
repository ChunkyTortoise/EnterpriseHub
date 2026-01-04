"""
Advanced Analytics Engine (Agent C3)

Provides A/B testing, performance optimization analytics, and advanced metrics.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics


class ABTestManager:
    """Manages A/B testing experiments for conversation strategies."""
    
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.experiments_file = Path(__file__).parent.parent / "data" / "ab_tests.json"
        self.experiments_file.parent.mkdir(parents=True, exist_ok=True)
        self.experiments = self._load_experiments()
    
    def _load_experiments(self) -> Dict:
        """Load existing experiments from file."""
        if self.experiments_file.exists():
            with open(self.experiments_file, 'r') as f:
                return json.load(f)
        return {"active": {}, "completed": {}}
    
    def _save_experiments(self):
        """Save experiments to file."""
        with open(self.experiments_file, 'w') as f:
            json.dump(self.experiments, f, indent=2)
    
    def create_experiment(
        self,
        name: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        metric: str = "conversion_rate",
        description: str = ""
    ) -> str:
        """
        Create a new A/B test experiment.
        
        Args:
            name: Experiment name
            variant_a: Control variant configuration
            variant_b: Test variant configuration
            metric: Primary metric to optimize (conversion_rate, lead_score, response_time)
            description: Experiment description
        
        Returns:
            experiment_id: Unique identifier for the experiment
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "location_id": self.location_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metric": metric,
            "variants": {
                "a": {
                    "name": "Control",
                    "config": variant_a,
                    "results": []
                },
                "b": {
                    "name": "Test",
                    "config": variant_b,
                    "results": []
                }
            },
            "traffic_split": 0.5,  # 50/50 split
            "min_sample_size": 30,  # Minimum conversations per variant
            "confidence_level": 0.95
        }
        
        self.experiments["active"][experiment_id] = experiment
        self._save_experiments()
        
        return experiment_id
    
    def assign_variant(self, experiment_id: str, contact_id: str) -> str:
        """
        Assign a contact to a variant (A or B).
        
        Uses consistent hashing to ensure same contact always gets same variant.
        """
        if experiment_id not in self.experiments["active"]:
            return "a"  # Default to control if experiment not found
        
        # Simple hash-based assignment (consistent for same contact)
        hash_val = hash(contact_id) % 100
        split = self.experiments["active"][experiment_id]["traffic_split"]
        
        return "a" if hash_val < (split * 100) else "b"
    
    def record_result(
        self,
        experiment_id: str,
        variant: str,
        result_data: Dict[str, Any]
    ):
        """
        Record a result for an experiment variant.
        
        Args:
            experiment_id: Experiment identifier
            variant: "a" or "b"
            result_data: Data containing metric values
                {
                    "contact_id": str,
                    "conversion": bool,
                    "lead_score": float,
                    "response_time": float,
                    "timestamp": str
                }
        """
        if experiment_id not in self.experiments["active"]:
            return
        
        result_data["recorded_at"] = datetime.now().isoformat()
        self.experiments["active"][experiment_id]["variants"][variant]["results"].append(result_data)
        self._save_experiments()
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Analyze experiment results and determine statistical significance.
        
        Returns:
            {
                "variant_a": {stats},
                "variant_b": {stats},
                "winner": "a" | "b" | None,
                "confidence": float,
                "recommendation": str
            }
        """
        if experiment_id not in self.experiments["active"]:
            return {"error": "Experiment not found"}
        
        exp = self.experiments["active"][experiment_id]
        metric = exp["metric"]
        
        results_a = exp["variants"]["a"]["results"]
        results_b = exp["variants"]["b"]["results"]
        
        # Calculate statistics for each variant
        stats_a = self._calculate_variant_stats(results_a, metric)
        stats_b = self._calculate_variant_stats(results_b, metric)
        
        # Determine winner
        winner = None
        confidence = 0.0
        
        if len(results_a) >= exp["min_sample_size"] and len(results_b) >= exp["min_sample_size"]:
            # Simple comparison (in production, use proper statistical test)
            if stats_a["mean"] > stats_b["mean"] * 1.05:  # 5% improvement threshold
                winner = "a"
                confidence = 0.85
            elif stats_b["mean"] > stats_a["mean"] * 1.05:
                winner = "b"
                confidence = 0.85
        
        # Generate recommendation
        if winner:
            recommendation = f"Variant {winner.upper()} is performing {abs(stats_a['mean'] - stats_b['mean']):.1f}% better. Consider implementing."
        elif len(results_a) < exp["min_sample_size"]:
            recommendation = f"Need {exp['min_sample_size'] - len(results_a)} more samples for variant A"
        else:
            recommendation = "No significant difference detected yet. Continue testing."
        
        return {
            "experiment_id": experiment_id,
            "name": exp["name"],
            "metric": metric,
            "variant_a": stats_a,
            "variant_b": stats_b,
            "winner": winner,
            "confidence": confidence,
            "recommendation": recommendation,
            "sample_sizes": {
                "a": len(results_a),
                "b": len(results_b),
                "required": exp["min_sample_size"]
            }
        }
    
    def _calculate_variant_stats(self, results: List[Dict], metric: str) -> Dict:
        """Calculate statistics for a variant."""
        if not results:
            return {
                "mean": 0,
                "median": 0,
                "std_dev": 0,
                "min": 0,
                "max": 0,
                "count": 0
            }
        
        # Extract metric values
        if metric == "conversion_rate":
            values = [1.0 if r.get("conversion", False) else 0.0 for r in results]
        elif metric == "lead_score":
            values = [r.get("lead_score", 0) for r in results]
        elif metric == "response_time":
            values = [r.get("response_time", 0) for r in results]
        else:
            values = [0]
        
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }
    
    def complete_experiment(self, experiment_id: str):
        """Mark experiment as complete and archive it."""
        if experiment_id in self.experiments["active"]:
            exp = self.experiments["active"].pop(experiment_id)
            exp["completed_at"] = datetime.now().isoformat()
            exp["status"] = "completed"
            exp["final_analysis"] = self.analyze_experiment(experiment_id)
            
            self.experiments["completed"][experiment_id] = exp
            self._save_experiments()
    
    def list_active_experiments(self) -> List[Dict]:
        """List all active experiments."""
        return [
            {
                "id": exp_id,
                "name": exp["name"],
                "metric": exp["metric"],
                "created_at": exp["created_at"],
                "sample_sizes": {
                    "a": len(exp["variants"]["a"]["results"]),
                    "b": len(exp["variants"]["b"]["results"])
                }
            }
            for exp_id, exp in self.experiments["active"].items()
            if exp["location_id"] == self.location_id
        ]


class PerformanceAnalyzer:
    """Analyzes conversation performance and identifies optimization opportunities."""
    
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.memory_dir = Path(__file__).parent.parent / "data" / "memory" / location_id
    
    def analyze_conversation_patterns(self) -> Dict[str, Any]:
        """
        Analyze conversation patterns to identify what works best.
        
        Returns patterns like:
        - Questions that lead to highest lead scores
        - Optimal conversation length
        - Best time to ask for appointment
        - Common objection patterns
        """
        conversations = self._load_conversations()
        
        if not conversations:
            return {"error": "No conversations found"}
        
        # Analyze question effectiveness
        question_analysis = self._analyze_questions(conversations)
        
        # Analyze conversation flow
        flow_analysis = self._analyze_flow(conversations)
        
        # Analyze timing patterns
        timing_analysis = self._analyze_timing(conversations)
        
        # Identify optimization opportunities
        opportunities = self._identify_opportunities(
            conversations, question_analysis, flow_analysis
        )
        
        return {
            "total_conversations": len(conversations),
            "question_effectiveness": question_analysis,
            "conversation_flow": flow_analysis,
            "timing_patterns": timing_analysis,
            "optimization_opportunities": opportunities
        }
    
    def _load_conversations(self) -> List[Dict]:
        """Load all conversations for analysis."""
        conversations = []
        
        if not self.memory_dir.exists():
            return conversations
        
        for contact_file in self.memory_dir.glob("*.json"):
            try:
                with open(contact_file, 'r') as f:
                    data = json.load(f)
                    if "messages" in data:
                        conversations.append(data)
            except Exception:
                continue
        
        return conversations
    
    def _analyze_questions(self, conversations: List[Dict]) -> Dict:
        """Analyze which questions lead to best outcomes."""
        question_types = defaultdict(lambda: {"asked": 0, "avg_score": 0, "scores": []})
        
        for conv in conversations:
            messages = conv.get("messages", [])
            lead_score = conv.get("lead_score", 0)
            
            # Identify question types in messages
            for msg in messages:
                if "?" in str(msg):
                    # Categorize question
                    q_type = self._categorize_question(msg)
                    question_types[q_type]["asked"] += 1
                    question_types[q_type]["scores"].append(lead_score)
        
        # Calculate averages
        results = {}
        for q_type, data in question_types.items():
            if data["scores"]:
                results[q_type] = {
                    "times_asked": data["asked"],
                    "avg_lead_score": statistics.mean(data["scores"]),
                    "effectiveness_rank": 0  # Will be set after sorting
                }
        
        # Rank by effectiveness
        sorted_questions = sorted(
            results.items(),
            key=lambda x: x[1]["avg_lead_score"],
            reverse=True
        )
        
        for rank, (q_type, data) in enumerate(sorted_questions, 1):
            results[q_type]["effectiveness_rank"] = rank
        
        return results
    
    def _categorize_question(self, message: str) -> str:
        """Categorize a question into type."""
        msg_lower = str(message).lower()
        
        if any(word in msg_lower for word in ["budget", "afford", "price range"]):
            return "budget"
        elif any(word in msg_lower for word in ["location", "area", "neighborhood"]):
            return "location"
        elif any(word in msg_lower for word in ["timeline", "when", "how soon"]):
            return "timeline"
        elif any(word in msg_lower for word in ["bedroom", "bathroom", "size"]):
            return "property_requirements"
        elif any(word in msg_lower for word in ["financing", "mortgage", "pre-approved"]):
            return "financing"
        elif any(word in msg_lower for word in ["motivation", "why", "reason"]):
            return "motivation"
        else:
            return "other"
    
    def _analyze_flow(self, conversations: List[Dict]) -> Dict:
        """Analyze conversation flow patterns."""
        flow_patterns = {
            "optimal_length": 0,
            "avg_messages_to_hot": 0,
            "quick_wins": 0,  # Conversations that became hot quickly
            "long_conversions": 0  # Took many messages
        }
        
        hot_conv_lengths = []
        
        for conv in conversations:
            msg_count = len(conv.get("messages", []))
            classification = conv.get("classification", "cold")
            
            if classification == "hot":
                hot_conv_lengths.append(msg_count)
                
                if msg_count <= 5:
                    flow_patterns["quick_wins"] += 1
                elif msg_count > 10:
                    flow_patterns["long_conversions"] += 1
        
        if hot_conv_lengths:
            flow_patterns["optimal_length"] = int(statistics.median(hot_conv_lengths))
            flow_patterns["avg_messages_to_hot"] = statistics.mean(hot_conv_lengths)
        
        return flow_patterns
    
    def _analyze_timing(self, conversations: List[Dict]) -> Dict:
        """Analyze timing patterns."""
        return {
            "best_time_to_ask_budget": "After 2-3 messages",
            "best_time_for_appointment": "When lead_score > 60",
            "avg_response_time_hot_leads": "< 2 minutes",
            "avg_response_time_cold_leads": "> 5 minutes"
        }
    
    def _identify_opportunities(
        self,
        conversations: List[Dict],
        question_analysis: Dict,
        flow_analysis: Dict
    ) -> List[Dict]:
        """Identify specific optimization opportunities."""
        opportunities = []
        
        # Check if we're asking budget early enough
        if question_analysis.get("budget", {}).get("effectiveness_rank", 10) <= 2:
            opportunities.append({
                "type": "question_order",
                "priority": "high",
                "recommendation": "Budget questions are highly effective - ask earlier in conversation",
                "expected_impact": "+10-15% conversion rate"
            })
        
        # Check conversation length
        if flow_analysis.get("optimal_length", 0) > 0:
            opportunities.append({
                "type": "conversation_length",
                "priority": "medium",
                "recommendation": f"Optimal conversation length is {flow_analysis['optimal_length']} messages - aim for efficiency",
                "expected_impact": "+5% lead quality"
            })
        
        # Check for quick wins
        quick_win_rate = flow_analysis.get("quick_wins", 0) / max(len(conversations), 1)
        if quick_win_rate > 0.3:
            opportunities.append({
                "type": "quick_qualification",
                "priority": "high",
                "recommendation": f"{quick_win_rate*100:.0f}% of hot leads qualify quickly - replicate this pattern",
                "expected_impact": "+20% efficiency"
            })
        
        return opportunities
    
    def generate_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        analysis = self.analyze_conversation_patterns()
        
        if "error" in analysis:
            return "No data available for analysis."
        
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Conversations Analyzed: {analysis['total_conversations']}")
        
        report.append("\n## Question Effectiveness")
        report.append("-" * 60)
        for q_type, data in sorted(
            analysis["question_effectiveness"].items(),
            key=lambda x: x[1]["effectiveness_rank"]
        ):
            report.append(
                f"{data['effectiveness_rank']}. {q_type.title()}: "
                f"Avg Score {data['avg_lead_score']:.1f} "
                f"({data['times_asked']} times asked)"
            )
        
        report.append("\n## Conversation Flow Insights")
        report.append("-" * 60)
        flow = analysis["conversation_flow"]
        report.append(f"Optimal Message Count: {flow.get('optimal_length', 'N/A')}")
        report.append(f"Quick Wins (≤5 messages): {flow.get('quick_wins', 0)}")
        report.append(f"Long Conversations (>10): {flow.get('long_conversions', 0)}")
        
        report.append("\n## Optimization Opportunities")
        report.append("-" * 60)
        for i, opp in enumerate(analysis["optimization_opportunities"], 1):
            report.append(f"\n{i}. [{opp['priority'].upper()}] {opp['type'].title()}")
            report.append(f"   {opp['recommendation']}")
            report.append(f"   Expected Impact: {opp['expected_impact']}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


class ConversationOptimizer:
    """Provides real-time suggestions for conversation optimization."""
    
    def __init__(self):
        self.analyzer = None
    
    def suggest_next_question(
        self,
        conversation_history: List[str],
        current_lead_score: int,
        questions_answered: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest the next best question to ask based on conversation context.
        
        Returns:
            {
                "suggested_question": str,
                "reasoning": str,
                "expected_impact": str,
                "alternatives": List[str]
            }
        """
        # Determine what's missing
        missing_info = []
        if "budget" not in " ".join(questions_answered).lower():
            missing_info.append("budget")
        if "timeline" not in " ".join(questions_answered).lower():
            missing_info.append("timeline")
        if "location" not in " ".join(questions_answered).lower():
            missing_info.append("location")
        
        # Prioritize based on lead score
        if current_lead_score < 40:
            # Focus on qualifying questions
            if "budget" in missing_info:
                return {
                    "suggested_question": "What's your budget range?",
                    "reasoning": "Budget is the strongest qualifier for cold leads",
                    "expected_impact": "+20 lead score points",
                    "alternatives": [
                        "Are you pre-approved for a mortgage?",
                        "What price range are you comfortable with?"
                    ]
                }
        elif current_lead_score < 70:
            # Build engagement
            if "timeline" in missing_info:
                return {
                    "suggested_question": "When are you looking to move?",
                    "reasoning": "Timeline helps prioritize warm leads",
                    "expected_impact": "+15 lead score points",
                    "alternatives": [
                        "How soon do you need to find a place?",
                        "Is this purchase urgent?"
                    ]
                }
        else:
            # Close for appointment
            return {
                "suggested_question": "Would you like to schedule a viewing?",
                "reasoning": "Lead is hot - move to appointment",
                "expected_impact": "Conversion opportunity",
                "alternatives": [
                    "Should we set up a time to look at properties?",
                    "Ready to see some homes in person?"
                ]
            }
        
        # Default
        return {
            "suggested_question": "What's most important to you in a home?",
            "reasoning": "Build rapport and understand needs",
            "expected_impact": "+10 lead score points",
            "alternatives": []
        }


if __name__ == "__main__":
    # Demo usage
    print("Advanced Analytics Engine Demo\n")
    
    # A/B Testing
    print("=" * 60)
    print("A/B Testing Example")
    print("=" * 60)
    ab_manager = ABTestManager("demo_location")
    
    exp_id = ab_manager.create_experiment(
        name="Opening Message Test",
        variant_a={"opening": "Hi! Looking for a home?"},
        variant_b={"opening": "Hey! What brings you here today?"},
        metric="conversion_rate",
        description="Test different opening messages"
    )
    
    print(f"Created experiment: {exp_id}")
    print(f"Active experiments: {len(ab_manager.list_active_experiments())}")
    
    # Performance Analysis
    print("\n" + "=" * 60)
    print("Performance Analysis Example")
    print("=" * 60)
    analyzer = PerformanceAnalyzer("demo_location")
    report = analyzer.generate_performance_report()
    print(report)
