"""Unit tests for PromptTemplateManager — CRUD, rendering, variable extraction."""

from __future__ import annotations

import pytest

from devops_suite.prompt_registry.templates import PromptTemplateManager


@pytest.fixture
def mgr():
    return PromptTemplateManager()


class TestTemplateRegistration:
    def test_register_template(self, mgr):
        info = mgr.register("t1", "Greeting", "Hello {{ name }}", "A greeting")
        assert info.template_id == "t1"
        assert info.name == "Greeting"
        assert "name" in info.variables

    def test_list_templates(self, mgr):
        mgr.register("t1", "A", "Hello {{ name }}")
        mgr.register("t2", "B", "Bye {{ user }}")
        assert len(mgr.list_templates()) == 2

    def test_get_template(self, mgr):
        mgr.register("t1", "A", "Hello {{ name }}")
        info = mgr.get_template("t1")
        assert info is not None
        assert info.name == "A"

    def test_get_nonexistent_template(self, mgr):
        assert mgr.get_template("missing") is None

    def test_delete_template(self, mgr):
        mgr.register("t1", "A", "Hello")
        assert mgr.delete_template("t1") is True
        assert mgr.get_template("t1") is None

    def test_delete_nonexistent_returns_false(self, mgr):
        assert mgr.delete_template("missing") is False


class TestTemplateRendering:
    def test_render_simple(self, mgr):
        mgr.register("t1", "A", "Hello {{ name }}!")
        result = mgr.render("t1", {"name": "World"})
        assert result == "Hello World!"

    def test_render_multiple_variables(self, mgr):
        mgr.register("t1", "A", "{{ greeting }} {{ name }}, welcome to {{ place }}.")
        result = mgr.render("t1", {"greeting": "Hi", "name": "John", "place": "Home"})
        assert result == "Hi John, welcome to Home."

    def test_render_missing_template_raises(self, mgr):
        with pytest.raises(KeyError, match="not found"):
            mgr.render("missing", {})

    def test_render_missing_variable_renders_empty(self, mgr):
        mgr.register("t1", "A", "Hello {{ name }}")
        # Jinja2 default Environment replaces undefined with empty string
        result = mgr.render("t1", {})
        assert result == "Hello "


class TestVariableExtraction:
    def test_simple_variable(self, mgr):
        vars = mgr.extract_variables("Hello {{ name }}")
        assert "name" in vars

    def test_multiple_variables(self, mgr):
        vars = mgr.extract_variables("{{ a }} and {{ b }} and {{ c }}")
        assert sorted(vars) == ["a", "b", "c"]

    def test_no_variables(self, mgr):
        vars = mgr.extract_variables("No variables here.")
        assert vars == []

    def test_duplicate_variables(self, mgr):
        vars = mgr.extract_variables("{{ x }} and {{ x }}")
        assert vars == ["x"]  # deduplicated


class TestValidation:
    def test_valid_template(self, mgr):
        mgr.register("t1", "A", "Hello {{ name }}")
        errors = mgr.validate("t1", {"name": "John"})
        assert errors == []

    def test_missing_variable(self, mgr):
        mgr.register("t1", "A", "{{ greeting }} {{ name }}")
        errors = mgr.validate("t1", {"greeting": "Hi"})
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_nonexistent_template(self, mgr):
        errors = mgr.validate("missing", {})
        assert len(errors) == 1
        assert "not found" in errors[0]
