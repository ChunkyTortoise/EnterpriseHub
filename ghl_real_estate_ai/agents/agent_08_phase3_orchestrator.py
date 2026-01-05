#!/usr/bin/env python3
"""
Agent 8: Phase 3 Master Orchestrator
Coordinates all Phase 3 agents and tracks progress
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class Phase3Orchestrator:
    """Master orchestrator for Phase 3 execution."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.agents_dir = self.base_dir / "agents"
        
        # Define all Phase 3 agents
        self.agents = {
            "tier1": [
                {
                    "id": 9,
                    "name": "Test Logic Implementer",
                    "file": "agent_09_test_logic_implementer.py",
                    "objective": "Achieve 80%+ test coverage",
                    "estimated_iterations": 20,
                    "priority": "CRITICAL"
                },
                {
                    "id": 10,
                    "name": "Documentation Completionist",
                    "file": "agent_10_documentation_completionist.py",
                    "objective": "Document all 48+ remaining functions",
                    "estimated_iterations": 12,
                    "priority": "CRITICAL"
                },
                {
                    "id": 11,
                    "name": "Security Test Fixer",
                    "file": "agent_11_security_test_fixer.py",
                    "objective": "Fix all security integration tests",
                    "estimated_iterations": 7,
                    "priority": "CRITICAL"
                },
                {
                    "id": 12,
                    "name": "Security Auditor",
                    "file": "agent_12_security_auditor.py",
                    "objective": "Zero critical vulnerabilities",
                    "estimated_iterations": 5,
                    "priority": "CRITICAL"
                }
            ],
            "tier2": [
                {
                    "id": 13,
                    "name": "Performance Optimizer",
                    "file": "agent_13_performance_optimizer.py",
                    "objective": "Response time < 200ms",
                    "estimated_iterations": 10,
                    "priority": "HIGH"
                },
                {
                    "id": 14,
                    "name": "Error Handler",
                    "file": "agent_14_error_handler.py",
                    "objective": "Comprehensive error handling",
                    "estimated_iterations": 8,
                    "priority": "HIGH"
                },
                {
                    "id": 15,
                    "name": "Observability Engineer",
                    "file": "agent_15_observability_engineer.py",
                    "objective": "Production-grade logging & monitoring",
                    "estimated_iterations": 9,
                    "priority": "HIGH"
                },
                {
                    "id": 16,
                    "name": "API Documentor",
                    "file": "agent_16_api_documentor.py",
                    "objective": "Complete OpenAPI documentation",
                    "estimated_iterations": 6,
                    "priority": "HIGH"
                }
            ],
            "tier3": [
                {
                    "id": 17,
                    "name": "Load Tester",
                    "file": "agent_17_load_tester.py",
                    "objective": "Test under 1000+ concurrent users",
                    "estimated_iterations": 5,
                    "priority": "MEDIUM"
                },
                {
                    "id": 18,
                    "name": "Code Refactorer",
                    "file": "agent_18_code_refactorer.py",
                    "objective": "Reduce code complexity",
                    "estimated_iterations": 10,
                    "priority": "MEDIUM"
                }
            ]
        }
        
        self.results = {
            "tier1": {"completed": [], "failed": [], "skipped": []},
            "tier2": {"completed": [], "failed": [], "skipped": []},
            "tier3": {"completed": [], "failed": [], "skipped": []}
        }
        
        self.start_time = None
        self.end_time = None
    
    def check_agent_exists(self, agent: Dict) -> bool:
        """Check if agent file exists."""
        agent_path = self.agents_dir / agent["file"]
        return agent_path.exists()
    
    def run_agent(self, agent: Dict, tier: str) -> Tuple[bool, str]:
        """Execute a single agent."""
        agent_path = self.agents_dir / agent["file"]
        
        if not agent_path.exists():
            return False, f"Agent file not found: {agent['file']}"
        
        print(f"\n{'='*80}")
        print(f"🚀 Running Agent {agent['id']}: {agent['name']}")
        print(f"{'='*80}")
        print(f"Objective: {agent['objective']}")
        print(f"Estimated iterations: {agent['estimated_iterations']}")
        print(f"Priority: {agent['priority']}")
        print()
        
        try:
            # Run the agent
            result = subprocess.run(
                ["python3", str(agent_path)],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            
            if result.returncode == 0:
                print(f"\n✅ Agent {agent['id']} completed successfully")
                self.results[tier]["completed"].append(agent["id"])
                return True, "Success"
            else:
                print(f"\n❌ Agent {agent['id']} failed")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                self.results[tier]["failed"].append(agent["id"])
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            print(f"\n⏱️  Agent {agent['id']} timed out")
            self.results[tier]["failed"].append(agent["id"])
            return False, "Timeout"
        
        except Exception as e:
            print(f"\n❌ Agent {agent['id']} error: {e}")
            self.results[tier]["failed"].append(agent["id"])
            return False, str(e)
    
    def run_tier(self, tier_name: str, parallel: bool = False) -> bool:
        """Execute all agents in a tier."""
        agents = self.agents.get(tier_name, [])
        
        if not agents:
            print(f"⚠️  No agents defined for {tier_name}")
            return True
        
        print(f"\n{'='*80}")
        print(f"📋 TIER: {tier_name.upper()}")
        print(f"{'='*80}")
        print(f"Agents: {len(agents)}")
        print(f"Mode: {'Parallel' if parallel else 'Sequential'}")
        print()
        
        all_success = True
        
        for agent in agents:
            # Check if agent exists
            if not self.check_agent_exists(agent):
                print(f"⚠️  Skipping Agent {agent['id']}: {agent['name']} (not created yet)")
                self.results[tier_name]["skipped"].append(agent["id"])
                continue
            
            # Run agent
            success, message = self.run_agent(agent, tier_name)
            
            if not success:
                all_success = False
                
                # For Tier 1, stop on failure
                if tier_name == "tier1":
                    print(f"\n❌ Tier 1 agent failed. Stopping execution.")
                    return False
        
        return all_success
    
    def generate_progress_report(self) -> str:
        """Generate progress report."""
        report = []
        report.append("=" * 80)
        report.append("PHASE 3 ORCHESTRATOR - PROGRESS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Calculate totals
        total_completed = sum(len(self.results[t]["completed"]) for t in self.results)
        total_failed = sum(len(self.results[t]["failed"]) for t in self.results)
        total_skipped = sum(len(self.results[t]["skipped"]) for t in self.results)
        total_agents = sum(len(self.agents[t]) for t in self.agents)
        
        report.append(f"📊 Overall Progress:")
        report.append(f"  Total Agents: {total_agents}")
        report.append(f"  Completed: {total_completed} ✅")
        report.append(f"  Failed: {total_failed} ❌")
        report.append(f"  Skipped: {total_skipped} ⚠️")
        report.append(f"  Success Rate: {(total_completed / (total_completed + total_failed) * 100) if (total_completed + total_failed) > 0 else 0:.1f}%")
        report.append("")
        
        # Tier breakdown
        for tier_name in ["tier1", "tier2", "tier3"]:
            tier_results = self.results[tier_name]
            report.append(f"📋 {tier_name.upper()}:")
            report.append(f"  Completed: {tier_results['completed']}")
            report.append(f"  Failed: {tier_results['failed']}")
            report.append(f"  Skipped: {tier_results['skipped']}")
            report.append("")
        
        # Execution time
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            report.append(f"⏱️  Execution Time: {duration:.2f} seconds")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_phase3(self, tiers: List[str] = ["tier1"]) -> bool:
        """Execute Phase 3 with specified tiers."""
        self.start_time = datetime.now()
        
        print("=" * 80)
        print("🚀 PHASE 3 ORCHESTRATOR - STARTING")
        print("=" * 80)
        print(f"Tiers to execute: {', '.join(tiers)}")
        print(f"Start time: {self.start_time}")
        print()
        
        all_success = True
        
        for tier_name in tiers:
            if tier_name not in self.agents:
                print(f"⚠️  Unknown tier: {tier_name}")
                continue
            
            success = self.run_tier(tier_name)
            
            if not success:
                all_success = False
                
                # Stop execution if Tier 1 fails
                if tier_name == "tier1":
                    print("\n❌ Tier 1 failed. Stopping Phase 3 execution.")
                    break
        
        self.end_time = datetime.now()
        
        # Generate report
        print("\n" + "=" * 80)
        print("✅ PHASE 3 ORCHESTRATOR - COMPLETE")
        print("=" * 80)
        print()
        
        report = self.generate_progress_report()
        print(report)
        
        # Save report
        report_path = self.base_dir / "PHASE3_ORCHESTRATOR_REPORT.md"
        report_path.write_text(report)
        print(f"\n📄 Report saved to: {report_path}")
        
        return all_success


def main():
    """Run Phase 3 orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Orchestrator")
    parser.add_argument(
        "--tiers",
        nargs="+",
        default=["tier1"],
        choices=["tier1", "tier2", "tier3"],
        help="Tiers to execute (default: tier1)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all tiers"
    )
    
    args = parser.parse_args()
    
    if args.all:
        tiers = ["tier1", "tier2", "tier3"]
    else:
        tiers = args.tiers
    
    orchestrator = Phase3Orchestrator()
    success = orchestrator.run_phase3(tiers=tiers)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
