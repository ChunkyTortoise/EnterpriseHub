
import asyncio
import os
import sys

# Ensure current directory is in PYTHONPATH
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher

async def main():
    researcher = PerplexityResearcher()
    
    categories = {
        "Strategic & Orchestration": "Chief Architect Agent, Task Decomposer Agent, Context Manager Agent, Constraint Verifier Agent.",
        "Low-Level & Performance": "Bytecode Optimization Agent, Memory Leak Profiler, Database Query Optimizer, Assembly/C-Level Expert.",
        "Quality & Security": "Pentest/Red-Team Agent, Fuzzing Agent, Static Analysis Enforcement Agent, Regression Hunter, Accessibility (A11y) Compliance Agent.",
        "Legacy & Migration": "Library Version Migrator (e.g., Python 2-3, React Class to Hooks), COBOL-to-Java Transpiler Agent, Dead-Code Janitor.",
        "UX & Documentation": "Visual Consistency Auditor, i18n/Localization Agent, API Spec Sync Agent, User Persona Simulator.",
        "Infrastructure & DevOps": "Cloud Cost Optimizer, K8s Configuration Auditor, Incident Triage Agent, Dependency Vulnerability Resolver."
    }
    
    all_reports = []
    for cat, examples in categories.items():
        print(f"Researching Category: {cat}...")
        topic = f"Detail the specialized sub-agents needed for the '{cat}' domain in an autonomous AI software factory. Examples to explore: {examples}"
        context = "Provide specific roles, their inputs/outputs, and the specialized tools they would use (e.g., Valgrind, Semgrep, Playwright)."
        report = await researcher.research_topic(topic, context)
        all_reports.append(f"### {cat}\n{report}")
    
    final_report = "\n\n".join(all_reports)
    print("--- COMPREHENSIVE RESEARCH REPORT ---")
    print(final_report)


if __name__ == "__main__":
    asyncio.run(main())
