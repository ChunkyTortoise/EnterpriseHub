"""CLI main entry point for AgentForge.

This module provides the command-line interface for AgentForge,
including project scaffolding and agent creation commands.
"""

import argparse
import asyncio
import importlib.util
import inspect
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Template files for project scaffolding
AGENTS_TEMPLATE = '''"""
Agent definitions for {project_name}.
"""
from agentforge import ConfigurableAgent, tool

@tool
def example_tool(query: str) -> str:
    """An example tool for demonstration."""
    return f"Processed: {query}"

# Define your agents here
researcher = ConfigurableAgent(
    name="researcher",
    instructions="Research the given topic thoroughly.",
    tools=[example_tool],
    llm="openai/gpt-4o",
)
'''

MAIN_TEMPLATE = '''"""
Main entry point for {project_name}.
"""
import asyncio
from agentforge import DAG, DAGConfig, ExecutionEngine
from agents import researcher

async def main():
    # Create a simple DAG
    dag = DAG(config=DAGConfig(name="main_workflow"))
    dag.add_node("researcher", researcher)

    # Execute
    engine = ExecutionEngine()
    result = await engine.execute(dag)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
'''

CONFIG_TEMPLATE = """# AgentForge Configuration
# Model settings
default_llm: openai/gpt-4o

# Execution settings
max_retries: 3
timeout: 300

# Memory settings
session_max_messages: 100
"""

README_TEMPLATE = """# {project_name}

A multi-agent system built with AgentForge.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export OPENAI_API_KEY=your-key-here
   ```

3. Run the agents:
   ```bash
   python main.py
   ```

## Project Structure

- `agents.py` - Agent definitions
- `main.py` - Main entry point
- `config.yaml` - Configuration
- `tests/` - Test files

## Documentation

See [AgentForge Docs](https://github.com/your-org/agentforge) for more information.
"""

REQUIREMENTS_TEMPLATE = """agentforge>=0.2.0
pytest>=8.0
pytest-asyncio>=0.23
"""

TEST_TEMPLATE = '''"""
Tests for {project_name}.
"""
import pytest
from agentforge import DAG, DAGConfig, ExecutionEngine

def test_dag_creation():
    """Test that a DAG can be created."""
    dag = DAG(config=DAGConfig(name="test"))
    assert dag.config.name == "test"
'''


