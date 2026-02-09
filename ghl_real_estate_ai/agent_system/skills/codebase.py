"""
Codebase Analysis Skills.
Optimized for Gemini 2.0 with Context Caching.
"""

from pathlib import Path
from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger

from .base import skill

logger = get_logger(__name__)


@skill(name="map_codebase", tags=["architecture", "discovery"])
def map_codebase(root_dir: str = ".") -> Dict[str, Any]:
    """
    Recursively maps the codebase structure, identifying key packages and files.
    """
    structure = {}
    root = Path(root_dir)

    for path in root.rglob("*"):
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        if path.is_file():
            # Basic file info
            parts = path.relative_to(root).parts
            current = structure
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = f"{path.stat().st_size} bytes"

    return structure


@skill(name="analyze_dependencies", tags=["architecture", "security"])
def analyze_dependencies(file_path: str) -> List[str]:
    """
    Analyzes imports in a given Python file to determine dependencies.
    """
    imports = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
    except Exception as e:
        logger.error(f"Failed to analyze dependencies for {file_path}: {e}")

    return imports


@skill(name="deep_search_codebase", tags=["architecture", "discovery"])
def deep_search_codebase(query: str, root_dir: str = ".") -> List[str]:
    """
    Performs a grep-like search across the codebase for a specific pattern or query.
    """
    results = []
    root = Path(root_dir)

    for path in root.rglob("*.py"):
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        try:
            with open(path, "r") as f:
                if query.lower() in f.read().lower():
                    results.append(str(path.relative_to(root)))
        except Exception:
            pass

    return results
