from __future__ import annotations

from pathlib import Path

from scripts.ci.secret_scan import is_placeholder, scan_file


def test_secret_scan_flags_real_openrouter_key(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text('OPENROUTER_API_KEY="sk-or-v1-1234567890abcdef1234567890abcdef"', encoding="utf-8")

    findings = scan_file(path)

    assert len(findings) == 1
    assert findings[0].pattern_name == "openrouter_api_key"


def test_secret_scan_allows_angle_bracket_placeholders() -> None:
    assert is_placeholder("<OPENROUTER_API_KEY>")


def test_secret_scan_allows_test_anthropic_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "ci.yml"
    path.write_text("ANTHROPIC_API_KEY: sk-ant-test-fake-key-for-testing-only", encoding="utf-8")

    assert scan_file(path) == []
