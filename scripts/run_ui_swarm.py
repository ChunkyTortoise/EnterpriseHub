import asyncio
from pathlib import Path
from ghl_real_estate_ai.agents.swarm_orchestrator import SwarmOrchestrator, TaskStatus


async def run_ui_swarm():
    """
    Runs the agent swarm specifically for frontend UI generation and visual QA.
    """
    print("🚀 Initializing Frontend Agent Swarm (UI Only Mode) கார்பன்...")
    project_root = Path(__file__).parent.parent
    orchestrator = SwarmOrchestrator(project_root)

    # Identify UI tasks
    ui_task_ids = ["task_021", "task_022", "task_023", "task_024"]

    # Deactivate all other tasks to save quota
    for tid, task in orchestrator.tasks.items():
        if tid not in ui_task_ids:
            task.status = TaskStatus.COMPLETED  # Mark as completed so dependencies are met
            orchestrator.completed_tasks.add(tid)

    # Inject some mock data to the blackboard that PHI might need
    orchestrator.blackboard.write(
        "project_analysis", {"framework": "Next.js", "ui_library": "Shadcn/UI", "viz_library": "Tremor"}, "System"
    )
    orchestrator.blackboard.write("api_docs", "GHL API endpoints for leads and opportunities are available.", "System")

    print("🎨 Starting UI Generation Swarm...")
    await orchestrator.run_parallel_swarm()

    print("\n✅ UI Swarm Run Complete.")


if __name__ == "__main__":
    asyncio.run(run_ui_swarm())
