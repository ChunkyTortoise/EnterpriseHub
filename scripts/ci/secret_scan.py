#!/usr/bin/env python3
"""Fail when tracked text files contain real-looking secret values."""

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SCAN_SUFFIXES = {
    ".env",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "__tests__",
    "node_modules",
    "tests",
}

PLACEHOLDER_WORDS = (
    "changeme",
    "dummy",
    "demo",
    "example",
    "fake",
    "placeholder",
    "replace",
    "sample",
    "test",
    "your",
    "xxx",
)


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]


PATTERNS = [
    SecretPattern("openrouter_api_key", re.compile(r"sk-or-v1-[A-Za-z0-9]{32,}")),
    SecretPattern("anthropic_api_key", re.compile(r"sk-ant-[A-Za-z0-9._-]{20,}")),
    SecretPattern("openai_project_key", re.compile(r"sk-proj-[A-Za-z0-9._-]{20,}")),
    SecretPattern("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    SecretPattern("stripe_live_secret", re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b")),
    SecretPattern("stripe_webhook_secret", re.compile(r"\bwhsec_[A-Za-z0-9]{20,}\b")),
    SecretPattern("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")),
    SecretPattern("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    SecretPattern("private_key_block", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    SecretPattern(
        "credential_assignment",
        re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"\n]{24,}['\"]"),
    ),
]


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    pattern_name: str
    value: str


def tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files"], check=True, capture_output=True, text=True)
    return [Path(line) for line in result.stdout.splitlines() if line]


def should_scan(path: Path, requested_roots: tuple[Path, ...]) -> bool:
    if not path.exists() or not path.is_file():
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name.startswith("test_") or ".test." in path.name or path.name.endswith("_test.py"):
        return False
    if requested_roots and not any(path == root or root in path.parents for root in requested_roots):
        return False
    return path.suffix in SCAN_SUFFIXES or path.name.startswith(".env")


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    if any(word in lowered for word in PLACEHOLDER_WORDS):
        return True
    return value.startswith("<") and value.endswith(">")


def mask(value: str) -> str:
    if len(value) <= 12:
        return "<redacted>"
    return f"{value[:6]}...{value[-4:]}"


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return findings

    for line_number, line in enumerate(lines, start=1):
        for pattern in PATTERNS:
            for match in pattern.regex.finditer(line):
                value = match.group(0)
                if is_placeholder(value):
                    continue
                findings.append(Finding(path, line_number, pattern.name, value))
    return findings


def scan(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", help="Optional tracked-file roots to scan.")
    args = parser.parse_args()

    roots = tuple(Path(root) for root in args.roots)
    paths = [path for path in tracked_files() if should_scan(path, roots)]
    findings = scan(paths)

    if findings:
        print("Secret scan failed:")
        for finding in findings:
            print(f"- {finding.path}:{finding.line_number} {finding.pattern_name} {mask(finding.value)}")
        print("\nReplace real-looking values with placeholders and rotate any exposed credentials.")
        return 1

    print(f"Secret scan passed ({len(paths)} tracked text files scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
