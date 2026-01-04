#!/usr/bin/env python3
"""
Tier 2 Orchestrator - Parallel Agent Execution

Launches all 4 Tier 2 agents simultaneously and coordinates their work
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import all Tier 2 agents
from theta_recommendations import AgentTheta
from iota_revenue_attribution import AgentIota
from kappa_competitive_benchmarking import AgentKappa
from lambda_quality_assurance import AgentLambda


class Tier2Orchestrator:
    """Orchestrate parallel execution of Tier 2 intelligence agents"""
    
    def __init__(self):
        self.name = "Tier 2 Orchestrator"
        self.agents = {
            "theta": AgentTheta(),
            "iota": AgentIota(),
            "kappa": AgentKappa(),
            "lambda": AgentLambda()
        }
        self.results = {}
        
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🎯 {self.name}: {message}")
        
    async def execute_all_agents(self) -> Dict[str, Any]:
        """Execute all agents in parallel"""
        self.log("🚀 Launching all 4 Tier 2 agents in parallel...")
        
        # Create tasks for parallel execution
        tasks = {
            name: agent.execute_mission() 
            for name, agent in self.agents.items()
        }
        
        # Execute all agents concurrently
        self.log("⚡ Agents running in parallel...")
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to agent names
        self.results = dict(zip(tasks.keys(), results))
        
        # Check for any failures
        failures = [
            name for name, result in self.results.items() 
            if isinstance(result, Exception)
        ]
        
        if failures:
            self.log(f"⚠️ Some agents encountered errors: {failures}")
        else:
            self.log("✅ All agents completed successfully!")
        
        return self.results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary of all agent deliverables"""
        total_deliverables = sum(
            len(result.get("deliverables", [])) 
            for result in self.results.values()
            if isinstance(result, dict)
        )
        
        summary = {
            "orchestrator": self.name,
            "execution_time": datetime.now().isoformat(),
            "agents_executed": len(self.agents),
            "agents_successful": sum(
                1 for r in self.results.values() 
                if isinstance(r, dict) and r.get("status") == "COMPLETE"
            ),
            "total_deliverables": total_deliverables,
            "agent_results": self.results,
            "tier2_features": {
                "smart_recommendations": {
                    "status": self.results.get("theta", {}).get("status"),
                    "description": "Proactive optimization recommendations based on data patterns",
                    "deliverables": self.results.get("theta", {}).get("deliverables", [])
                },
                "revenue_attribution": {
                    "status": self.results.get("iota", {}).get("status"),
                    "description": "Full revenue tracking from lead to closed deal",
                    "deliverables": self.results.get("iota", {}).get("deliverables", [])
                },
                "competitive_benchmarking": {
                    "status": self.results.get("kappa", {}).get("status"),
                    "description": "Performance comparison against industry standards",
                    "deliverables": self.results.get("kappa", {}).get("deliverables", [])
                },
                "quality_assurance": {
                    "status": self.results.get("lambda", {}).get("status"),
                    "description": "AI-powered conversation quality review",
                    "deliverables": self.results.get("lambda", {}).get("deliverables", [])
                }
            }
        }
        
        return summary


async def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🎯 TIER 2 INTELLIGENCE ORCHESTRATOR")
    print("="*70)
    print("\nLaunching 4 agents in parallel:")
    print("  💡 Agent Theta - Smart Recommendations")
    print("  💰 Agent Iota - Revenue Attribution")
    print("  📊 Agent Kappa - Competitive Benchmarking")
    print("  🔍 Agent Lambda - Quality Assurance")
    print("\n" + "="*70 + "\n")
    
    orchestrator = Tier2Orchestrator()
    
    # Execute all agents in parallel
    start_time = datetime.now()
    results = await orchestrator.execute_all_agents()
    end_time = datetime.now()
    
    # Generate summary report
    summary = orchestrator.generate_summary_report()
    
    # Save summary report
    report_file = Path(__file__).parent.parent / f"TIER2_EXECUTION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 EXECUTION SUMMARY")
    print("="*70)
    print(f"\nTotal Execution Time: {(end_time - start_time).total_seconds():.2f} seconds")
    print(f"Agents Executed: {summary['agents_executed']}")
    print(f"Agents Successful: {summary['agents_successful']}")
    print(f"Total Deliverables: {summary['total_deliverables']}")
    print(f"\nDetailed report saved: {report_file.name}")
    print("\n" + "="*70 + "\n")
    
    # Print individual agent status
    print("Individual Agent Status:")
    for feature_name, feature_data in summary['tier2_features'].items():
        status_icon = "✅" if feature_data['status'] == "COMPLETE" else "❌"
        print(f"  {status_icon} {feature_name}: {feature_data['status']}")
        print(f"     {feature_data['description']}")
        print(f"     Deliverables: {len(feature_data['deliverables'])}")
    
    print("\n" + "="*70 + "\n")
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())
