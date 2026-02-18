"""Playwright UI tests for trust badge environment/data-source messaging."""

import os
import socket
import subprocess
import textwrap
import time
from pathlib import Path
from typing import Dict, Iterable

import pytest

playwright = pytest.importorskip("playwright", reason="playwright not installed")
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.integration


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "output" / "playwright"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _write_streamlit_entrypoint(tmp_path: Path, *, force_fallback: bool) -> Path:
    entrypoint = tmp_path / "streamlit_test_entrypoint.py"

    if not force_fallback:
        entrypoint.write_text(
            "import ghl_real_estate_ai.streamlit_demo.app  # noqa: F401\n",
            encoding="utf-8",
        )
        return entrypoint

    entrypoint.write_text(
        textwrap.dedent(
            """
            from types import SimpleNamespace

            from ghl_real_estate_ai.services.ghl_client import GHLClient


            async def _mock_check_health(self):
                return SimpleNamespace(status_code=500)


            async def _mock_fetch_dashboard_data(self):
                return None


            GHLClient.check_health = _mock_check_health
            GHLClient.fetch_dashboard_data = _mock_fetch_dashboard_data

            import ghl_real_estate_ai.streamlit_demo.app  # noqa: F401
            """
        ),
        encoding="utf-8",
    )
    return entrypoint


def _wait_for_streamlit(url: str, timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            import urllib.request

            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"Streamlit app did not become ready within {timeout_seconds}s: {url}")


def _start_streamlit_process(
    tmp_path: Path,
    scenario_name: str,
    env_overrides: Dict[str, str],
    *,
    force_fallback: bool,
) -> tuple[subprocess.Popen[str], Path, str]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    entrypoint = _write_streamlit_entrypoint(tmp_path, force_fallback=force_fallback)
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"
    log_path = ARTIFACT_DIR / f"{scenario_name}.log"

    env = os.environ.copy()
    env.update(
        {
            "ANTHROPIC_API_KEY": "sk-ant-test-key-for-ui",
            "GHL_API_KEY": "live_like_key_for_ui_tests",
            "GHL_LOCATION_ID": "ui-test-location",
            "JWT_SECRET_KEY": "ui-test-jwt-secret-key-with-32-plus-length",
            "GHL_WEBHOOK_SECRET": "ui-test-webhook-secret",
            "REDIS_PASSWORD": "ui-test-redis-password",
            "PYTHONUNBUFFERED": "1",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        }
    )
    env.update(env_overrides)

    command = [
        "python3",
        "-m",
        "streamlit",
        "run",
        str(entrypoint),
        "--server.headless=true",
        f"--server.port={port}",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]

    log_handle = open(log_path, "w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    process._log_handle = log_handle  # type: ignore[attr-defined]
    return process, log_path, url


def _stop_streamlit_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    finally:
        log_handle = getattr(process, "_log_handle", None)
        if log_handle:
            log_handle.close()


def _assert_badges_and_capture(url: str, expected_texts: Iterable[str], screenshot_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(url, wait_until="networkidle", timeout=120000)

        for expected in expected_texts:
            page.get_by_text(expected, exact=False).first.wait_for(timeout=120000)

        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot_path), full_page=True)
        browser.close()


@pytest.mark.parametrize(
    "scenario_name,env_overrides,force_fallback,expected_texts",
    [
        (
            "trust_badge_demo_mode",
            {"ENVIRONMENT": "demo"},
            False,
            ("Data Source: Demo Sample Data",),
        ),
        (
            "trust_badge_live_mode_fallback",
            {"ENVIRONMENT": "production"},
            True,
            ("Live Mode (Fallback)", "Data Source: Sample Data Fallback"),
        ),
    ],
)
def test_trust_badge_scenarios(
    tmp_path: Path,
    scenario_name: str,
    env_overrides: Dict[str, str],
    force_fallback: bool,
    expected_texts: Iterable[str],
) -> None:
    process, log_path, url = _start_streamlit_process(
        tmp_path,
        scenario_name,
        env_overrides,
        force_fallback=force_fallback,
    )
    screenshot_path = ARTIFACT_DIR / f"{scenario_name}.png"

    try:
        _wait_for_streamlit(url)
        _assert_badges_and_capture(url, expected_texts, screenshot_path)
    finally:
        _stop_streamlit_process(process)

    assert screenshot_path.exists(), f"Missing screenshot artifact: {screenshot_path}"
    assert log_path.exists(), f"Missing streamlit log artifact: {log_path}"
