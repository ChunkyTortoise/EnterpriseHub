"""
Context Engine Module
---------------------
Handles semantic chunking and prompt assembly for Gemini 1.5/2.0/3.0.
"""

from typing import List, Dict, Any
import os

class ContextEngine:
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name

    def assemble_prompt(self, task: str, context_files: List[Dict[str, str]]) -> str:
        """
        Assembles a boundary-weighted prompt.
        
        Args:
            task: The user's query.
            context_files: List of dicts with 'path' and 'content'.
        """
        system_preamble = self._get_system_preamble()
        code_context = self._format_code_context(context_files)
        final_instruction = self._get_final_instruction(task)
        
        # The "Sandwich"
        return f"{system_preamble}\n\n{code_context}\n\n{final_instruction}"

    def _get_system_preamble(self) -> str:
        return """You are the EnterpriseHub Gemini Assistant.
Focus on production-quality, secure code.
"""

    def _format_code_context(self, files: List[Dict[str, str]]) -> str:
        """
        Formats files with XML-style tags for better model delineation.
        """
        buffer = []
        for f in files:
            buffer.append(f"<file path='{f['path']}'>\n{f['content']}\n</file>")
        return "\n".join(buffer)

    def _get_final_instruction(self, task: str) -> str:
        return f"""
CRITICAL INSTRUCTION:
Task: {task}
Think step-by-step. Verify security before outputting code.
"""

    def semantic_chunk(self, file_path: str, max_chunk_size: int = 100000) -> List[str]:
        """
        Reads a file and returns it as a single chunk (for now), respecting the 1M context window.
        In a full implementation, this would use AST parsing to split strictly at class/function boundaries
        if the file exceeded the context limit.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple check: if file is huge, we might warn, but Gemini 1.5/2.0 can handle it.
            # We wrap it in a list to mimic a "list of chunks".
            return [content]
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
