"""Regression tests for OptimizedJSONResponse.

Covers the class that caused the v1.0.31 production bug:
- Pydantic model serialization
- Dict null removal (top-level and nested)
- List handling (None items must be preserved — they are valid list elements)
- Nested object combinations
"""

import json

import pytest
from pydantic import BaseModel

from ghl_real_estate_ai.api.main import OptimizedJSONResponse


# ---------------------------------------------------------------------------
# Pydantic helpers
# ---------------------------------------------------------------------------


class SimpleModel(BaseModel):
    name: str
    score: float
    note: str | None = None


class NestedModel(BaseModel):
    id: str
    child: SimpleModel | None = None
    tags: list[str] = []


# ---------------------------------------------------------------------------
# Helper: decode rendered bytes back to a Python object
# ---------------------------------------------------------------------------


def decode(response: OptimizedJSONResponse, content) -> dict | list:
    rendered = response.render(content)
    return json.loads(rendered.decode("utf-8"))


# ---------------------------------------------------------------------------
# Pydantic model serialisation
# ---------------------------------------------------------------------------


class TestPydanticModelSerialization:
    def test_simple_model_roundtrips(self):
        model = SimpleModel(name="Alice", score=0.9)
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, model)
        assert result["name"] == "Alice"
        assert result["score"] == 0.9

    def test_none_fields_stripped_from_pydantic_model(self):
        model = SimpleModel(name="Bob", score=0.5, note=None)
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, model)
        # note is None → should be removed from output
        assert "note" not in result

    def test_set_fields_present_in_pydantic_model(self):
        model = SimpleModel(name="Carol", score=0.7, note="VIP")
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, model)
        assert result["note"] == "VIP"

    def test_nested_pydantic_model(self):
        child = SimpleModel(name="child", score=1.0)
        parent = NestedModel(id="p1", child=child)
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, parent)
        assert result["id"] == "p1"
        assert result["child"]["name"] == "child"

    def test_nested_none_pydantic_field_stripped(self):
        parent = NestedModel(id="p2", child=None)
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, parent)
        assert "child" not in result


# ---------------------------------------------------------------------------
# Dict null removal
# ---------------------------------------------------------------------------


class TestDictNullRemoval:
    def test_top_level_none_removed(self):
        content = {"a": 1, "b": None, "c": "hello"}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert "b" not in result
        assert result == {"a": 1, "c": "hello"}

    def test_nested_dict_none_removed(self):
        content = {"outer": {"inner": None, "value": 42}}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert "inner" not in result["outer"]
        assert result["outer"]["value"] == 42

    def test_all_none_values_stripped(self):
        content = {"x": None, "y": None}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert result == {}

    def test_empty_dict_passthrough(self):
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, {})
        assert result == {}

    def test_zero_false_empty_string_preserved(self):
        content = {"zero": 0, "flag": False, "empty": ""}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert result == {"zero": 0, "flag": False, "empty": ""}


# ---------------------------------------------------------------------------
# List handling — None items inside lists must be PRESERVED
# (stripping None from lists changes semantics and is a bug, tracked as issue #9)
# ---------------------------------------------------------------------------


class TestListNullHandling:
    def test_list_of_strings_passthrough(self):
        content = {"tags": ["hot", "lead"]}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert result["tags"] == ["hot", "lead"]

    def test_list_with_none_items_preserves_none(self):
        """None items inside a list are valid — they must not be silently removed."""
        content = {"items": [1, None, 3]}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert result["items"] == [1, None, 3]

    def test_empty_list_passthrough(self):
        content = {"actions": []}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert result["actions"] == []

    def test_list_of_dicts_nested_nulls_removed(self):
        content = {"leads": [{"name": "Alice", "score": None}, {"name": "Bob", "score": 0.8}]}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert "score" not in result["leads"][0]
        assert result["leads"][1]["score"] == 0.8


# ---------------------------------------------------------------------------
# Nested object combinations
# ---------------------------------------------------------------------------


class TestNestedObjects:
    def test_deeply_nested_nulls_stripped(self):
        content = {"a": {"b": {"c": None, "d": 1}}}
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert "c" not in result["a"]["b"]
        assert result["a"]["b"]["d"] == 1

    def test_mixed_list_and_dict_nesting(self):
        content = {
            "contacts": [
                {"id": "c1", "note": None},
                {"id": "c2", "note": "follow-up"},
            ],
            "total": 2,
            "cursor": None,
        }
        resp = OptimizedJSONResponse(content=None)
        result = decode(resp, content)
        assert "cursor" not in result
        assert "note" not in result["contacts"][0]
        assert result["contacts"][1]["note"] == "follow-up"
        assert result["total"] == 2

    def test_non_dict_non_list_passthrough(self):
        resp = OptimizedJSONResponse(content=None)
        assert resp.render("plain text") == b'"plain text"'
        assert resp.render(42) == b"42"
        assert resp.render(True) == b"true"
