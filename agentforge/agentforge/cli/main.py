"""CLI main entry point for AgentForge.

This module provides the command-line interface for AgentForge,
including project scaffolding and agent creation commands.
"""

import argparse
import asyncio
import importlib.util
import inspect
import sys
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

CONFIG_TEMPLATE = '''# AgentForge Configuration
# Model settings
default_llm: openai/gpt-4o

# Execution settings
max_retries: 3
timeout: 300

# Memory settings
session_max_messages: 100
'''

README_TEMPLATE = '''# {project_name}

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
'''

REQUIREMENTS_TEMPLATE = '''agentforge>=0.2.0
pytest>=8.0
pytest-asyncio>=0.23
'''

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
            prog="agentforge",
            description="AgentForge - Lightweight multi-agent LLM orchestration"
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
        run_parser.add_argument("--monitor", "-m", action="store_true", help="Show monitoring dashboard")

        # version command
        subparsers.add_parser("version", help="Show version")

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
        self._write_file(project_path / "requirements.txt", REQUIREMENTS_TEMPLATE, args.project_name)

        if not args.no_tests:
            self._write_file(project_path / "tests" / "test_agents.py", TEST_TEMPLATE, args.project_name)

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

        agent_code = f'''

from agentforge import ConfigurableAgent

{args.name} = ConfigurableAgent(
    name="{args.name}",
    instructions="Add instructions for {args.name}.",
    llm="{args.llm}",
)
'''
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
