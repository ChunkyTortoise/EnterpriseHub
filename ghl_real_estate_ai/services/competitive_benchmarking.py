"""
Competitive Benchmarking Service

Compare performance metrics against industry standards
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class BenchmarkingEngine:
    """Compare performance against industry benchmarks"""

    # Industry benchmarks based on real estate data
    INDUSTRY_BENCHMARKS = {
        "real_estate": {
            "response_time_minutes": {
                "top_10_percent": 1.0,
                "top_25_percent": 2.0,
                "average": 4.2,
                "below_average": 8.0,
            },
            "conversion_rate": {
                "top_10_percent": 25.0,
                "top_25_percent": 18.0,
                "average": 12.3,
                "below_average": 8.0,
            },
            "lead_score_avg": {
                "top_10_percent": 72,
                "top_25_percent": 60,
                "average": 52,
                "below_average": 40,
            },
            "reengagement_rate": {
                "top_10_percent": 20.0,
                "top_25_percent": 12.0,
                "average": 8.0,
                "below_average": 4.0,
            },
            "appointment_booking": {
                "top_10_percent": 25.0,
                "top_25_percent": 18.0,
                "average": 15.0,
                "below_average": 10.0,
            },
            "weekend_coverage": {
                "top_10_percent": 85.0,
                "top_25_percent": 65.0,
                "average": 45.0,
                "below_average": 20.0,
            },
        }
    }

    def __init__(self, data_dir: Path = None):
        """
        Execute init operation.

        Args:
            data_dir: Data to process
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"

    def generate_benchmark_report(
        self, location_id: str, metrics: Dict[str, float], industry: str = "real_estate"
    ) -> Dict[str, Any]:
        """
        Generate competitive benchmark report

        Args:
            location_id: GHL location ID
            metrics: Current performance metrics
            industry: Industry type for benchmarking

        Returns:
            Comprehensive benchmark comparison
        """
        benchmarks = self.INDUSTRY_BENCHMARKS.get(industry, {})

        if not benchmarks:
            return {"error": f"No benchmarks available for industry: {industry}"}

        # Compare each metric
        comparisons = {}
        overall_scores = []

        for metric_name, metric_value in metrics.items():
            if metric_name in benchmarks:
                comparison = self._compare_metric(metric_name, metric_value, benchmarks[metric_name])
                comparisons[metric_name] = comparison
                overall_scores.append(comparison["percentile_score"])

        # Calculate overall ranking
        avg_percentile = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        overall_ranking = self._calculate_ranking(avg_percentile)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(comparisons)
        opportunities = self._identify_opportunities(comparisons)

        # Generate recommendations
        recommendations = self._generate_benchmark_recommendations(comparisons, benchmarks)

        return {
            "location_id": location_id,
            "industry": industry,
            "overall_ranking": overall_ranking,
            "percentile": round(avg_percentile, 1),
            "comparisons": comparisons,
            "strengths": strengths,
            "opportunities": opportunities,
            "recommendations": recommendations,
            "competitive_position": self._describe_position(avg_percentile),
            "generated_at": datetime.now().isoformat(),
        }

    def _compare_metric(self, metric_name: str, your_value: float, benchmark_data: Dict[str, float]) -> Dict[str, Any]:
        """Compare a single metric against benchmarks"""

        # Determine if higher is better (varies by metric)
        higher_is_better = metric_name not in ["response_time_minutes"]

        # Calculate percentile
        if higher_is_better:
            if your_value >= benchmark_data["top_10_percent"]:
                percentile = 95
                tier = "top_10_percent"
            elif your_value >= benchmark_data["top_25_percent"]:
                percentile = 80
                tier = "top_25_percent"
            elif your_value >= benchmark_data["average"]:
                percentile = 50
                tier = "average"
            else:
                percentile = 25
                tier = "below_average"
        else:
            # Lower is better (e.g., response time)
            if your_value <= benchmark_data["top_10_percent"]:
                percentile = 95
                tier = "top_10_percent"
            elif your_value <= benchmark_data["top_25_percent"]:
                percentile = 80
                tier = "top_25_percent"
            elif your_value <= benchmark_data["average"]:
                percentile = 50
                tier = "average"
            else:
                percentile = 25
                tier = "below_average"

        # Calculate difference from average
        diff = your_value - benchmark_data["average"]
        if not higher_is_better:
            diff = -diff  # Invert for metrics where lower is better

        percent_diff = (diff / benchmark_data["average"] * 100) if benchmark_data["average"] != 0 else 0

        return {
            "metric": metric_name,
            "your_value": your_value,
            "industry_average": benchmark_data["average"],
            "difference": round(diff, 2),
            "percent_difference": round(percent_diff, 1),
            "percentile": percentile,
            "percentile_score": percentile,
            "tier": tier,
            "performance": self._rate_performance(percentile),
            "comparison_text": self._generate_comparison_text(
                metric_name, your_value, benchmark_data, tier, percent_diff
            ),
        }

    def _calculate_ranking(self, percentile: float) -> str:
        """Calculate overall ranking tier"""
        if percentile >= 90:
            return "Top 10%"
        elif percentile >= 75:
            return "Top 25%"
        elif percentile >= 50:
            return "Above Average"
        elif percentile >= 25:
            return "Average"
        else:
            return "Below Average"

    def _rate_performance(self, percentile: float) -> str:
        """Rate performance based on percentile"""
        if percentile >= 90:
            return "Excellent"
        elif percentile >= 75:
            return "Very Good"
        elif percentile >= 50:
            return "Good"
        elif percentile >= 25:
            return "Fair"
        else:
            return "Needs Improvement"

    def _generate_comparison_text(
        self,
        metric_name: str,
        your_value: float,
        benchmarks: Dict[str, float],
        tier: str,
        percent_diff: float,
    ) -> str:
        """Generate human-readable comparison text"""

        if tier == "top_10_percent":
            return f"Outstanding! You're in the top 10% ({abs(percent_diff):.0f}% better than average)"
        elif tier == "top_25_percent":
            return f"Excellent performance, top 25% ({abs(percent_diff):.0f}% better than average)"
        elif tier == "average":
            if percent_diff > 0:
                return f"Slightly above average (+{percent_diff:.0f}%)"
            else:
                return f"At industry average"
        else:
            return f"Below average by {abs(percent_diff):.0f}% - opportunity for improvement"

    def _identify_strengths(self, comparisons: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify top strengths"""
        strengths = []

        for metric_name, comparison in comparisons.items():
            if comparison["percentile"] >= 80:
                strengths.append(
                    {
                        "metric": metric_name.replace("_", " ").title(),
                        "performance": comparison["performance"],
                        "message": f"{comparison['comparison_text']}",
                    }
                )

        # Sort by percentile
        strengths.sort(
            key=lambda x: comparisons[x["metric"].lower().replace(" ", "_")]["percentile"],
            reverse=True,
        )

        return strengths

    def _identify_opportunities(self, comparisons: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify improvement opportunities"""
        opportunities = []

        for metric_name, comparison in comparisons.items():
            if comparison["percentile"] < 50:
                gap = comparison["industry_average"] - comparison["your_value"]
                opportunities.append(
                    {
                        "metric": metric_name.replace("_", " ").title(),
                        "current": comparison["your_value"],
                        "target": comparison["industry_average"],
                        "gap": abs(gap),
                        "message": f"Close the gap to reach industry average",
                    }
                )

        # Sort by gap size
        opportunities.sort(key=lambda x: x["gap"], reverse=True)

        return opportunities

    def _generate_benchmark_recommendations(
        self, comparisons: Dict[str, Any], benchmarks: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on benchmark comparison"""
        recommendations = []

        # Response time recommendation
        if "response_time_minutes" in comparisons:
            comp = comparisons["response_time_minutes"]
            if comp["percentile"] < 75:
                recommendations.append(
                    {
                        "category": "Response Time",
                        "priority": "high",
                        "current": f"{comp['your_value']:.1f} minutes",
                        "target": f"{benchmarks['response_time_minutes']['top_25_percent']:.1f} minutes",
                        "action": "Implement SMS alerts and auto-responders to reach top 25% (< 2 min)",
                    }
                )

        # Conversion rate recommendation
        if "conversion_rate" in comparisons:
            comp = comparisons["conversion_rate"]
            if comp["percentile"] < 75:
                recommendations.append(
                    {
                        "category": "Conversion",
                        "priority": "high",
                        "current": f"{comp['your_value']:.1f}%",
                        "target": f"{benchmarks['conversion_rate']['top_25_percent']:.1f}%",
                        "action": "Focus on lead qualification and follow-up to reach top 25% conversion",
                    }
                )

        # Weekend coverage recommendation
        if "weekend_coverage" in comparisons:
            comp = comparisons["weekend_coverage"]
            if comp["percentile"] < 50:
                recommendations.append(
                    {
                        "category": "Availability",
                        "priority": "medium",
                        "current": f"{comp['your_value']:.0f}%",
                        "target": f"{benchmarks['weekend_coverage']['average']:.0f}%",
                        "action": "Improve weekend coverage with automated responses or weekend staff",
                    }
                )

        return recommendations

    def _describe_position(self, percentile: float) -> str:
        """Describe competitive position"""
        if percentile >= 90:
            return "Industry Leader - You're outperforming 90% of competitors. Maintain excellence!"
        elif percentile >= 75:
            return "Strong Performer - You're in the top quartile. Keep pushing for #1!"
        elif percentile >= 50:
            return "Solid Performance - You're above average. Focus on key improvements to reach top tier."
        elif percentile >= 25:
            return "Room for Growth - You're at industry average. Implement recommendations to improve."
        else:
            return "Improvement Needed - Below average performance. Prioritize key initiatives."


class CompetitorAnalyzer:
    """Analyze competitor strategies and performance"""

    def analyze_competitive_landscape(self) -> Dict[str, Any]:
        """Analyze the competitive landscape"""

        return {
            "market_position": "Top 5%",
            "key_differentiators": [
                "24/7 AI-powered qualification",
                "Sub-2-minute response time",
                "Predictive lead scoring",
                "Automated re-engagement",
            ],
            "competitive_advantages": [
                "Technology-enabled efficiency",
                "Data-driven decision making",
                "Consistent quality at scale",
            ],
            "threats": ["Competitors adopting AI", "Market saturation in some areas"],
            "opportunities": [
                "Expand to additional markets",
                "White-label solution for other agents",
                "Advanced analytics upsell",
            ],
        }
