"""Tests for PromptVersionManager: versioning, diffs, tagging."""

import pytest

from devops_suite.prompt_registry.versioning import PromptVersionManager


@pytest.fixture
def version_manager():
    return PromptVersionManager()


class TestPromptVersionManager:
    def test_create_first_version(self, version_manager):
        record = version_manager.create_version(
            prompt_id="prompt-1",
            content="Hello {{name}}!",
            created_by="test-user",
        )
        assert record.version == 1
        assert record.parent_version is None
        assert "name" in record.variables

    def test_create_multiple_versions(self, version_manager):
        v1 = version_manager.create_version(
            prompt_id="prompt-1",
            content="Version 1",
            created_by="user-1",
        )
        v2 = version_manager.create_version(
            prompt_id="prompt-1",
            content="Version 2",
            created_by="user-2",
        )
        assert v1.version == 1
        assert v2.version == 2
        assert v2.parent_version == 1

    def test_get_latest_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p1", "V2")
        version_manager.create_version("p1", "V3")
        latest = version_manager.get_version("p1")
        assert latest is not None
        assert latest.version == 3
        assert latest.content == "V3"

    def test_get_specific_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p1", "V2")
        v1 = version_manager.get_version("p1", version=1)
        assert v1 is not None
        assert v1.content == "V1"

    def test_get_nonexistent_prompt(self, version_manager):
        result = version_manager.get_version("fake-id")
        assert result is None

    def test_get_nonexistent_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        result = version_manager.get_version("p1", version=99)
        assert result is None

    def test_get_all_versions(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p1", "V2")
        version_manager.create_version("p1", "V3")
        all_versions = version_manager.get_all_versions("p1")
        assert len(all_versions) == 3
        assert all_versions[0].version == 1
        assert all_versions[-1].version == 3

    def test_extract_variables_jinja2(self, version_manager):
        record = version_manager.create_version(
            "p1",
            "Hello {{user}}, you have {{count}} messages.",
        )
        assert set(record.variables) == {"user", "count"}

    def test_explicit_variables_override(self, version_manager):
        record = version_manager.create_version(
            "p1",
            "Hello {{user}}",
            variables=["custom_var"],
        )
        assert record.variables == ["custom_var"]

    def test_model_hint(self, version_manager):
        record = version_manager.create_version(
            "p1",
            "Content",
            model_hint="gpt-4o",
        )
        assert record.model_hint == "gpt-4o"

    def test_tags(self, version_manager):
        record = version_manager.create_version(
            "p1",
            "Content",
            tags=["production", "approved"],
        )
        assert "production" in record.tags
        assert "approved" in record.tags

    def test_changelog(self, version_manager):
        version_manager.create_version("p1", "V1")
        v2 = version_manager.create_version(
            "p1",
            "V2",
            changelog="Added error handling",
        )
        assert v2.changelog == "Added error handling"

    def test_diff_versions(self, version_manager):
        version_manager.create_version("p1", "Line 1\nLine 2\nLine 3")
        version_manager.create_version("p1", "Line 1\nModified Line 2\nLine 3")
        diff = version_manager.diff_versions("p1", from_v=1, to_v=2)
        assert diff is not None
        assert diff.from_version == 1
        assert diff.to_version == 2
        assert "Modified Line 2" in diff.unified_diff
        assert diff.added_lines == 1
        assert diff.removed_lines == 1

    def test_diff_nonexistent(self, version_manager):
        version_manager.create_version("p1", "V1")
        diff = version_manager.diff_versions("p1", from_v=1, to_v=99)
        assert diff is None

    def test_tag_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p1", "V2")
        success = version_manager.tag_version("p1", 1, "stable")
        assert success is True
        tagged = version_manager.get_by_tag("p1", "stable")
        assert tagged is not None
        assert tagged.version == 1

    def test_tag_moves_to_new_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p1", "V2")
        version_manager.tag_version("p1", 1, "stable")
        version_manager.tag_version("p1", 2, "stable")
        tagged = version_manager.get_by_tag("p1", "stable")
        assert tagged is not None
        assert tagged.version == 2

    def test_tag_nonexistent_version(self, version_manager):
        version_manager.create_version("p1", "V1")
        success = version_manager.tag_version("p1", 99, "tag")
        assert success is False

    def test_get_by_tag_nonexistent(self, version_manager):
        version_manager.create_version("p1", "V1")
        result = version_manager.get_by_tag("p1", "nonexistent-tag")
        assert result is None

    def test_list_prompts(self, version_manager):
        version_manager.create_version("p1", "V1")
        version_manager.create_version("p2", "V1")
        version_manager.create_version("p3", "V1")
        prompts = version_manager.list_prompts()
        assert set(prompts) == {"p1", "p2", "p3"}

    def test_multiple_prompts_isolated(self, version_manager):
        version_manager.create_version("p1", "P1 V1")
        version_manager.create_version("p2", "P2 V1")
        version_manager.create_version("p1", "P1 V2")
        p1_versions = version_manager.get_all_versions("p1")
        p2_versions = version_manager.get_all_versions("p2")
        assert len(p1_versions) == 2
        assert len(p2_versions) == 1

    def test_no_variables_extracted(self, version_manager):
        record = version_manager.create_version("p1", "Static content with no vars")
        assert record.variables == []
