#!/usr/bin/env python3
"""
Benchmark Comparison Script

Compares current benchmark results against baseline to detect:
- Performance regressions
- Quality degradations
- Improvements
- Statistical significance of changes

Provides detailed analysis for continuous performance monitoring.
"""

import json
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys

try:
    import numpy as np
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    np = None
    stats = None


@dataclass
class ComparisonResult:
    """Results of comparing two benchmark values."""
    metric_name: str
    current_value: float
    baseline_value: float
    change_percent: float
    change_absolute: float
    is_regression: bool
    is_improvement: bool
    significance: str  # 'significant', 'minor', 'insignificant'
    confidence: float


class BenchmarkComparator:
    """Compare benchmark results against baselines for regression detection."""

    def __init__(self):
        """Initialize benchmark comparator with thresholds."""
        # Regression detection thresholds
        self.regression_thresholds = {
            # Performance metrics (higher = worse)
            "latency": {
                "significant": 0.15,  # 15% increase
                "minor": 0.05,        # 5% increase
                "absolute_min": 5.0   # 5ms minimum change
            },
            # Quality metrics (lower = worse)
            "quality": {
                "significant": -0.10,  # 10% decrease
                "minor": -0.03,        # 3% decrease
                "absolute_min": 0.01   # 0.01 minimum change
            },
            # Throughput metrics (lower = worse)
            "throughput": {
                "significant": -0.20,  # 20% decrease
                "minor": -0.05,        # 5% decrease
                "absolute_min": 50.0   # 50 req/min minimum change
            }
        }

        # Metric categorization
        self.metric_categories = {
            "latency": [
                "api_p50", "api_p95", "api_p99",
                "embedding", "dense_retrieval", "hybrid_retrieval",
                "query_latency", "latency", "response_time"
            ],
            "quality": [
                "recall_at_5", "recall_at_10", "ndcg_at_10",
                "answer_relevance", "faithfulness", "context_precision",
                "context_recall", "accuracy", "precision", "f1_score"
            ],
            "throughput": [
                "requests_per_minute", "requests_per_second", "throughput",
                "queries_per_second", "concurrent_users"
            ]
        }

    def compare_benchmarks(
        self,
        current_file: str,
        baseline_file: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare current benchmark results against baseline.

        Args:
            current_file: Path to current benchmark results
            baseline_file: Path to baseline benchmark results
            output_file: Optional path to save comparison results

        Returns:
            Dictionary containing comparison analysis
        """
        print(f"Comparing benchmarks:")
        print(f"  Current: {current_file}")
        print(f"  Baseline: {baseline_file}")

        # Load results
        current_results = self._load_benchmark_file(current_file)
        baseline_results = self._load_benchmark_file(baseline_file)

        if not current_results or not baseline_results:
            raise ValueError("Could not load benchmark results")

        # Perform comparison
        comparison = self._perform_comparison(current_results, baseline_results)

        # Save results if requested
        if output_file:
            self._save_comparison(comparison, output_file)

        return comparison

    def _load_benchmark_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load benchmark results from file."""
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}")
            return None

        try:
            with path.open('r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return None

    def _perform_comparison(
        self,
        current: Dict[str, Any],
        baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed comparison between current and baseline results."""
        comparison = {
            "metadata": {
                "comparison_timestamp": datetime.now().isoformat(),
                "current_metrics": self._count_metrics(current),
                "baseline_metrics": self._count_metrics(baseline),
            },
            "summary": {
                "total_comparisons": 0,
                "regressions": 0,
                "improvements": 0,
                "no_change": 0,
                "significant_changes": 0
            },
            "results": [],
            "regressions": [],
            "improvements": [],
            "analysis": {}
        }

        # Extract metrics for comparison
        current_metrics = self._extract_metrics(current)
        baseline_metrics = self._extract_metrics(baseline)

        # Find common metrics
        common_metrics = set(current_metrics.keys()) & set(baseline_metrics.keys())

        if not common_metrics:
            print("Warning: No common metrics found between current and baseline")
            return comparison

        print(f"Comparing {len(common_metrics)} common metrics...")

        # Compare each metric
        for metric_name in sorted(common_metrics):
            current_value = current_metrics[metric_name]
            baseline_value = baseline_metrics[metric_name]

            if not isinstance(current_value, (int, float)) or not isinstance(baseline_value, (int, float)):
                continue

            # Perform comparison
            result = self._compare_metric(metric_name, current_value, baseline_value)
            comparison["results"].append(result)

            # Update summary
            comparison["summary"]["total_comparisons"] += 1

            if result.is_regression:
                comparison["summary"]["regressions"] += 1
                comparison["regressions"].append(result)
            elif result.is_improvement:
                comparison["summary"]["improvements"] += 1
                comparison["improvements"].append(result)
            else:
                comparison["summary"]["no_change"] += 1

            if result.significance == "significant":
                comparison["summary"]["significant_changes"] += 1

        # Generate analysis
        comparison["analysis"] = self._generate_analysis(comparison)

        return comparison

    def _extract_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical metrics from benchmark results."""
        metrics = {}

        def extract_recursive(data: Dict[str, Any], prefix: str = ""):
            """Recursively extract metrics from nested dictionaries."""
            for key, value in data.items():
                full_key = f"{prefix}_{key}" if prefix else key

                if isinstance(value, dict):
                    extract_recursive(value, full_key)
                elif isinstance(value, (int, float)):
                    metrics[full_key] = float(value)
                elif isinstance(value, list) and value and isinstance(value[0], (int, float)):
                    # Handle lists of numbers (e.g., latency arrays)
                    metrics[f"{full_key}_mean"] = statistics.mean(value)
                    if len(value) > 1:
                        metrics[f"{full_key}_p95"] = np.percentile(value, 95) if HAS_SCIPY else max(value)
                        metrics[f"{full_key}_p99"] = np.percentile(value, 99) if HAS_SCIPY else max(value)

        extract_recursive(results)
        return metrics

    def _compare_metric(self, metric_name: str, current: float, baseline: float) -> ComparisonResult:
        """Compare a single metric against its baseline."""
        # Calculate changes
        absolute_change = current - baseline
        percent_change = (absolute_change / baseline * 100) if baseline != 0 else 0

        # Determine metric category
        category = self._get_metric_category(metric_name)

        # Determine if this is a regression or improvement
        is_regression = self._is_regression(percent_change, absolute_change, category)
        is_improvement = self._is_improvement(percent_change, absolute_change, category)

        # Determine significance
        significance, confidence = self._assess_significance(
            percent_change, absolute_change, category
        )

        return ComparisonResult(
            metric_name=metric_name,
            current_value=current,
            baseline_value=baseline,
            change_percent=percent_change,
            change_absolute=absolute_change,
            is_regression=is_regression,
            is_improvement=is_improvement,
            significance=significance,
            confidence=confidence
        )

    def _get_metric_category(self, metric_name: str) -> str:
        """Determine the category of a metric."""
        metric_lower = metric_name.lower()

        for category, keywords in self.metric_categories.items():
            if any(keyword in metric_lower for keyword in keywords):
                return category

        # Default classification based on common patterns
        if any(word in metric_lower for word in ["time", "latency", "duration", "ms"]):
            return "latency"
        elif any(word in metric_lower for word in ["rate", "accuracy", "precision", "recall", "score"]):
            return "quality"
        elif any(word in metric_lower for word in ["throughput", "rps", "qps", "concurrent"]):
            return "throughput"

        return "latency"  # Default to latency (conservative)

    def _is_regression(self, percent_change: float, absolute_change: float, category: str) -> bool:
        """Determine if a change represents a regression."""
        thresholds = self.regression_thresholds.get(category, self.regression_thresholds["latency"])

        if category == "latency":
            # For latency, increases are bad
            return (percent_change > abs(thresholds["minor"]) * 100 and
                    absolute_change > thresholds.get("absolute_min", 0))
        else:
            # For quality/throughput, decreases are bad
            return (percent_change < thresholds["minor"] * 100 and
                    abs(absolute_change) > thresholds.get("absolute_min", 0))

    def _is_improvement(self, percent_change: float, absolute_change: float, category: str) -> bool:
        """Determine if a change represents an improvement."""
        thresholds = self.regression_thresholds.get(category, self.regression_thresholds["latency"])

        if category == "latency":
            # For latency, decreases are good
            return (percent_change < -abs(thresholds["minor"]) * 100 and
                    abs(absolute_change) > thresholds.get("absolute_min", 0))
        else:
            # For quality/throughput, increases are good
            return (percent_change > abs(thresholds["minor"]) * 100 and
                    absolute_change > thresholds.get("absolute_min", 0))

    def _assess_significance(
        self,
        percent_change: float,
        absolute_change: float,
        category: str
    ) -> Tuple[str, float]:
        """Assess the significance of a change."""
        thresholds = self.regression_thresholds.get(category, self.regression_thresholds["latency"])

        abs_percent = abs(percent_change)
        abs_absolute = abs(absolute_change)

        # Check for significant change
        if (abs_percent > abs(thresholds["significant"]) * 100 and
                abs_absolute > thresholds.get("absolute_min", 0) * 2):
            return "significant", 0.95

        # Check for minor change
        elif (abs_percent > abs(thresholds["minor"]) * 100 and
              abs_absolute > thresholds.get("absolute_min", 0)):
            return "minor", 0.80

        # Insignificant change
        else:
            return "insignificant", 0.50

    def _generate_analysis(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level analysis of the comparison results."""
        summary = comparison["summary"]
        results = comparison["results"]

        analysis = {
            "overall_status": "stable",
            "critical_regressions": 0,
            "minor_regressions": 0,
            "significant_improvements": 0,
            "most_impacted_metrics": [],
            "recommendations": []
        }

        # Categorize regressions by significance
        for regression in comparison["regressions"]:
            if regression.significance == "significant":
                analysis["critical_regressions"] += 1
            else:
                analysis["minor_regressions"] += 1

        # Count significant improvements
        for improvement in comparison["improvements"]:
            if improvement.significance == "significant":
                analysis["significant_improvements"] += 1

        # Determine overall status
        if analysis["critical_regressions"] > 0:
            analysis["overall_status"] = "critical_regression"
        elif analysis["minor_regressions"] > analysis["significant_improvements"]:
            analysis["overall_status"] = "minor_regression"
        elif analysis["significant_improvements"] > 0:
            analysis["overall_status"] = "improved"
        else:
            analysis["overall_status"] = "stable"

        # Find most impacted metrics
        significant_changes = [r for r in results if r.significance == "significant"]
        analysis["most_impacted_metrics"] = sorted(
            significant_changes,
            key=lambda x: abs(x.change_percent),
            reverse=True
        )[:5]

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis, comparison)

        return analysis

    def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on comparison results."""
        recommendations = []

        if analysis["critical_regressions"] > 0:
            recommendations.append(
                f"🚨 **Critical Action Required**: {analysis['critical_regressions']} "
                "significant performance regressions detected"
            )

        if analysis["minor_regressions"] > 3:
            recommendations.append(
                "⚠️ **Multiple Minor Regressions**: Consider comprehensive performance review"
            )

        # Specific metric recommendations
        for metric in analysis["most_impacted_metrics"][:3]:
            if metric.is_regression:
                recommendations.append(
                    f"🔍 **Investigate {metric.metric_name}**: "
                    f"{metric.change_percent:+.1f}% change from baseline"
                )

        if analysis["significant_improvements"] > 0:
            recommendations.append(
                f"✅ **Performance Improvements**: {analysis['significant_improvements']} "
                "metrics showed significant improvement - consider updating baselines"
            )

        if analysis["overall_status"] == "stable":
            recommendations.append(
                "🟢 **Stable Performance**: No significant regressions detected"
            )

        return recommendations

    def _count_metrics(self, results: Dict[str, Any]) -> int:
        """Count the number of metrics in results."""
        count = 0

        def count_recursive(data):
            nonlocal count
            if isinstance(data, dict):
                for value in data.values():
                    count_recursive(value)
            elif isinstance(data, (int, float)):
                count += 1

        count_recursive(results)
        return count

    def _save_comparison(self, comparison: Dict[str, Any], output_file: str) -> None:
        """Save comparison results to file."""
        # Convert ComparisonResult objects to dictionaries for JSON serialization
        serializable_comparison = comparison.copy()

        def convert_results(results_list):
            return [
                {
                    "metric_name": r.metric_name,
                    "current_value": r.current_value,
                    "baseline_value": r.baseline_value,
                    "change_percent": r.change_percent,
                    "change_absolute": r.change_absolute,
                    "is_regression": r.is_regression,
                    "is_improvement": r.is_improvement,
                    "significance": r.significance,
                    "confidence": r.confidence
                }
                for r in results_list
            ]

        serializable_comparison["results"] = convert_results(comparison["results"])
        serializable_comparison["regressions"] = convert_results(comparison["regressions"])
        serializable_comparison["improvements"] = convert_results(comparison["improvements"])

        # Convert most_impacted_metrics in analysis
        if "most_impacted_metrics" in serializable_comparison["analysis"]:
            serializable_comparison["analysis"]["most_impacted_metrics"] = convert_results(
                serializable_comparison["analysis"]["most_impacted_metrics"]
            )

        output_path = Path(output_file)
        with output_path.open('w') as f:
            json.dump(serializable_comparison, f, indent=2)

        print(f"Comparison results saved to: {output_file}")

    def generate_text_report(self, comparison: Dict[str, Any]) -> str:
        """Generate a human-readable text report of the comparison."""
        analysis = comparison["analysis"]
        summary = comparison["summary"]

        # Status emoji mapping
        status_emoji = {
            "critical_regression": "🔴",
            "minor_regression": "🟡",
            "stable": "🟢",
            "improved": "⭐"
        }

        report = f"""
# Benchmark Comparison Report

**Status**: {status_emoji.get(analysis['overall_status'], '⚪')} {analysis['overall_status'].replace('_', ' ').title()}
**Generated**: {comparison['metadata']['comparison_timestamp']}

## Summary

- **Total Comparisons**: {summary['total_comparisons']}
- **Regressions**: {summary['regressions']} ({analysis['critical_regressions']} critical, {analysis['minor_regressions']} minor)
- **Improvements**: {summary['improvements']} ({analysis['significant_improvements']} significant)
- **No Change**: {summary['no_change']}

## Critical Issues
"""

        # Add critical regressions
        critical_regressions = [r for r in comparison["regressions"] if r.significance == "significant"]
        if critical_regressions:
            for reg in critical_regressions[:5]:  # Top 5
                report += f"- 🔴 **{reg.metric_name}**: {reg.change_percent:+.1f}% ({reg.current_value:.3f} vs {reg.baseline_value:.3f})\n"
        else:
            report += "- No critical regressions detected ✅\n"

        # Add improvements
        significant_improvements = [r for r in comparison["improvements"] if r.significance == "significant"]
        if significant_improvements:
            report += "\n## Significant Improvements\n"
            for imp in significant_improvements[:5]:
                report += f"- 🟢 **{imp.metric_name}**: {imp.change_percent:+.1f}% ({imp.current_value:.3f} vs {imp.baseline_value:.3f})\n"

        # Add recommendations
        if analysis["recommendations"]:
            report += "\n## Recommendations\n"
            for rec in analysis["recommendations"]:
                report += f"- {rec}\n"

        return report


def main():
    """Command line interface for benchmark comparison."""
    parser = argparse.ArgumentParser(description="Compare benchmark results against baseline")
    parser.add_argument("--current", required=True, help="Current benchmark results file")
    parser.add_argument("--baseline", required=True, help="Baseline benchmark results file")
    parser.add_argument("--output", help="Output file for comparison results (JSON)")
    parser.add_argument("--report", help="Output file for text report")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit with error code if regressions detected")

    args = parser.parse_args()

    # Perform comparison
    comparator = BenchmarkComparator()

    try:
        comparison = comparator.compare_benchmarks(
            current_file=args.current,
            baseline_file=args.baseline,
            output_file=args.output
        )

        # Generate text report
        if args.report:
            text_report = comparator.generate_text_report(comparison)
            with Path(args.report).open('w') as f:
                f.write(text_report)
            print(f"Text report saved to: {args.report}")

        # Print summary
        analysis = comparison["analysis"]
        print(f"\n✅ Comparison completed:")
        print(f"  Status: {analysis['overall_status']}")
        print(f"  Critical regressions: {analysis['critical_regressions']}")
        print(f"  Minor regressions: {analysis['minor_regressions']}")
        print(f"  Significant improvements: {analysis['significant_improvements']}")

        # Exit with error if regressions and fail-on-regression is set
        if args.fail_on_regression and analysis["critical_regressions"] > 0:
            print(f"\n❌ Failing due to {analysis['critical_regressions']} critical regressions")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during benchmark comparison: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()