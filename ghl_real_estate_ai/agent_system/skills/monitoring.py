"""
System Monitoring and Health Skills.
Allows agents to audit system performance and health.
"""
from typing import Dict, Any, List
import os
import psutil
import time
from .base import skill
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@skill(name="get_system_health", tags=["monitoring", "devops"])
def get_system_health() -> Dict[str, Any]:
    """
    Returns high-level system health metrics (CPU, Memory, Disk).
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if cpu_percent < 90 else "strained",
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "disk_free_gb": disk.free / (1024**3),
        "timestamp": time.time()
    }

@skill(name="check_agent_performance", tags=["monitoring", "agents"])
def check_agent_performance(agent_name: str) -> Dict[str, Any]:
    """
    Checks the performance metrics for a specific agent.
    
    Args:
        agent_name: Name of the agent to check.
    """
    # In a real implementation, this would query a metrics database (e.g. Prometheus or Redis)
    return {
        "agent": agent_name,
        "success_rate": 0.98,
        "average_latency_ms": 120,
        "total_tasks_completed": 1542,
        "last_active": "2026-01-20T08:00:00Z"
    }

@skill(name="list_active_tasks", tags=["monitoring", "orchestration"])
def list_active_tasks() -> List[Dict[str, Any]]:
    """
    Lists currently running or pending tasks in the agent swarm.
    """
    # This would interact with the SwarmOrchestrator's blackboard/task list
    return [
        {"id": "task_001", "agent": "Alpha", "status": "in_progress", "started_at": time.time() - 300},
        {"id": "task_002", "agent": "Beta", "status": "pending"}
    ]
