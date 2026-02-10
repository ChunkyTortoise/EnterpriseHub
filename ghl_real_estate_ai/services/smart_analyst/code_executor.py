"""Self-healing code executor for Smart Analyst."""
from __future__ import annotations

import asyncio
import contextlib
import io
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ghl_real_estate_ai.core.llm_client import get_llm_client
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: Optional[str] = None
    attempts: int = 1
    last_code: Optional[str] = None


class SelfHealingExecutor:
    """Executes Python code with iterative error correction via LLM."""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.llm_client = get_llm_client()

    async def execute(self, code: str, globals_dict: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        globals_dict = globals_dict or {}
        attempt = 0
        last_error = None
        current_code = textwrap.dedent(code)

        while attempt < self.max_attempts:
            attempt += 1
            output_buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(output_buffer):
                    exec(current_code, globals_dict)
                return ExecutionResult(
                    success=True,
                    output=output_buffer.getvalue(),
                    attempts=attempt,
                    last_code=current_code,
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"SelfHealingExecutor attempt {attempt} failed: {exc}")
                current_code = await self._repair_code(current_code, last_error)

        return ExecutionResult(
            success=False,
            output=output_buffer.getvalue() if 'output_buffer' in locals() else "",
            error=last_error,
            attempts=attempt,
            last_code=current_code,
        )

    async def _repair_code(self, code: str, error: str) -> str:
        """Use LLM to fix code errors with minimal edits."""
        prompt = f"""
        You are a Python debugging assistant. Fix the code based on the error.
        Return only the corrected code.

        Error:
        {error}

        Code:
        {code}
        """
        try:
            if hasattr(self.llm_client, "agenerate"):
                response = await self.llm_client.agenerate(prompt=prompt, max_tokens=400, temperature=0.2)
            else:
                response = self.llm_client.generate(prompt=prompt, max_tokens=400, temperature=0.2)
            fixed = response.content.strip() if response and response.content else code
            # Strip markdown fences
            if fixed.startswith("```"):
                fixed = fixed.split("```", 2)[1]
            return textwrap.dedent(fixed)
        except Exception as exc:
            logger.error(f"SelfHealingExecutor repair failed: {exc}")
            return code
