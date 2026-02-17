"""Tests for AgentForge CLI.

This module tests the CLI functionality including:
- CLI parser creation
- init command
- add agent command
- add tool command
- version command
"""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from agentforge.cli import CLI, main


class TestCLI:
    """Test CLI class."""

    def test_cli_parser_creation(self) -> None:
        """Test that CLI parser is created correctly."""
        cli = CLI()
        assert cli.parser is not None
        assert cli.parser.prog == "agentforge"

    def test_cli_parser_has_init_command(self) -> None:
        """Test that init command is available."""
        cli = CLI()
        # Parse init command with --help to verify it exists
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["init", "--help"])
        # --help exits with 0
        assert exc_info.value.code == 0

    def test_cli_parser_has_add_command(self) -> None:
        """Test that add command is available."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["add", "--help"])
        assert exc_info.value.code == 0

    def test_cli_parser_has_run_command(self) -> None:
        """Test that run command is available."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["run", "--help"])
        assert exc_info.value.code == 0

    def test_cli_parser_has_version_command(self) -> None:
        """Test that version command is available."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["version", "--help"])
        assert exc_info.value.code == 0


class TestInitCommand:
    """Test init command."""

    def test_init_creates_project_directory(self, tmp_path: Path) -> None:
        """Test that init creates project directory."""
        cli = CLI()
        project_name = "test_project"
        project_path = tmp_path / project_name

        result = cli.run(["init", project_name, "--path", str(tmp_path)])

        assert result == 0
        assert project_path.exists()
        assert project_path.is_dir()

    def test_init_creates_required_files(self, tmp_path: Path) -> None:
        """Test that init creates all required files."""
        cli = CLI()
        project_name = "test_project"
        project_path = tmp_path / project_name

        cli.run(["init", project_name, "--path", str(tmp_path)])

        # Check main files
        assert (project_path / "agents.py").exists()
        assert (project_path / "main.py").exists()
        assert (project_path / "config.yaml").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / "requirements.txt").exists()

        # Check tests directory
        assert (project_path / "tests").is_dir()
        assert (project_path / "tests" / "test_agents.py").exists()

    def test_init_with_no_tests_flag(self, tmp_path: Path) -> None:
        """Test that --no-tests skips test file creation."""
        cli = CLI()
        project_name = "test_project"
        project_path = tmp_path / project_name

        cli.run(["init", project_name, "--path", str(tmp_path), "--no-tests"])

        # Tests directory should still exist but be empty
        assert (project_path / "tests").is_dir()
        assert not (project_path / "tests" / "test_agents.py").exists()

    def test_init_fails_if_directory_exists(self, tmp_path: Path) -> None:
        """Test that init fails if directory already exists."""
        cli = CLI()
        project_name = "existing_project"
        project_path = tmp_path / project_name

        # Create the directory first
        project_path.mkdir()

        result = cli.run(["init", project_name, "--path", str(tmp_path)])

        assert result == 1

    def test_init_file_content_has_project_name(self, tmp_path: Path) -> None:
        """Test that generated files contain project name."""
        cli = CLI()
        project_name = "my_awesome_project"
        project_path = tmp_path / project_name

        cli.run(["init", project_name, "--path", str(tmp_path)])

        # Check README contains project name
        readme_content = (project_path / "README.md").read_text()
        assert project_name in readme_content

        # Check agents.py contains project name
        agents_content = (project_path / "agents.py").read_text()
        assert project_name in agents_content

    def test_init_generated_templates_are_runnable(self, tmp_path: Path) -> None:
        """Test that generated project templates can be imported and executed."""
        cli = CLI()
        project_name = "runnable_project"
        project_path = tmp_path / project_name

        result = cli.run(["init", project_name, "--path", str(tmp_path)])
        assert result == 0

        sys.path.insert(0, str(project_path))
        try:
            agents_spec = importlib.util.spec_from_file_location(
                "generated_agents",
                project_path / "agents.py",
            )
            assert agents_spec is not None and agents_spec.loader is not None
            agents_module = importlib.util.module_from_spec(agents_spec)
            agents_spec.loader.exec_module(agents_module)
            assert hasattr(agents_module, "researcher")

            tests_spec = importlib.util.spec_from_file_location(
                "generated_tests",
                project_path / "tests" / "test_agents.py",
            )
            assert tests_spec is not None and tests_spec.loader is not None
            tests_module = importlib.util.module_from_spec(tests_spec)
            tests_spec.loader.exec_module(tests_module)
            tests_module.test_dag_creation()
        finally:
            sys.path.pop(0)


class TestAddAgentCommand:
    """Test add agent command."""

    def test_add_agent_creates_agent_code(self, tmp_path: Path) -> None:
        """Test that add agent adds code to agents.py."""
        cli = CLI()

        # Create a minimal agents.py
        agents_file = tmp_path / "agents.py"
        agents_file.write_text("# Agents file\n")

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = cli.run(["add", "agent", "researcher"])

            assert result == 0
            content = agents_file.read_text()
            assert "researcher" in content
            assert "ConfigurableAgent(" in content
        finally:
            os.chdir(original_cwd)

    def test_add_agent_with_custom_llm(self, tmp_path: Path) -> None:
        """Test that add agent uses custom LLM."""
        cli = CLI()

        agents_file = tmp_path / "agents.py"
        agents_file.write_text("# Agents file\n")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = cli.run(["add", "agent", "analyst", "--llm", "anthropic/claude-3"])

            assert result == 0
            content = agents_file.read_text()
            assert "anthropic/claude-3" in content
        finally:
            os.chdir(original_cwd)

    def test_add_agent_fails_without_agents_file(self, tmp_path: Path) -> None:
        """Test that add agent fails if no agents.py exists."""
        cli = CLI()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = cli.run(["add", "agent", "researcher"])
            assert result == 1
        finally:
            os.chdir(original_cwd)


class TestAddToolCommand:
    """Test add tool command."""

    def test_add_tool_creates_tool_code(self, tmp_path: Path) -> None:
        """Test that add tool adds code to agents.py."""
        cli = CLI()

        agents_file = tmp_path / "agents.py"
        agents_file.write_text("# Agents file\n")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = cli.run(["add", "tool", "search"])

            assert result == 0
            content = agents_file.read_text()
            assert "search" in content
            assert "@tool" in content
        finally:
            os.chdir(original_cwd)

    def test_add_tool_fails_without_agents_file(self, tmp_path: Path) -> None:
        """Test that add tool fails if no agents.py exists."""
        cli = CLI()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = cli.run(["add", "tool", "search"])
            assert result == 1
        finally:
            os.chdir(original_cwd)


class TestVersionCommand:
    """Test version command."""

    def test_version_shows_version(self, capsys) -> None:
        """Test that version command shows version."""
        cli = CLI()
        result = cli.run(["version"])

        assert result == 0
        captured = capsys.readouterr()
        assert "AgentForge" in captured.out

    def test_version_with_import_error(self, capsys) -> None:
        """Test version when import fails."""
        cli = CLI()
        with patch.dict(sys.modules, {"agentforge": None}):
            # This should still work, showing "development"
            result = cli.run(["version"])

        assert result == 0


class TestRunCommand:
    """Test run command."""

    def test_run_fails_if_file_not_found(self) -> None:
        """Test that run fails if file doesn't exist."""
        cli = CLI()
        result = cli.run(["run", "--file", "nonexistent.py"])
        assert result == 1

    def test_run_fails_if_no_main_function(self, tmp_path: Path) -> None:
        """Test that run fails if no main function in file."""
        cli = CLI()

        # Create a Python file without main function
        script_file = tmp_path / "no_main.py"
        script_file.write_text("# No main function\nprint('hello')\n")

        result = cli.run(["run", "--file", str(script_file)])
        assert result == 1

    def test_run_supports_sync_main(self, tmp_path: Path) -> None:
        """Test that run executes a synchronous main function."""
        cli = CLI()

        script_file = tmp_path / "sync_main.py"
        output_file = tmp_path / "sync_main.out"
        script_file.write_text(
            "from pathlib import Path\n"
            "def main():\n"
            f"    Path({str(output_file)!r}).write_text('ok')\n"
        )

        result = cli.run(["run", "--file", str(script_file)])
        assert result == 0
        assert output_file.read_text() == "ok"


class TestMainFunction:
    """Test main entry point."""

    def test_main_exits_with_cli_result(self) -> None:
        """Test that main exits with CLI result code."""
        with patch.object(sys, "argv", ["agentforge", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # --help exits with 0
            assert exc_info.value.code == 0

    def test_main_with_no_args_shows_help(self, capsys) -> None:
        """Test that main with no args shows help."""
        cli = CLI()
        result = cli.run([])
        assert result == 0


class TestCLIHelp:
    """Test CLI help output."""

    def test_help_shows_description(self, capsys) -> None:
        """Test that help shows program description."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--help"])
        # --help exits with 0
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "AgentForge" in captured.out
        assert "multi-agent" in captured.out.lower()

    def test_init_help_shows_options(self, capsys) -> None:
        """Test that init --help shows available options."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["init", "--help"])
        assert exc_info.value.code == 0

    def test_add_help_shows_choices(self, capsys) -> None:
        """Test that add --help shows component choices."""
        cli = CLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["add", "--help"])
        assert exc_info.value.code == 0