class CLI:
    """AgentForge CLI."""

    def __init__(self) -> None:
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog="agentforge", description="AgentForge - Lightweight multi-agent LLM orchestration"
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # init command
        init_parser = subparsers.add_parser("init", help="Create a new project")
        init_parser.add_argument("project_name", help="Name of the project")
        init_parser.add_argument("--path", "-p", default=".", help="Path to create project in")
        init_parser.add_argument("--no-tests", action="store_true", help="Skip test file creation")

        # add command
        add_parser = subparsers.add_parser("add", help="Add components to project")
        add_parser.add_argument("component", choices=["agent", "tool"], help="Component to add")
        add_parser.add_argument("name", help="Name of the component")
        add_parser.add_argument("--llm", default="openai/gpt-4o", help="LLM for agent")

        # run command
        run_parser = subparsers.add_parser("run", help="Run a DAG")
        run_parser.add_argument("--file", "-f", default="main.py", help="File to run")
        run_parser.add_argument(
            "--monitor", "-m", action="store_true", help="Show monitoring dashboard"
        )

        # version command
        subparsers.add_parser("version", help="Show version")

        # report command
        report_parser = subparsers.add_parser("report", help="Generate observability reports")
        report_subparsers = report_parser.add_subparsers(dest="report_command", help="Report type")

        report_validate = report_subparsers.add_parser(
            "validate-runlog", help="Validate a run log file"
        )
        report_validate.add_argument("--input", required=True, help="Path to run log JSON file")
        report_validate.add_argument(
            "--output", required=True, help="Path to write markdown report"
        )

        report_daily = report_subparsers.add_parser(
            "daily-errors", help="Render daily error report"
        )
        report_daily.add_argument("--input", required=True, help="Path to run log JSON file")
        report_daily.add_argument("--output", required=True, help="Path to write markdown report")

        report_trends = report_subparsers.add_parser(
            "trends", help="Render latency/cost trend report"
        )
        report_trends.add_argument("--input", required=True, help="Path to run log JSON file")
        report_trends.add_argument("--output", required=True, help="Path to write markdown report")

        report_pack = report_subparsers.add_parser(
            "pack", help="Render validate/errors/trends/roi reports together"
        )
        report_pack.add_argument("--input", required=True, help="Path to run log JSON file")
        report_pack.add_argument(
            "--output-dir", required=True, help="Directory to write report files into"
        )
        report_pack.add_argument(
            "--format",
            choices=["md", "json"],
            default="md",
            help="Output format for the report pack (default: md)",
        )

        # bundle command
        bundle_parser = subparsers.add_parser("bundle", help="Generate handoff bundles")
        bundle_subparsers = bundle_parser.add_subparsers(dest="bundle_command", help="Bundle type")

        bundle_handoff = bundle_subparsers.add_parser(
            "handoff", help="Render the client handoff document bundle"
        )
        bundle_handoff.add_argument(
            "--output-dir", required=True, help="Directory to write handoff files into"
        )
        bundle_handoff.add_argument(
            "--project", required=True, help="Project name used in handoff documents"
        )
        bundle_handoff.add_argument(
            "--execution-profile",
            required=True,
            help="Execution profile name used in the architecture document",
        )

        return parser

    def run(self, args: list[str] | None = None) -> int:
        """Run the CLI."""
        parsed = self.parser.parse_args(args)

        if parsed.command == "init":
            return self._cmd_init(parsed)
        elif parsed.command == "add":
            return self._cmd_add(parsed)
        elif parsed.command == "run":
            return self._cmd_run(parsed)
        elif parsed.command == "version":
            return self._cmd_version()
        elif parsed.command == "report":
            return self._cmd_report(parsed)
        elif parsed.command == "bundle":
            return self._cmd_bundle(parsed)
        else:
            self.parser.print_help()
            return 0

    def _cmd_init(self, args: argparse.Namespace) -> int:
        """Initialize a new project."""
        project_path = Path(args.path) / args.project_name

        if project_path.exists():
            print(f"Error: Directory '{project_path}' already exists")
            return 1

        # Create directory structure
        project_path.mkdir(parents=True)
        (project_path / "tests").mkdir()

        # Write files
        self._write_file(project_path / "agents.py", AGENTS_TEMPLATE, args.project_name)
        self._write_file(project_path / "main.py", MAIN_TEMPLATE, args.project_name)
        self._write_file(project_path / "config.yaml", CONFIG_TEMPLATE, args.project_name)
        self._write_file(project_path / "README.md", README_TEMPLATE, args.project_name)
        self._write_file(
            project_path / "requirements.txt", REQUIREMENTS_TEMPLATE, args.project_name
        )

        if not args.no_tests:
            self._write_file(
                project_path / "tests" / "test_agents.py", TEST_TEMPLATE, args.project_name
            )

        print(f"Created project '{args.project_name}' at {project_path}")
        print("\nNext steps:")
        print(f"  cd {args.project_name}")
        print("  pip install -r requirements.txt")
        print("  python main.py")

        return 0

    def _cmd_add(self, args: argparse.Namespace) -> int:
        """Add a component to the project."""
        if args.component == "agent":
            return self._add_agent(args)
        elif args.component == "tool":
            return self._add_tool(args)
        return 1

    def _add_agent(self, args: argparse.Namespace) -> int:
        """Add an agent to the project."""
        agents_file = Path("agents.py")
        if not agents_file.exists():
            print("Error: No agents.py found. Run 'agentforge init' first.")
            return 1

        agent_code = f"""

from agentforge import ConfigurableAgent

{args.name} = ConfigurableAgent(
    name="{args.name}",
    instructions="Add instructions for {args.name}.",
    llm="{args.llm}",
)
"""
        with open(agents_file, "a") as f:
            f.write(agent_code)

        print(f"Added agent '{args.name}' to agents.py")
        return 0

    def _add_tool(self, args: argparse.Namespace) -> int:
        """Add a tool to the project."""
        agents_file = Path("agents.py")
        if not agents_file.exists():
            print("Error: No agents.py found. Run 'agentforge init' first.")
            return 1

        tool_code = f'''

from agentforge import tool

@tool
def {args.name}(*args, **kwargs) -> str:
    """Add description for {args.name}."""
    # Implement tool logic here
    return "Not implemented"
'''
        with open(agents_file, "a") as f:
            f.write(tool_code)

        print(f"Added tool '{args.name}' to agents.py")
        return 0

    def _cmd_run(self, args: argparse.Namespace) -> int:
        """Run a DAG file."""
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{args.file}' not found")
            return 1

        # Load and run the module
        spec = importlib.util.spec_from_file_location("main", file_path)
        if spec is None or spec.loader is None:
            print(f"Error: Could not load file '{args.file}'")
            return 1

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        entrypoint = getattr(module, "main", None)
        if entrypoint is None or not callable(entrypoint):
            print(f"Error: No 'main' function found in {args.file}")
            return 1

        result = entrypoint()
        if inspect.isawaitable(result):
            asyncio.run(result)

        return 0

    def _cmd_version(self) -> int:
        """Show version."""
        try:
            from agentforge import __version__

            print(f"AgentForge {__version__}")
        except ImportError:
            print("AgentForge (development)")
        return 0

    def _cmd_report(self, args: argparse.Namespace) -> int:
        """Dispatch report subcommands."""
        command = getattr(args, "report_command", None)
        if command == "validate-runlog":
            return self._cmd_report_validate_runlog(args)
        if command == "daily-errors":
            return self._cmd_report_daily_errors(args)
        if command == "trends":
            return self._cmd_report_trends(args)
        if command == "pack":
            return self._cmd_report_pack(args)
        print("Error: report requires a subcommand (validate-runlog, daily-errors, trends, pack)")
        return 1

    def _cmd_report_validate_runlog(self, args: argparse.Namespace) -> int:
        """Render the run log validation markdown report."""
        from agentforge.observe.runlog import (
            generate_validate_runlog_markdown,
            validate_run_log_file,
        )

        try:
            summary = validate_run_log_file(args.input)
        except (OSError, ValueError) as exc:
            print(f"Error: failed to validate run log: {exc}")
            return 1

        markdown = generate_validate_runlog_markdown(summary)
        return self._write_report_output(args.output, markdown)

    def _cmd_report_daily_errors(self, args: argparse.Namespace) -> int:
        """Render the daily error markdown report."""
        from agentforge.observe.runlog import (
            generate_daily_errors_markdown,
            load_run_logs,
        )

        try:
            runs = load_run_logs(args.input)
        except (OSError, ValueError) as exc:
            print(f"Error: failed to load run log: {exc}")
            return 1

        markdown = generate_daily_errors_markdown(runs)
        return self._write_report_output(args.output, markdown)

    def _cmd_report_trends(self, args: argparse.Namespace) -> int:
        """Render the trends markdown report."""
        from agentforge.observe.runlog import (
            generate_trends_markdown,
            load_run_logs,
        )

        try:
            runs = load_run_logs(args.input)
        except (OSError, ValueError) as exc:
            print(f"Error: failed to load run log: {exc}")
            return 1

        markdown = generate_trends_markdown(runs)
        return self._write_report_output(args.output, markdown)

    def _cmd_report_pack(self, args: argparse.Namespace) -> int:
        """Render the full report pack (validate, daily-errors, trends, roi)."""
        from agentforge.observe.runlog import (
            generate_daily_errors_json,
            generate_daily_errors_markdown,
            generate_roi_json,
            generate_roi_markdown,
            generate_trends_json,
            generate_trends_markdown,
            generate_validate_runlog_json,
            generate_validate_runlog_markdown,
            load_run_logs,
            validate_run_log_file,
        )

        try:
            summary = validate_run_log_file(args.input)
            runs = load_run_logs(args.input)
        except (OSError, ValueError) as exc:
            print(f"Error: failed to load run log: {exc}")
            return 1

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.format == "json":
            payloads = {
                "validate-runlog.json": generate_validate_runlog_json(summary),
                "daily-errors.json": generate_daily_errors_json(runs),
                "trends.json": generate_trends_json(runs),
                "roi.json": generate_roi_json(runs),
            }
            try:
                for filename, payload in payloads.items():
                    (output_dir / filename).write_text(json.dumps(payload, indent=2))
            except OSError as exc:
                print(f"Error: failed to write report pack: {exc}")
                return 1
            return 0

        markdown_files = {
            "validate-runlog.md": generate_validate_runlog_markdown(summary),
            "daily-errors.md": generate_daily_errors_markdown(runs),
            "trends.md": generate_trends_markdown(runs),
            "roi.md": generate_roi_markdown(runs),
        }
        try:
            for filename, content in markdown_files.items():
                (output_dir / filename).write_text(content)
        except OSError as exc:
            print(f"Error: failed to write report pack: {exc}")
            return 1
        return 0

    def _cmd_bundle(self, args: argparse.Namespace) -> int:
        """Dispatch bundle subcommands."""
        command = getattr(args, "bundle_command", None)
        if command == "handoff":
            return self._cmd_bundle_handoff(args)
        print("Error: bundle requires a subcommand (handoff)")
        return 1

    def _cmd_bundle_handoff(self, args: argparse.Namespace) -> int:
        """Render the handoff bundle atomically into the output directory."""
        from agentforge.observe.handoff_generator import (
            generate_api_contract_summary_md,
            generate_architecture_md,
            generate_operations_checklist_md,
        )

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        documents = {
            "architecture.md": generate_architecture_md(args.project, args.execution_profile),
            "api-contract-summary.md": generate_api_contract_summary_md(args.project),
            "operations-checklist.md": generate_operations_checklist_md(args.project),
        }

        staging_dir = Path(
            tempfile.mkdtemp(prefix="agentforge-handoff-", dir=str(output_dir.parent))
        )
        try:
            for filename, content in documents.items():
                (staging_dir / filename).write_text(content)

            for filename in documents:
                shutil.move(str(staging_dir / filename), str(output_dir / filename))
        except OSError as exc:
            print(f"Error: failed to render handoff bundle: {exc}")
            return 1
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)

        return 0

    def _write_report_output(self, output: str, content: str) -> int:
        """Write report content to disk, creating parent directories as needed."""
        output_path = Path(output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
        except OSError as exc:
            print(f"Error: failed to write report: {exc}")
            return 1
        return 0

    def _write_file(self, path: Path, template: str, project_name: str) -> None:
        """Write a template file with project name substitution."""
        content = template.replace("{project_name}", project_name)
        with open(path, "w") as f:
            f.write(content)


def main() -> None:
    """Entry point for the CLI."""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
