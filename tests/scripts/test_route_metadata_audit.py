from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_route_metadata_audit_reports_happy_path(tmp_path: Path) -> None:
    target = tmp_path / "routes.py"
    target.write_text(
        "\n".join(
            [
                "from fastapi import APIRouter, status",
                "router = APIRouter()",
                "",
                "@router.get('/health', response_model=dict, status_code=status.HTTP_200_OK)",
                "async def health():",
                "    return {'ok': True}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "scripts/ci/route_metadata_audit.py", str(target), "--fail-on-missing"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Routes scanned: 1" in proc.stdout
    assert "Missing response_model: 0" in proc.stdout
    assert "Missing explicit status_code: 0" in proc.stdout


def test_route_metadata_audit_fails_when_metadata_is_missing(tmp_path: Path) -> None:
    target = tmp_path / "routes.py"
    target.write_text(
        "\n".join(
            [
                "from fastapi import APIRouter",
                "router = APIRouter()",
                "",
                "@router.post('/widgets')",
                "async def create_widget():",
                "    return {'ok': True}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "scripts/ci/route_metadata_audit.py", str(target), "--fail-on-missing"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "Missing response_model: 1" in proc.stdout
    assert "Missing explicit status_code: 1" in proc.stdout


def test_route_metadata_audit_targets_file_does_not_add_default_target(tmp_path: Path) -> None:
    target = tmp_path / "routes.py"
    targets_file = tmp_path / "targets.txt"
    target.write_text(
        "\n".join(
            [
                "from fastapi import APIRouter, status",
                "router = APIRouter()",
                "",
                "@router.get('/health', response_model=dict, status_code=status.HTTP_200_OK)",
                "async def health():",
                "    return {'ok': True}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    targets_file.write_text(f"{target}\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/ci/route_metadata_audit.py",
            "--targets-file",
            str(targets_file),
            "--fail-on-missing",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Routes scanned: 1" in proc.stdout
    assert "portal_api" not in proc.stdout
