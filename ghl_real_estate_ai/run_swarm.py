#!/usr/bin/env python3
"""
🚀 Quick Launcher for Agent Swarm
=================================

Run this to execute the full agent swarm for GHL project finalization.

Usage:
    python3 run_swarm.py

Author: Agent Swarm System
Date: 2026-01-05
"""

import sys
from pathlib import Path

# Add agents directory to path
agents_dir = Path(__file__).parent / "agents"
sys.path.insert(0, str(agents_dir))

from swarm_executor import SwarmExecutor


def main():
    """Main launcher"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          🤖 GHL PROJECT FINALIZATION - AGENT SWARM SYSTEM 🤖               ║
║                                                                            ║
║  5 Specialized Union[Agents, 20] Union[Tasks, Full] Project Finalization              ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Agent Roster:
  🔍 Alpha   - Code Auditor (Quality & Security)
  🧪 Beta    - Test Completer (TODO Resolution)
  🔗 Gamma   - Integration Validator (API & Services)
  📚 Delta   - Documentation Finalizer (Docs & Guides)
  🚀 Epsilon - Deployment Preparer (Production Ready)

Tasks:
  📊 Phase 1: Analysis & Planning (2 tasks)
  🔍 Phase 2: Code Quality (2 tasks)
  🧪 Phase 3: Test Completion (4 tasks)
  🔗 Phase 4: Integration Validation (3 tasks)
  📚 Phase 5: Documentation (3 tasks)
  🚀 Phase 6: Deployment Preparation (4 tasks)
  ✅ Phase 7: Final Validation (2 tasks)

""")
    
    response = input("🚀 Ready to launch agent swarm? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Swarm launch cancelled.")
        return
    
    print("\n" + "="*80)
    print("🚀 LAUNCHING AGENT SWARM...")
    print("="*80 + "\n")
    
    # Execute swarm
    project_root = Path(__file__).parent
    executor = SwarmExecutor(project_root)
    executor.execute_all()
    
    print("\n" + "="*80)
    print("✨ AGENT SWARM COMPLETE!")
    print("="*80)
    print("\n📊 Check the reports/ directory for detailed results.")
    print("\n")


if __name__ == "__main__":
    main()
