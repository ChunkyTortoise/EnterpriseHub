"""
Automated ML Pipeline for RAG System
Demonstrates enterprise MLOps automation and workflow orchestration
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline execution stages"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class PipelineType(Enum):
    """Types of ML pipelines"""

    TRAINING = "training"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    DATA_VALIDATION = "data_validation"
    MODEL_VALIDATION = "model_validation"


@dataclass
class PipelineStep:
    """Individual pipeline step configuration"""

    name: str
    command: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 3600
    retry_count: int = 3
    environment: Dict[str, str] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    # Runtime state
    stage: PipelineStage = PipelineStage.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    artifacts_produced: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["stage"] = self.stage.value
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


@dataclass
class PipelineRun:
    """Pipeline execution run"""

    run_id: str
    pipeline_name: str
    pipeline_type: PipelineType
    trigger: str
    configuration: Dict[str, Any]
    steps: List[PipelineStep]

    # Runtime state
    status: PipelineStage = PipelineStage.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["pipeline_type"] = self.pipeline_type.value
        data["status"] = self.status.value
        data["steps"] = [step.to_dict() for step in self.steps]
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


class PipelineExecutor:
    """
    Enterprise pipeline execution engine

    Features:
    - Dependency-based step ordering
    - Parallel execution where possible
    - Robust error handling and retries
    - Comprehensive logging and monitoring
    - Artifact management
    - Success criteria validation
    """

    def __init__(self, workspace_dir: str = "pipeline_workspace"):
        """Initialize pipeline executor"""
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.workspace_dir / "logs").mkdir(exist_ok=True)
        (self.workspace_dir / "artifacts").mkdir(exist_ok=True)
        (self.workspace_dir / "runs").mkdir(exist_ok=True)

        self.active_runs: Dict[str, PipelineRun] = {}

    def _generate_run_id(self, pipeline_name: str) -> str:
        """Generate unique run ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(f"{pipeline_name}_{timestamp}".encode()).hexdigest()[:8]
        return f"{pipeline_name}_{timestamp}_{hash_suffix}"

    def _resolve_dependencies(self, steps: List[PipelineStep]) -> List[List[str]]:
        """
        Resolve step dependencies and return execution order

        Returns list of step groups that can be executed in parallel
        """
        step_names = {step.name for step in steps}
        step_deps = {step.name: set(step.depends_on) for step in steps}

        # Validate dependencies exist
        for step_name, deps in step_deps.items():
            missing_deps = deps - step_names
            if missing_deps:
                raise ValueError(f"Step '{step_name}' has missing dependencies: {missing_deps}")

        # Topological sort with parallel groups
        executed = set()
        execution_groups = []

        while len(executed) < len(steps):
            # Find steps ready to execute (all dependencies satisfied)
            ready_steps = []
            for step in steps:
                if step.name not in executed and step_deps[step.name].issubset(executed):
                    ready_steps.append(step.name)

            if not ready_steps:
                # Check for circular dependencies
                remaining = step_names - executed
                raise ValueError(f"Circular dependency detected among steps: {remaining}")

            execution_groups.append(ready_steps)
            executed.update(ready_steps)

        return execution_groups

    async def _execute_step(self, step: PipelineStep, run_id: str, run_env: Dict[str, str]) -> bool:
        """
        Execute a single pipeline step

        Returns True if successful, False if failed
        """
        step.start_time = datetime.utcnow()
        step.stage = PipelineStage.RUNNING

        # Setup logging for this step
        log_file = self.workspace_dir / "logs" / f"{run_id}_{step.name}.log"

        try:
            logger.info(f"Starting step '{step.name}' in run {run_id}")

            # Prepare environment
            env = {**run_env, **step.environment}
            env["PIPELINE_RUN_ID"] = run_id
            env["PIPELINE_STEP_NAME"] = step.name
            env["PIPELINE_WORKSPACE"] = str(self.workspace_dir)

            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                step.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                cwd=self.workspace_dir,
            )

            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=step.timeout_seconds)
                step.output = stdout.decode("utf-8", errors="ignore")

                # Write output to log file
                with open(log_file, "w") as f:
                    f.write(step.output)

                # Check return code
                if process.returncode == 0:
                    step.stage = PipelineStage.SUCCESS
                    step.end_time = datetime.utcnow()

                    # Validate success criteria
                    if not self._validate_success_criteria(step):
                        step.stage = PipelineStage.FAILED
                        step.error_message = "Success criteria validation failed"
                        return False

                    # Collect artifacts
                    self._collect_artifacts(step, run_id)

                    logger.info(f"Step '{step.name}' completed successfully")
                    return True
                else:
                    step.stage = PipelineStage.FAILED
                    step.error_message = f"Command failed with return code {process.returncode}"
                    step.end_time = datetime.utcnow()
                    logger.error(f"Step '{step.name}' failed: {step.error_message}")
                    return False

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                step.stage = PipelineStage.FAILED
                step.error_message = f"Step timed out after {step.timeout_seconds} seconds"
                step.end_time = datetime.utcnow()
                logger.error(f"Step '{step.name}' timed out")
                return False

        except Exception as e:
            step.stage = PipelineStage.FAILED
            step.error_message = str(e)
            step.end_time = datetime.utcnow()
            logger.error(f"Step '{step.name}' failed with exception: {e}")
            return False

    def _validate_success_criteria(self, step: PipelineStep) -> bool:
        """Validate step success criteria"""
        if not step.success_criteria:
            return True

        try:
            # Check exit code
            if "exit_code" in step.success_criteria:
                # This would be checked in the main execution logic
                pass

            # Check output contains specific text
            if "output_contains" in step.success_criteria:
                required_text = step.success_criteria["output_contains"]
                if required_text not in (step.output or ""):
                    logger.error(f"Output validation failed: '{required_text}' not found")
                    return False

            # Check artifacts exist
            if "required_artifacts" in step.success_criteria:
                for artifact in step.success_criteria["required_artifacts"]:
                    artifact_path = self.workspace_dir / "artifacts" / artifact
                    if not artifact_path.exists():
                        logger.error(f"Required artifact '{artifact}' not found")
                        return False

            # Check metrics thresholds
            if "metrics_thresholds" in step.success_criteria:
                # Would need to parse metrics from output or artifacts
                pass

            return True

        except Exception as e:
            logger.error(f"Success criteria validation failed: {e}")
            return False

    def _collect_artifacts(self, step: PipelineStep, run_id: str) -> None:
        """Collect and organize step artifacts"""
        artifacts_dir = self.workspace_dir / "artifacts" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for artifact_pattern in step.artifacts:
            try:
                # Find matching files
                matching_files = list(self.workspace_dir.glob(artifact_pattern))

                for file_path in matching_files:
                    if file_path.is_file():
                        # Copy to artifacts directory
                        target_path = artifacts_dir / f"{step.name}_{file_path.name}"
                        target_path.write_bytes(file_path.read_bytes())
                        step.artifacts_produced.append(str(target_path))
                        logger.info(f"Collected artifact: {target_path}")

            except Exception as e:
                logger.warning(f"Failed to collect artifact '{artifact_pattern}': {e}")

    async def execute_pipeline(self, pipeline_config: Dict[str, Any], trigger: str = "manual") -> PipelineRun:
        """
        Execute a complete pipeline

        Args:
            pipeline_config: Pipeline configuration
            trigger: What triggered this pipeline run

        Returns:
            PipelineRun object with execution results
        """
        # Parse configuration
        pipeline_name = pipeline_config["name"]
        pipeline_type = PipelineType(pipeline_config["type"])
        steps_config = pipeline_config["steps"]

        # Create pipeline steps
        steps = []
        for step_config in steps_config:
            step = PipelineStep(**step_config)
            steps.append(step)

        # Create pipeline run
        run_id = self._generate_run_id(pipeline_name)
        run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            pipeline_type=pipeline_type,
            trigger=trigger,
            configuration=pipeline_config,
            steps=steps,
        )

        self.active_runs[run_id] = run
        run.start_time = datetime.utcnow()
        run.status = PipelineStage.RUNNING

        try:
            # Resolve dependencies and create execution groups
            execution_groups = self._resolve_dependencies(steps)

            logger.info(f"Starting pipeline run {run_id} with {len(execution_groups)} execution groups")

            # Execute steps in dependency order
            for group_idx, step_names in enumerate(execution_groups):
                logger.info(f"Executing group {group_idx + 1}: {step_names}")

                # Create tasks for parallel execution within group
                group_steps = [step for step in steps if step.name in step_names]
                tasks = []

                for step in group_steps:
                    task = asyncio.create_task(
                        self._execute_step_with_retry(step, run_id, pipeline_config.get("environment", {}))
                    )
                    tasks.append((step, task))

                # Wait for all tasks in group to complete
                for step, task in tasks:
                    try:
                        success = await task
                        if not success:
                            # Step failed, fail the entire pipeline
                            run.status = PipelineStage.FAILED
                            run.error_message = f"Step '{step.name}' failed: {step.error_message}"
                            run.end_time = datetime.utcnow()

                            # Cancel remaining tasks
                            for _, remaining_task in tasks:
                                if not remaining_task.done():
                                    remaining_task.cancel()

                            logger.error(f"Pipeline {run_id} failed at step '{step.name}'")
                            return run

                    except Exception as e:
                        run.status = PipelineStage.FAILED
                        run.error_message = f"Unexpected error in step '{step.name}': {str(e)}"
                        run.end_time = datetime.utcnow()
                        logger.error(f"Pipeline {run_id} failed with exception: {e}")
                        return run

            # All steps completed successfully
            run.status = PipelineStage.SUCCESS
            run.end_time = datetime.utcnow()

            # Collect final metrics
            run.metrics = self._collect_pipeline_metrics(run)

            logger.info(f"Pipeline {run_id} completed successfully")

        except Exception as e:
            run.status = PipelineStage.FAILED
            run.error_message = f"Pipeline execution failed: {str(e)}"
            run.end_time = datetime.utcnow()
            logger.error(f"Pipeline {run_id} failed: {e}")

        finally:
            # Save run results
            self._save_run_results(run)

        return run

    async def _execute_step_with_retry(self, step: PipelineStep, run_id: str, run_env: Dict[str, str]) -> bool:
        """Execute step with retry logic"""
        for attempt in range(step.retry_count + 1):
            if attempt > 0:
                logger.info(f"Retrying step '{step.name}' (attempt {attempt + 1})")
                await asyncio.sleep(2**attempt)  # Exponential backoff

            success = await self._execute_step(step, run_id, run_env)
            if success:
                return True

            if attempt < step.retry_count:
                # Reset step state for retry
                step.stage = PipelineStage.PENDING
                step.start_time = None
                step.end_time = None

        return False

    def _collect_pipeline_metrics(self, run: PipelineRun) -> Dict[str, float]:
        """Collect pipeline execution metrics"""
        metrics = {}

        if run.start_time and run.end_time:
            duration = (run.end_time - run.start_time).total_seconds()
            metrics["total_duration_seconds"] = duration

        # Step statistics
        successful_steps = sum(1 for step in run.steps if step.stage == PipelineStage.SUCCESS)
        failed_steps = sum(1 for step in run.steps if step.stage == PipelineStage.FAILED)

        metrics["successful_steps"] = successful_steps
        metrics["failed_steps"] = failed_steps
        metrics["total_steps"] = len(run.steps)
        metrics["success_rate"] = successful_steps / len(run.steps) if run.steps else 0

        # Average step duration
        step_durations = []
        for step in run.steps:
            if step.start_time and step.end_time:
                duration = (step.end_time - step.start_time).total_seconds()
                step_durations.append(duration)

        if step_durations:
            metrics["avg_step_duration_seconds"] = sum(step_durations) / len(step_durations)
            metrics["max_step_duration_seconds"] = max(step_durations)

        return metrics

    def _save_run_results(self, run: PipelineRun) -> None:
        """Save pipeline run results"""
        run_file = self.workspace_dir / "runs" / f"{run.run_id}.json"

        try:
            with open(run_file, "w") as f:
                json.dump(run.to_dict(), f, indent=2, default=str)
            logger.info(f"Saved run results to {run_file}")
        except Exception as e:
            logger.error(f"Failed to save run results: {e}")

    def get_run_status(self, run_id: str) -> Optional[PipelineRun]:
        """Get status of a pipeline run"""
        return self.active_runs.get(run_id)

    def list_runs(self, pipeline_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent pipeline runs"""
        runs_dir = self.workspace_dir / "runs"
        run_files = sorted(runs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        runs = []
        for run_file in run_files[:limit]:
            try:
                with open(run_file, "r") as f:
                    run_data = json.load(f)

                if pipeline_name is None or run_data.get("pipeline_name") == pipeline_name:
                    runs.append(run_data)

            except Exception as e:
                logger.warning(f"Failed to load run file {run_file}: {e}")

        return runs


class PipelineBuilder:
    """
    Builder for creating ML pipeline configurations

    Provides fluent API for defining complex pipelines
    """

    def __init__(self, name: str, pipeline_type: PipelineType):
        """Initialize pipeline builder"""
        self.config = {"name": name, "type": pipeline_type.value, "steps": [], "environment": {}}

    def add_step(
        self,
        name: str,
        command: str,
        description: str = "",
        depends_on: Optional[List[str]] = None,
        timeout_seconds: int = 3600,
        retry_count: int = 3,
        environment: Optional[Dict[str, str]] = None,
        artifacts: Optional[List[str]] = None,
        success_criteria: Optional[Dict[str, Any]] = None,
    ) -> "PipelineBuilder":
        """Add a step to the pipeline"""
        step_config = {
            "name": name,
            "command": command,
            "description": description,
            "depends_on": depends_on or [],
            "timeout_seconds": timeout_seconds,
            "retry_count": retry_count,
            "environment": environment or {},
            "artifacts": artifacts or [],
            "success_criteria": success_criteria or {},
        }

        self.config["steps"].append(step_config)
        return self

    def set_environment(self, env: Dict[str, str]) -> "PipelineBuilder":
        """Set global environment variables"""
        self.config["environment"].update(env)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the pipeline configuration"""
        return self.config.copy()


# Pre-built pipeline templates for RAG system
class RAGPipelineTemplates:
    """Pre-built pipeline templates for RAG system"""

    @staticmethod
    def create_model_evaluation_pipeline() -> Dict[str, Any]:
        """Create model evaluation pipeline"""
        builder = PipelineBuilder("rag_model_evaluation", PipelineType.EVALUATION)

        return (
            builder.add_step(
                name="setup_environment",
                command="python -m pip install -r requirements.txt",
                description="Install dependencies",
                timeout_seconds=600,
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="validate_data",
                command="python -m pytest tests/test_data_validation.py -v",
                description="Validate evaluation datasets",
                depends_on=["setup_environment"],
                artifacts=["test_results.xml"],
                success_criteria={"exit_code": 0, "output_contains": "PASSED"},
            )
            .add_step(
                name="run_benchmarks",
                command="make benchmark-quality",
                description="Execute quality benchmarks",
                depends_on=["validate_data"],
                timeout_seconds=1800,
                artifacts=["benchmark_results/*.json"],
                success_criteria={"required_artifacts": ["quality_combined.json"]},
            )
            .add_step(
                name="generate_report",
                command="python scripts/generate_benchmark_report.py --results-dir benchmark_results --output evaluation_report",
                description="Generate evaluation report",
                depends_on=["run_benchmarks"],
                artifacts=["evaluation_report.*"],
                success_criteria={"required_artifacts": ["evaluation_report.html"]},
            )
            .set_environment({"PYTHONPATH": ".", "RAG_CONFIG": "config/evaluation.yaml"})
            .build()
        )

    @staticmethod
    def create_model_deployment_pipeline() -> Dict[str, Any]:
        """Create model deployment pipeline"""
        builder = PipelineBuilder("rag_model_deployment", PipelineType.DEPLOYMENT)

        return (
            builder.add_step(
                name="validate_model",
                command="python scripts/validate_model.py --model-path models/current",
                description="Validate model artifacts",
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="run_smoke_tests",
                command="python -m pytest tests/test_model_smoke.py -v",
                description="Run smoke tests",
                depends_on=["validate_model"],
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="deploy_staging",
                command="python scripts/deploy_model.py --environment staging",
                description="Deploy to staging",
                depends_on=["run_smoke_tests"],
                timeout_seconds=900,
                success_criteria={"output_contains": "deployment_successful"},
            )
            .add_step(
                name="integration_tests",
                command="python -m pytest tests/test_integration.py -v --staging",
                description="Run integration tests on staging",
                depends_on=["deploy_staging"],
                timeout_seconds=1200,
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="deploy_production",
                command="python scripts/deploy_model.py --environment production",
                description="Deploy to production",
                depends_on=["integration_tests"],
                timeout_seconds=900,
                success_criteria={"output_contains": "deployment_successful"},
            )
            .set_environment(
                {"DEPLOYMENT_CONFIG": "config/deployment.yaml", "MODEL_REGISTRY_URL": "http://localhost:5000"}
            )
            .build()
        )

    @staticmethod
    def create_monitoring_pipeline() -> Dict[str, Any]:
        """Create monitoring and drift detection pipeline"""
        builder = PipelineBuilder("rag_monitoring", PipelineType.MONITORING)

        return (
            builder.add_step(
                name="collect_metrics",
                command="python scripts/collect_production_metrics.py --window 1h",
                description="Collect production metrics",
                artifacts=["metrics/*.json"],
                success_criteria={"required_artifacts": ["metrics/current.json"]},
            )
            .add_step(
                name="detect_drift",
                command="python scripts/detect_drift.py --metrics-path metrics/current.json",
                description="Run drift detection",
                depends_on=["collect_metrics"],
                artifacts=["drift_report.json"],
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="update_dashboards",
                command="python scripts/update_monitoring_dashboards.py",
                description="Update monitoring dashboards",
                depends_on=["detect_drift"],
                success_criteria={"exit_code": 0},
            )
            .add_step(
                name="send_alerts",
                command="python scripts/process_alerts.py --drift-report drift_report.json",
                description="Process and send alerts if needed",
                depends_on=["detect_drift"],
                success_criteria={"exit_code": 0},
            )
            .set_environment({"MONITORING_CONFIG": "config/monitoring.yaml"})
            .build()
        )
