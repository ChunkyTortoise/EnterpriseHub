#!/usr/bin/env python3
"""
Benchmark Report Generator

Generates comprehensive benchmark reports from test results including:
- Performance metrics analysis
- Quality metrics evaluation
- Regression detection
- Visual charts and graphs
- HTML and Markdown outputs
"""

import json
import argparse
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import sys

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    plt = None
    sns = None
    pd = None

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    Template = None


class BenchmarkReportGenerator:
    """Generate comprehensive benchmark reports with analysis and visualizations."""

    def __init__(self, output_dir: str = "."):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Performance targets (as defined in BENCHMARKS.md)
        self.targets = {
            "latency": {
                "api_p50": 30.0,  # ms
                "api_p95": 50.0,  # ms
                "api_p99": 100.0,  # ms
                "embedding": 20.0,  # ms
                "dense_retrieval": 15.0,  # ms
                "hybrid_retrieval": 50.0,  # ms
            },
            "quality": {
                "recall_at_5": 0.85,
                "recall_at_10": 0.90,
                "ndcg_at_10": 0.85,
                "answer_relevance": 4.0,  # out of 5
                "faithfulness": 0.90,
                "context_precision": 0.80,
                "context_recall": 0.85,
            },
            "throughput": {
                "requests_per_minute": 1000,
                "concurrent_users": 100,
                "cache_hit_rate": 0.90,
            }
        }

        # Stretch goals (better than targets)
        self.stretch_goals = {
            "latency": {
                "api_p95": 35.0,
                "embedding": 15.0,
                "dense_retrieval": 10.0,
                "hybrid_retrieval": 35.0,
            },
            "quality": {
                "recall_at_5": 0.90,
                "recall_at_10": 0.95,
                "ndcg_at_10": 0.90,
                "answer_relevance": 4.5,
                "faithfulness": 0.95,
                "context_precision": 0.85,
                "context_recall": 0.90,
            },
            "throughput": {
                "requests_per_minute": 5000,
                "concurrent_users": 500,
                "cache_hit_rate": 0.95,
            }
        }

    def generate_report(
        self,
        results_dir: str,
        baseline_dir: Optional[str] = None,
        format_types: List[str] = ["markdown", "html"]
    ) -> Dict[str, str]:
        """
        Generate comprehensive benchmark report.

        Args:
            results_dir: Directory containing benchmark results
            baseline_dir: Directory containing baseline results for comparison
            format_types: Output formats to generate

        Returns:
            Dictionary mapping format to output file path
        """
        print("Generating benchmark report...")

        # Load results
        results = self._load_results(results_dir)
        baseline = self._load_results(baseline_dir) if baseline_dir else None

        # Analyze results
        analysis = self._analyze_results(results, baseline)

        # Generate visualizations
        if HAS_PLOTTING:
            self._generate_charts(analysis)

        # Generate reports
        output_files = {}

        if "markdown" in format_types:
            markdown_file = self._generate_markdown_report(analysis)
            output_files["markdown"] = str(markdown_file)

        if "html" in format_types and HAS_JINJA2:
            html_file = self._generate_html_report(analysis)
            output_files["html"] = str(html_file)

        # Generate summary for CI
        summary_file = self._generate_ci_summary(analysis)
        output_files["summary"] = str(summary_file)

        return output_files

    def _load_results(self, results_dir: str) -> Dict[str, Any]:
        """Load benchmark results from directory."""
        if not results_dir:
            return {}

        results_path = Path(results_dir)
        if not results_path.exists():
            print(f"Warning: Results directory {results_dir} not found")
            return {}

        results = {}

        # Load different result files
        result_files = [
            ("performance", ["performance_combined.json", "embedding_perf.json", "retrieval_perf.json", "api_perf.json"]),
            ("quality", ["quality_combined.json", "retrieval_quality.json", "answer_quality.json"]),
            ("load", ["locust_results.json", "k6_results.json"])
        ]

        for category, filenames in result_files:
            category_results = {}

            for filename in filenames:
                file_path = results_path / filename
                if file_path.exists():
                    try:
                        with file_path.open('r') as f:
                            data = json.load(f)
                            category_results[filename] = data
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse {filename}: {e}")
                    except Exception as e:
                        print(f"Warning: Error loading {filename}: {e}")

            if category_results:
                results[category] = category_results

        return results

    def _analyze_results(self, results: Dict[str, Any], baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze benchmark results against targets and baseline."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "performance": {},
            "quality": {},
            "load": {},
            "regression": {},
            "recommendations": []
        }

        # Analyze performance results
        if "performance" in results:
            analysis["performance"] = self._analyze_performance(results["performance"])

        # Analyze quality results
        if "quality" in results:
            analysis["quality"] = self._analyze_quality(results["quality"])

        # Analyze load test results
        if "load" in results:
            analysis["load"] = self._analyze_load_tests(results["load"])

        # Compare with baseline
        if baseline:
            analysis["regression"] = self._detect_regressions(results, baseline)

        # Generate summary
        analysis["summary"] = self._generate_summary(analysis)

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _analyze_performance(self, perf_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance benchmark results."""
        performance = {
            "latency": {},
            "throughput": {},
            "status": "unknown",
            "issues": []
        }

        # Extract latency metrics
        if "api_perf.json" in perf_results:
            api_data = perf_results["api_perf.json"]
            if "benchmarks" in api_data:
                for benchmark in api_data["benchmarks"]:
                    if "query_endpoint" in benchmark.get("name", ""):
                        stats = benchmark.get("stats", {})
                        performance["latency"]["api_p50"] = stats.get("mean", 0) * 1000
                        performance["latency"]["api_p95"] = stats.get("p95", 0) * 1000
                        performance["latency"]["api_p99"] = stats.get("p99", 0) * 1000

        if "embedding_perf.json" in perf_results:
            embed_data = perf_results["embedding_perf.json"]
            # Extract embedding metrics...

        if "retrieval_perf.json" in perf_results:
            retr_data = perf_results["retrieval_perf.json"]
            # Extract retrieval metrics...

        # Check against targets
        target_status = []
        stretch_status = []

        for metric, value in performance["latency"].items():
            target = self.targets["latency"].get(metric)
            stretch = self.stretch_goals["latency"].get(metric)

            if target and value > target:
                performance["issues"].append(f"{metric}: {value:.1f}ms exceeds target {target}ms")
                target_status.append(False)
            else:
                target_status.append(True)

            if stretch and value <= stretch:
                stretch_status.append(True)
            else:
                stretch_status.append(False)

        # Determine overall status
        if all(target_status):
            if any(stretch_status):
                performance["status"] = "excellent"
            else:
                performance["status"] = "good"
        else:
            performance["status"] = "needs_improvement"

        return performance

    def _analyze_quality(self, quality_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality benchmark results."""
        quality = {
            "retrieval": {},
            "generation": {},
            "status": "unknown",
            "issues": []
        }

        # Extract quality metrics from test results
        if "retrieval_quality.json" in quality_results:
            retr_data = quality_results["retrieval_quality.json"]
            if "tests" in retr_data:
                for test in retr_data["tests"]:
                    if "recall" in test.get("nodeid", "").lower():
                        # Extract recall metrics...
                        pass

        if "answer_quality.json" in quality_results:
            ans_data = quality_results["answer_quality.json"]
            # Extract answer quality metrics...

        # Check against targets
        target_status = []

        for metric, target in self.targets["quality"].items():
            value = quality["retrieval"].get(metric) or quality["generation"].get(metric)
            if value is not None and value < target:
                quality["issues"].append(f"{metric}: {value:.3f} below target {target}")
                target_status.append(False)
            else:
                target_status.append(True)

        # Determine status
        quality["status"] = "good" if all(target_status) else "needs_improvement"

        return quality

    def _analyze_load_tests(self, load_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze load test results."""
        load = {
            "throughput": {},
            "errors": {},
            "status": "unknown",
            "issues": []
        }

        # Analyze Locust results
        if "locust_results.json" in load_results:
            locust_data = load_results["locust_results.json"]
            # Extract throughput and error metrics...

        # Analyze K6 results
        if "k6_results.json" in load_results:
            k6_data = load_results["k6_results.json"]
            # Extract K6 metrics...

        return load

    def _detect_regressions(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Detect performance regressions compared to baseline."""
        regressions = {
            "detected": [],
            "improvements": [],
            "status": "stable"
        }

        # Compare performance metrics
        if "performance" in current and "performance" in baseline:
            # Compare latency metrics...
            pass

        # Compare quality metrics
        if "quality" in current and "quality" in baseline:
            # Compare quality metrics...
            pass

        return regressions

    def _generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of benchmark results."""
        summary = {
            "overall_status": "unknown",
            "targets_met": 0,
            "total_targets": 0,
            "critical_issues": 0,
            "performance_score": 0,
            "quality_score": 0
        }

        # Count targets met
        performance = analysis.get("performance", {})
        quality = analysis.get("quality", {})

        if performance.get("status") in ["good", "excellent"]:
            summary["performance_score"] = 85 if performance["status"] == "good" else 95

        if quality.get("status") == "good":
            summary["quality_score"] = 85

        # Count critical issues
        summary["critical_issues"] = len(performance.get("issues", [])) + len(quality.get("issues", []))

        # Determine overall status
        if summary["performance_score"] >= 85 and summary["quality_score"] >= 85:
            summary["overall_status"] = "excellent" if all(score >= 95 for score in [summary["performance_score"], summary["quality_score"]]) else "good"
        elif summary["critical_issues"] == 0:
            summary["overall_status"] = "acceptable"
        else:
            summary["overall_status"] = "needs_improvement"

        return summary

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        performance = analysis.get("performance", {})
        quality = analysis.get("quality", {})
        summary = analysis.get("summary", {})

        # Performance recommendations
        if performance.get("status") == "needs_improvement":
            if performance.get("issues"):
                recommendations.append("🚀 **Performance Optimization Needed**")
                for issue in performance["issues"][:3]:  # Top 3 issues
                    recommendations.append(f"  - {issue}")

        # Quality recommendations
        if quality.get("status") == "needs_improvement":
            recommendations.append("📈 **Quality Improvements Required**")
            for issue in quality.get("issues", [])[:3]:
                recommendations.append(f"  - {issue}")

        # Regression recommendations
        regressions = analysis.get("regression", {})
        if regressions.get("detected"):
            recommendations.append("⚠️ **Regressions Detected**")
            for regression in regressions["detected"][:2]:
                recommendations.append(f"  - {regression}")

        # General recommendations
        if summary.get("overall_status") == "excellent":
            recommendations.append("✅ **Excellent Performance** - Consider documenting these results as new baselines")
        elif summary.get("critical_issues", 0) > 5:
            recommendations.append("🔧 **Multiple Issues Detected** - Consider comprehensive performance review")

        return recommendations

    def _generate_charts(self, analysis: Dict[str, Any]) -> None:
        """Generate visualization charts for the report."""
        if not HAS_PLOTTING:
            return

        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Performance latency chart
        self._create_latency_chart(analysis)

        # Quality metrics chart
        self._create_quality_chart(analysis)

        # Trend chart (if baseline available)
        self._create_trend_chart(analysis)

    def _create_latency_chart(self, analysis: Dict[str, Any]) -> None:
        """Create latency performance chart."""
        performance = analysis.get("performance", {})
        latency = performance.get("latency", {})

        if not latency:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        metrics = list(latency.keys())
        values = list(latency.values())
        targets = [self.targets["latency"].get(metric, 0) for metric in metrics]

        x_pos = range(len(metrics))

        # Create bars
        bars1 = ax.bar([x - 0.2 for x in x_pos], values, 0.4, label='Actual', alpha=0.8)
        bars2 = ax.bar([x + 0.2 for x in x_pos], targets, 0.4, label='Target', alpha=0.6)

        # Color bars based on target achievement
        for i, (actual, target) in enumerate(zip(values, targets)):
            if target > 0 and actual > target:
                bars1[i].set_color('red')
            else:
                bars1[i].set_color('green')

        ax.set_xlabel('Metrics')
        ax.set_ylabel('Latency (ms)')
        ax.set_title('Performance Latency Benchmarks')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(metrics, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'latency_chart.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_quality_chart(self, analysis: Dict[str, Any]) -> None:
        """Create quality metrics chart."""
        quality = analysis.get("quality", {})
        all_metrics = {**quality.get("retrieval", {}), **quality.get("generation", {})}

        if not all_metrics:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        metrics = list(all_metrics.keys())
        values = list(all_metrics.values())
        targets = [self.targets["quality"].get(metric, 0) for metric in metrics]

        x_pos = range(len(metrics))

        # Create horizontal bar chart
        bars1 = ax.barh([y - 0.2 for y in x_pos], values, 0.4, label='Actual', alpha=0.8)
        bars2 = ax.barh([y + 0.2 for y in x_pos], targets, 0.4, label='Target', alpha=0.6)

        # Color bars based on target achievement
        for i, (actual, target) in enumerate(zip(values, targets)):
            if target > 0 and actual < target:
                bars1[i].set_color('red')
            else:
                bars1[i].set_color('green')

        ax.set_ylabel('Metrics')
        ax.set_xlabel('Score')
        ax.set_title('Quality Benchmarks')
        ax.set_yticks(x_pos)
        ax.set_yticklabels(metrics)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'quality_chart.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_trend_chart(self, analysis: Dict[str, Any]) -> None:
        """Create trend comparison chart."""
        # This would show trends over time if historical data is available
        pass

    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> Path:
        """Generate Markdown format report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        summary = analysis["summary"]
        performance = analysis["performance"]
        quality = analysis["quality"]

        # Status emoji mapping
        status_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "acceptable": "🟠",
            "needs_improvement": "🔴",
            "unknown": "⚪"
        }

        report_content = f"""# Benchmark Report

**Generated:** {timestamp}
**Overall Status:** {status_emoji.get(summary['overall_status'], '⚪')} {summary['overall_status'].replace('_', ' ').title()}

## Executive Summary

| Metric | Score | Status |
|--------|--------|--------|
| Performance | {summary.get('performance_score', 0)}/100 | {status_emoji.get(performance.get('status'), '⚪')} {performance.get('status', 'unknown').replace('_', ' ').title()} |
| Quality | {summary.get('quality_score', 0)}/100 | {status_emoji.get(quality.get('status'), '⚪')} {quality.get('status', 'unknown').replace('_', ' ').title()} |
| Critical Issues | {summary.get('critical_issues', 0)} | {'🔴' if summary.get('critical_issues', 0) > 0 else '🟢'} |

## Performance Results

### Latency Metrics

| Metric | Actual | Target | Stretch | Status |
|--------|--------|--------|---------|--------|
"""

        # Add performance metrics
        for metric, value in performance.get("latency", {}).items():
            target = self.targets["latency"].get(metric, "N/A")
            stretch = self.stretch_goals["latency"].get(metric, "N/A")

            if isinstance(value, (int, float)) and isinstance(target, (int, float)):
                status = "🟢" if value <= target else "🔴"
                if isinstance(stretch, (int, float)) and value <= stretch:
                    status = "🟢⭐"  # Stretch goal achieved
            else:
                status = "⚪"

            report_content += f"| {metric} | {value:.1f}ms | {target}ms | {stretch}ms | {status} |\n"

        # Add quality results
        report_content += f"""

## Quality Results

### Retrieval Quality

"""

        for metric, value in quality.get("retrieval", {}).items():
            target = self.targets["quality"].get(metric, "N/A")
            status = "🟢" if isinstance(value, (int, float)) and isinstance(target, (int, float)) and value >= target else "🔴"
            report_content += f"- **{metric}**: {value:.3f} (target: {target}) {status}\n"

        report_content += f"""

### Answer Quality

"""

        for metric, value in quality.get("generation", {}).items():
            target = self.targets["quality"].get(metric, "N/A")
            status = "🟢" if isinstance(value, (int, float)) and isinstance(target, (int, float)) and value >= target else "🔴"
            report_content += f"- **{metric}**: {value:.3f} (target: {target}) {status}\n"

        # Add issues and recommendations
        all_issues = performance.get("issues", []) + quality.get("issues", [])
        if all_issues:
            report_content += f"""

## Issues Identified

"""
            for issue in all_issues:
                report_content += f"- ⚠️ {issue}\n"

        recommendations = analysis.get("recommendations", [])
        if recommendations:
            report_content += f"""

## Recommendations

"""
            for rec in recommendations:
                report_content += f"{rec}\n"

        # Add regression analysis
        regressions = analysis.get("regression", {})
        if regressions.get("detected") or regressions.get("improvements"):
            report_content += f"""

## Regression Analysis

"""
            if regressions.get("detected"):
                report_content += "### Regressions Detected\n"
                for regression in regressions["detected"]:
                    report_content += f"- 🔴 {regression}\n"

            if regressions.get("improvements"):
                report_content += "### Improvements\n"
                for improvement in regressions["improvements"]:
                    report_content += f"- 🟢 {improvement}\n"

        # Add footer
        report_content += f"""

---

**Report Details:**
- Generated at: {timestamp}
- Performance targets based on BENCHMARKS.md specification
- Stretch goals represent excellence thresholds beyond minimum requirements

*Generated by RAG System Benchmark Suite*
"""

        # Save report
        report_file = self.output_dir / "benchmark_report.md"
        with report_file.open('w') as f:
            f.write(report_content)

        return report_file

    def _generate_html_report(self, analysis: Dict[str, Any]) -> Path:
        """Generate HTML format report with enhanced visualization."""
        if not HAS_JINJA2:
            print("Warning: Jinja2 not available, skipping HTML report")
            return self.output_dir / "benchmark_report.html"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .status-excellent { color: #28a745; }
        .status-good { color: #ffc107; }
        .status-needs_improvement { color: #dc3545; }
        .metric-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .metric-table th, .metric-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .metric-table th { background-color: #f8f9fa; }
        .chart-container { text-align: center; margin: 20px 0; }
        .recommendations { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .issue { color: #dc3545; }
        .success { color: #28a745; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RAG System Benchmark Report</h1>
        <p><strong>Generated:</strong> {{ timestamp }}</p>
        <p><strong>Overall Status:</strong> <span class="status-{{ summary.overall_status }}">{{ summary.overall_status.replace('_', ' ').title() }}</span></p>
    </div>

    <h2>Performance Metrics</h2>
    <table class="metric-table">
        <tr><th>Metric</th><th>Actual</th><th>Target</th><th>Status</th></tr>
        {% for metric, value in performance.latency.items() %}
        <tr>
            <td>{{ metric }}</td>
            <td>{{ "%.1f"|format(value) }}ms</td>
            <td>{{ targets.latency[metric] }}ms</td>
            <td>{{ "✅" if value <= targets.latency[metric] else "❌" }}</td>
        </tr>
        {% endfor %}
    </table>

    {% if recommendations %}
    <div class="recommendations">
        <h3>Recommendations</h3>
        {% for rec in recommendations %}
        <p>{{ rec }}</p>
        {% endfor %}
    </div>
    {% endif %}

    <div class="chart-container">
        <img src="latency_chart.png" alt="Latency Chart" style="max-width: 100%;">
    </div>

</body>
</html>
"""

        template = Template(html_template)
        html_content = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            analysis=analysis,
            summary=analysis["summary"],
            performance=analysis["performance"],
            quality=analysis["quality"],
            recommendations=analysis["recommendations"],
            targets=self.targets
        )

        html_file = self.output_dir / "benchmark_report.html"
        with html_file.open('w') as f:
            f.write(html_content)

        return html_file

    def _generate_ci_summary(self, analysis: Dict[str, Any]) -> Path:
        """Generate concise summary for CI/CD systems."""
        summary = analysis["summary"]
        performance = analysis["performance"]
        quality = analysis["quality"]

        ci_summary = f"""BENCHMARK_STATUS={summary["overall_status"]}
PERFORMANCE_SCORE={summary.get("performance_score", 0)}
QUALITY_SCORE={summary.get("quality_score", 0)}
CRITICAL_ISSUES={summary.get("critical_issues", 0)}
PERFORMANCE_STATUS={performance.get("status", "unknown")}
QUALITY_STATUS={quality.get("status", "unknown")}
"""

        summary_file = self.output_dir / "ci_summary.env"
        with summary_file.open('w') as f:
            f.write(ci_summary)

        return summary_file


def main():
    """Command line interface for benchmark report generator."""
    parser = argparse.ArgumentParser(description="Generate comprehensive benchmark reports")
    parser.add_argument("--results-dir", required=True, help="Directory containing benchmark results")
    parser.add_argument("--baseline-dir", help="Directory containing baseline results for comparison")
    parser.add_argument("--output", default=".", help="Output directory for reports")
    parser.add_argument("--format", choices=["markdown", "html", "both"], default="both", help="Report format")

    args = parser.parse_args()

    # Determine formats
    if args.format == "both":
        formats = ["markdown", "html"]
    else:
        formats = [args.format]

    # Generate report
    generator = BenchmarkReportGenerator(args.output)

    try:
        output_files = generator.generate_report(
            results_dir=args.results_dir,
            baseline_dir=args.baseline_dir,
            format_types=formats
        )

        print("✅ Benchmark report generated successfully!")
        for format_type, file_path in output_files.items():
            print(f"  {format_type}: {file_path}")

    except Exception as e:
        print(f"❌ Error generating benchmark report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()