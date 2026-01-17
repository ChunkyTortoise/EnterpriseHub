#!/usr/bin/env python3
"""
Claude Code Session Manager
============================

Monitors context usage and iteration count to prevent token exhaustion.
Provides proactive warnings and suggestions for optimization.

Token Budget: Zero-context execution (this script is not loaded)
Output only: ~200-400 tokens
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class SessionManager:
    """Manage Claude Code session health and token usage."""

    # Thresholds
    MAX_CONTEXT_TOKENS = 200_000
    WARNING_THRESHOLD = 0.75  # Warn at 75% usage (150k tokens)
    CRITICAL_THRESHOLD = 0.85  # Critical at 85% usage (170k tokens)
    MAX_ITERATIONS_WARNING = 20
    MAX_ITERATIONS_CRITICAL = 30

    def __init__(self):
        self.project_root = Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.session_file = self.claude_dir / "session_state.json"

    def estimate_current_usage(self) -> Dict[str, int]:
        """
        Estimate current token usage based on loaded context.

        Returns:
            Dictionary with token usage breakdown
        """
        usage = {
            "system_prompt": 15_000,  # Base Claude Code prompt
            "project_instructions": 0,  # CLAUDE.md
            "mcp_servers": 0,           # MCP server overhead
            "context_files": 0,         # Loaded files
            "conversation": 0,          # Conversation history
            "total": 0
        }

        # Estimate CLAUDE.md size
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.exists():
            # Rough estimate: 1 token ≈ 0.75 words ≈ 4 characters
            file_size = claude_md.stat().st_size
            usage["project_instructions"] = file_size // 4

        # Estimate MCP server overhead
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            # Count enabled MCP servers
            # Serena: ~4k, Context7: ~3k, Playwright: ~3k, Greptile: ~2k
            mcp_overhead = {
                "serena": 4_000,
                "context7": 3_000,
                "playwright": 3_000,
                "greptile": 2_000
            }

            allowed_tools = settings.get("permissions", {}).get("allowedTools", [])
            for tool in allowed_tools:
                if "serena" in tool:
                    usage["mcp_servers"] += mcp_overhead.get("serena", 0)
                    mcp_overhead.pop("serena", None)  # Count once
                elif "context7" in tool:
                    usage["mcp_servers"] += mcp_overhead.get("context7", 0)
                    mcp_overhead.pop("context7", None)
                elif "playwright" in tool:
                    usage["mcp_servers"] += mcp_overhead.get("playwright", 0)
                    mcp_overhead.pop("playwright", None)
                elif "greptile" in tool:
                    usage["mcp_servers"] += mcp_overhead.get("greptile", 0)
                    mcp_overhead.pop("greptile", None)

        usage["total"] = sum(usage.values())
        return usage

    def get_iteration_count(self) -> int:
        """Get current iteration count from session state."""
        if not self.session_file.exists():
            return 0

        try:
            with open(self.session_file, 'r') as f:
                state = json.load(f)
            return state.get("iteration_count", 0)
        except (json.JSONDecodeError, FileNotFoundError):
            return 0

    def update_iteration_count(self, count: int):
        """Update iteration count in session state."""
        state = {}
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    state = json.load(f)
            except json.JSONDecodeError:
                pass

        state["iteration_count"] = count
        state["last_updated"] = datetime.utcnow().isoformat()

        self.claude_dir.mkdir(exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(state, f, indent=2)

    def check_session_health(self) -> Dict:
        """
        Comprehensive session health check.

        Returns:
            Dictionary with health status and recommendations
        """
        usage = self.estimate_current_usage()
        iterations = self.get_iteration_count()

        # Calculate percentages
        usage_pct = usage["total"] / self.MAX_CONTEXT_TOKENS

        # Determine status
        status = "healthy"
        recommendations = []

        # Check token usage
        if usage_pct >= self.CRITICAL_THRESHOLD:
            status = "critical"
            recommendations.append({
                "priority": "critical",
                "action": "Context near exhaustion - use /compact or /clear immediately",
                "detail": f"{usage['total']:,} / {self.MAX_CONTEXT_TOKENS:,} tokens ({usage_pct:.1%})"
            })
        elif usage_pct >= self.WARNING_THRESHOLD:
            status = "warning"
            recommendations.append({
                "priority": "warning",
                "action": "High context usage - consider /compact",
                "detail": f"{usage['total']:,} / {self.MAX_CONTEXT_TOKENS:,} tokens ({usage_pct:.1%})"
            })

        # Check iterations
        if iterations >= self.MAX_ITERATIONS_CRITICAL:
            status = "critical"
            recommendations.append({
                "priority": "critical",
                "action": "Too many iterations - start new session",
                "detail": f"{iterations} iterations (recommended max: {self.MAX_ITERATIONS_CRITICAL})"
            })
        elif iterations >= self.MAX_ITERATIONS_WARNING:
            if status != "critical":
                status = "warning"
            recommendations.append({
                "priority": "warning",
                "action": "Many iterations - consider wrapping up",
                "detail": f"{iterations} iterations (recommended max: {self.MAX_ITERATIONS_WARNING})"
            })

        # Optimization suggestions
        if usage["project_instructions"] > 8_000:
            recommendations.append({
                "priority": "info",
                "action": "CLAUDE.md is large - consider moving content to reference files",
                "detail": f"{usage['project_instructions']:,} tokens estimated"
            })

        if usage["mcp_servers"] > 10_000:
            recommendations.append({
                "priority": "info",
                "action": "High MCP overhead - use minimal-context or research profile",
                "detail": f"{usage['mcp_servers']:,} tokens from MCP servers"
            })

        return {
            "status": status,
            "usage": usage,
            "iterations": iterations,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

    def print_health_report(self):
        """Print formatted health report."""
        health = self.check_session_health()

        # Status emoji
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌"
        }

        print(f"\n{'='*60}")
        print(f"  Claude Code Session Health Report")
        print(f"{'='*60}\n")

        # Status
        emoji = status_emoji.get(health["status"], "ℹ️")
        print(f"Status: {emoji} {health['status'].upper()}\n")

        # Usage breakdown
        usage = health["usage"]
        print("Token Usage Breakdown:")
        print(f"  System Prompt:          {usage['system_prompt']:>8,} tokens")
        print(f"  Project Instructions:   {usage['project_instructions']:>8,} tokens")
        print(f"  MCP Servers:            {usage['mcp_servers']:>8,} tokens")
        print(f"  Context Files:          {usage['context_files']:>8,} tokens")
        print(f"  Conversation:           {usage['conversation']:>8,} tokens")
        print(f"  {'─'*40}")
        total_pct = usage['total'] / self.MAX_CONTEXT_TOKENS
        print(f"  Total:                  {usage['total']:>8,} tokens ({total_pct:.1%})")
        print(f"  Available:              {self.MAX_CONTEXT_TOKENS - usage['total']:>8,} tokens")
        print()

        # Iterations
        print(f"Iterations: {health['iterations']}\n")

        # Recommendations
        if health["recommendations"]:
            print("Recommendations:")
            for rec in health["recommendations"]:
                emoji = "❌" if rec["priority"] == "critical" else "⚠️" if rec["priority"] == "warning" else "ℹ️"
                print(f"\n  {emoji} {rec['action']}")
                print(f"     {rec['detail']}")
            print()

        print(f"{'='*60}\n")

def main():
    """Main entry point."""
    manager = SessionManager()

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            manager.print_health_report()
        elif command == "increment":
            current = manager.get_iteration_count()
            manager.update_iteration_count(current + 1)
            print(f"✅ Iteration count updated: {current + 1}")
        elif command == "reset":
            manager.update_iteration_count(0)
            print("✅ Iteration count reset")
        else:
            print(f"Unknown command: {command}")
            print("Usage: session-manager.py [check|increment|reset]")
            sys.exit(1)
    else:
        # Default: show health report
        manager.print_health_report()

if __name__ == "__main__":
    main()
