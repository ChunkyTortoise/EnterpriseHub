#!/usr/bin/env python3
"""
Skill Metrics Tracking System
Tracks tool usage, skill effectiveness, and generates analytics

Version: 1.0.0
Last Updated: 2026-01-16

Usage:
    python update-skill-metrics.py --tool=Write --success=true --duration=450
    python update-skill-metrics.py --report
    python update-skill-metrics.py --export=csv
"""

import json
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import sys

# Configuration
METRICS_DIR = Path(__file__).parent.parent / "metrics"
TOOL_USAGE_LOG = METRICS_DIR / "tool-usage.log"
SKILL_USAGE_JSON = METRICS_DIR / "skill-usage.json"
RATE_LIMITS_JSON = METRICS_DIR / "rate-limits.json"
HOOK_PERFORMANCE_LOG = METRICS_DIR / "hook-performance.jsonl"


class MetricsTracker:
    """Track and analyze tool and skill usage metrics"""

    def __init__(self):
        self.metrics_dir = METRICS_DIR
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def log_tool_usage(self, tool_name: str, success: bool, duration_ms: int) -> None:
        """
        Log tool usage to metrics file

        Args:
            tool_name: Name of the tool (Read, Write, Edit, Bash, etc.)
            success: Whether the operation succeeded
            duration_ms: Execution time in milliseconds
        """
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "hour": datetime.utcnow().hour
        }

        # Append to JSONL log
        with open(TOOL_USAGE_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Update aggregated skill metrics
        self._update_skill_metrics(tool_name, success, duration_ms)

    def _update_skill_metrics(self, tool_name: str, success: bool, duration_ms: int) -> None:
        """Update aggregated skill usage statistics"""

        # Load existing metrics
        if SKILL_USAGE_JSON.exists():
            with open(SKILL_USAGE_JSON, "r") as f:
                metrics = json.load(f)
        else:
            metrics = {
                "last_updated": datetime.utcnow().isoformat(),
                "tools": {},
                "daily_summary": {},
                "skill_effectiveness": {}
            }

        # Initialize tool metrics if new
        if tool_name not in metrics["tools"]:
            metrics["tools"][tool_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "first_used": datetime.utcnow().isoformat(),
                "last_used": datetime.utcnow().isoformat()
            }

        # Update tool metrics
        tool_metrics = metrics["tools"][tool_name]
        tool_metrics["total_calls"] += 1
        tool_metrics["total_duration_ms"] += duration_ms
        tool_metrics["avg_duration_ms"] = (
            tool_metrics["total_duration_ms"] / tool_metrics["total_calls"]
        )
        tool_metrics["last_used"] = datetime.utcnow().isoformat()

        if success:
            tool_metrics["successful_calls"] += 1
        else:
            tool_metrics["failed_calls"] += 1

        # Update daily summary
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today not in metrics["daily_summary"]:
            metrics["daily_summary"][today] = {
                "total_operations": 0,
                "successful_operations": 0,
                "tools_used": set()
            }

        daily = metrics["daily_summary"][today]
        daily["total_operations"] += 1
        if success:
            daily["successful_operations"] += 1

        # Convert set to list for JSON serialization
        if isinstance(daily["tools_used"], set):
            daily["tools_used"] = list(daily["tools_used"])
        if tool_name not in daily["tools_used"]:
            daily["tools_used"].append(tool_name)

        # Calculate skill effectiveness (success rate)
        metrics["skill_effectiveness"] = self._calculate_skill_effectiveness(metrics)

        # Update timestamp
        metrics["last_updated"] = datetime.utcnow().isoformat()

        # Save updated metrics
        with open(SKILL_USAGE_JSON, "w") as f:
            json.dump(metrics, f, indent=2)

    def _calculate_skill_effectiveness(self, metrics: Dict) -> Dict:
        """Calculate effectiveness metrics for each tool/skill"""
        effectiveness = {}

        for tool_name, tool_data in metrics["tools"].items():
            total = tool_data["total_calls"]
            successful = tool_data["successful_calls"]

            effectiveness[tool_name] = {
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "avg_duration_ms": tool_data["avg_duration_ms"],
                "reliability": "high" if (successful / total) > 0.95 else "medium" if (successful / total) > 0.8 else "low",
                "performance": "fast" if tool_data["avg_duration_ms"] < 500 else "medium" if tool_data["avg_duration_ms"] < 2000 else "slow"
            }

        return effectiveness

    def check_rate_limit(self, operation: str, limit: int, window_seconds: int) -> Dict:
        """
        Check if operation is within rate limit

        Args:
            operation: Operation name (e.g., "subagent_creation")
            limit: Maximum operations allowed
            window_seconds: Time window in seconds

        Returns:
            Dict with allowed, current_count, limit, reset_time
        """
        # Load rate limits
        if RATE_LIMITS_JSON.exists():
            with open(RATE_LIMITS_JSON, "r") as f:
                rate_limits = json.load(f)
        else:
            rate_limits = {}

        now = time.time()

        # Initialize operation tracking
        if operation not in rate_limits:
            rate_limits[operation] = {
                "window_start": now,
                "count": 0,
                "limit": limit,
                "window_seconds": window_seconds
            }

        op_data = rate_limits[operation]

        # Reset window if expired
        if now - op_data["window_start"] > window_seconds:
            op_data["window_start"] = now
            op_data["count"] = 0

        # Check limit
        allowed = op_data["count"] < limit

        if allowed:
            op_data["count"] += 1

        # Calculate reset time
        reset_time = op_data["window_start"] + window_seconds

        # Save updated rate limits
        with open(RATE_LIMITS_JSON, "w") as f:
            json.dump(rate_limits, f, indent=2)

        return {
            "allowed": allowed,
            "current_count": op_data["count"],
            "limit": limit,
            "reset_time": datetime.fromtimestamp(reset_time).isoformat(),
            "seconds_until_reset": max(0, int(reset_time - now))
        }

    def generate_report(self, days: int = 7) -> str:
        """
        Generate comprehensive metrics report

        Args:
            days: Number of days to include in report

        Returns:
            Formatted report string
        """
        if not SKILL_USAGE_JSON.exists():
            return "No metrics data available. Start using tools to generate metrics."

        with open(SKILL_USAGE_JSON, "r") as f:
            metrics = json.load(f)

        report_lines = [
            "=" * 80,
            "ENTERPRISEHUB METRICS REPORT",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Period: Last {days} days",
            "=" * 80,
            "",
            "TOOL USAGE SUMMARY",
            "-" * 80,
        ]

        # Tool usage table
        for tool_name, tool_data in sorted(metrics["tools"].items(),
                                          key=lambda x: x[1]["total_calls"],
                                          reverse=True):
            success_rate = (tool_data["successful_calls"] / tool_data["total_calls"] * 100) if tool_data["total_calls"] > 0 else 0

            report_lines.append(
                f"{tool_name:20s} | "
                f"Calls: {tool_data['total_calls']:5d} | "
                f"Success: {success_rate:5.1f}% | "
                f"Avg Time: {tool_data['avg_duration_ms']:6.0f}ms"
            )

        # Skill effectiveness
        report_lines.extend([
            "",
            "SKILL EFFECTIVENESS",
            "-" * 80,
        ])

        for tool_name, effectiveness in sorted(metrics["skill_effectiveness"].items(),
                                              key=lambda x: x[1]["success_rate"],
                                              reverse=True):
            report_lines.append(
                f"{tool_name:20s} | "
                f"Success: {effectiveness['success_rate']:5.1f}% | "
                f"Reliability: {effectiveness['reliability']:8s} | "
                f"Performance: {effectiveness['performance']:8s}"
            )

        # Daily summary (last 7 days)
        report_lines.extend([
            "",
            "DAILY ACTIVITY (Last 7 Days)",
            "-" * 80,
        ])

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        daily_data = []

        for date_str, daily_summary in metrics["daily_summary"].items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if date_obj >= cutoff_date:
                success_rate = (daily_summary["successful_operations"] / daily_summary["total_operations"] * 100) if daily_summary["total_operations"] > 0 else 0
                daily_data.append((date_str, daily_summary, success_rate))

        for date_str, daily_summary, success_rate in sorted(daily_data, reverse=True):
            tools_count = len(daily_summary["tools_used"])
            report_lines.append(
                f"{date_str} | "
                f"Operations: {daily_summary['total_operations']:4d} | "
                f"Success: {success_rate:5.1f}% | "
                f"Tools Used: {tools_count}"
            )

        # Performance insights
        report_lines.extend([
            "",
            "PERFORMANCE INSIGHTS",
            "-" * 80,
        ])

        # Find slowest tools
        slow_tools = [(name, data["avg_duration_ms"])
                     for name, data in metrics["tools"].items()]
        slow_tools.sort(key=lambda x: x[1], reverse=True)

        report_lines.append("Slowest Tools (Optimization Opportunities):")
        for tool_name, avg_duration in slow_tools[:5]:
            report_lines.append(f"  - {tool_name}: {avg_duration:.0f}ms avg")

        # Find most reliable tools
        reliable_tools = [(name, eff["success_rate"])
                         for name, eff in metrics["skill_effectiveness"].items()]
        reliable_tools.sort(key=lambda x: x[1], reverse=True)

        report_lines.append("")
        report_lines.append("Most Reliable Tools:")
        for tool_name, success_rate in reliable_tools[:5]:
            report_lines.append(f"  - {tool_name}: {success_rate:.1f}% success rate")

        report_lines.extend([
            "",
            "=" * 80,
        ])

        return "\n".join(report_lines)

    def export_csv(self, output_file: str = "metrics-export.csv") -> None:
        """Export metrics to CSV format"""
        import csv

        if not SKILL_USAGE_JSON.exists():
            print("No metrics data to export.")
            return

        with open(SKILL_USAGE_JSON, "r") as f:
            metrics = json.load(f)

        output_path = Path(output_file)

        with open(output_path, "w", newline="") as csvfile:
            fieldnames = [
                "tool", "total_calls", "successful_calls", "failed_calls",
                "success_rate", "avg_duration_ms", "reliability", "performance",
                "first_used", "last_used"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for tool_name, tool_data in metrics["tools"].items():
                success_rate = (tool_data["successful_calls"] / tool_data["total_calls"] * 100) if tool_data["total_calls"] > 0 else 0
                effectiveness = metrics["skill_effectiveness"].get(tool_name, {})

                writer.writerow({
                    "tool": tool_name,
                    "total_calls": tool_data["total_calls"],
                    "successful_calls": tool_data["successful_calls"],
                    "failed_calls": tool_data["failed_calls"],
                    "success_rate": f"{success_rate:.2f}",
                    "avg_duration_ms": f"{tool_data['avg_duration_ms']:.2f}",
                    "reliability": effectiveness.get("reliability", "unknown"),
                    "performance": effectiveness.get("performance", "unknown"),
                    "first_used": tool_data["first_used"],
                    "last_used": tool_data["last_used"]
                })

        print(f"Metrics exported to {output_path}")


def main():
    """CLI interface for metrics tracking"""
    parser = argparse.ArgumentParser(
        description="Track and analyze skill/tool usage metrics"
    )
    # Automated metrics collection mode (from PostToolUse hooks)
    parser.add_argument("--auto", action="store_true",
                       help="Enable automated metrics collection mode (from hooks)")
    
    # Tool tracking arguments
    parser.add_argument("--tool", help="Tool name (Read, Write, Edit, Bash, Skill, etc.)")
    parser.add_argument("--success", type=lambda x: x.lower() == "true",
                       help="Whether operation succeeded (true/false)")
    parser.add_argument("--duration", type=int, help="Duration in milliseconds")
    
    # Enhanced metrics arguments (from PostToolUse hooks)
    parser.add_argument("--timestamp", help="ISO timestamp of operation")
    parser.add_argument("--operation", help="Description of what the tool did")
    parser.add_argument("--context-tokens", type=int, help="Tokens used from context")
    parser.add_argument("--result-tokens", type=int, help="Result tokens if applicable")
    parser.add_argument("--skill-tag", help="Skill that invoked the tool")
    
    # Skill-specific tracking
    parser.add_argument("--skill-name", help="Name of skill being tracked")
    parser.add_argument("--skill-outcome", help="Outcome of skill invocation")
    parser.add_argument("--tokens-saved", type=int, help="Tokens saved by skill")
    
    # Report and export arguments
    parser.add_argument("--report", action="store_true",
                       help="Generate metrics report")
    parser.add_argument("--days", type=int, default=7,
                       help="Number of days for report (default: 7)")
    parser.add_argument("--export", help="Export to CSV file")
    parser.add_argument("--check-rate-limit", help="Check rate limit for operation")
    parser.add_argument("--limit", type=int, default=10,
                       help="Rate limit count (default: 10)")
    parser.add_argument("--window", type=int, default=300,
                       help="Rate limit window in seconds (default: 300)")

    args = parser.parse_args()
    tracker = MetricsTracker()

    # AUTOMATED MODE: Log tool usage with enhanced metrics (from PostToolUse hooks)
    if args.auto and args.tool and args.success is not None and args.duration is not None:
        tracker.log_tool_usage_auto(
            tool_name=args.tool,
            success=args.success,
            duration_ms=args.duration,
            timestamp=args.timestamp,
            operation=args.operation,
            context_tokens=args.context_tokens,
            result_tokens=args.result_tokens,
            skill_tag=args.skill_tag,
            skill_name=args.skill_name,
            skill_outcome=args.skill_outcome,
            tokens_saved=args.tokens_saved
        )
        # Silent in auto mode - no output to user
        return
    
    # MANUAL MODE: Log tool usage (backward compatible)
    elif args.tool and args.success is not None and args.duration is not None:
        tracker.log_tool_usage(args.tool, args.success, args.duration)
        print(f"✅ Logged: {args.tool} - {'Success' if args.success else 'Failed'} - {args.duration}ms")

    # Generate report
    elif args.report:
        report = tracker.generate_report(days=args.days)
        print(report)

    # Export to CSV
    elif args.export:
        tracker.export_csv(args.export)

    # Check rate limit
    elif args.check_rate_limit:
        result = tracker.check_rate_limit(args.check_rate_limit, args.limit, args.window)
        if result["allowed"]:
            print(f"✅ Rate limit OK: {result['current_count']}/{result['limit']}")
            print(f"   Resets in {result['seconds_until_reset']} seconds")
        else:
            print(f"🛑 Rate limit exceeded: {result['current_count']}/{result['limit']}")
            print(f"   Resets at {result['reset_time']}")
            print(f"   Wait {result['seconds_until_reset']} seconds")
        sys.exit(0 if result["allowed"] else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
