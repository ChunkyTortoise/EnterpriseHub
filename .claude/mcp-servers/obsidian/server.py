#!/usr/bin/env python3
"""
Obsidian MCP Server
Filesystem-based Obsidian vault integration for Claude Code.
No Obsidian desktop or plugins required.
"""
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("obsidian")

VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "")


def _get_vault() -> Path:
    """Get and validate vault path."""
    if not VAULT_PATH:
        raise RuntimeError(
            "OBSIDIAN_VAULT_PATH not set. Export it or add to .mcp.json env."
        )
    vault = Path(VAULT_PATH).resolve()
    if not vault.is_dir():
        raise RuntimeError(f"Vault directory not found: {vault}")
    return vault


def _safe_path(vault: Path, note_path: str) -> Path:
    """Resolve note path within vault, preventing traversal."""
    resolved = (vault / note_path).resolve()
    if not str(resolved).startswith(str(vault)):
        raise ValueError(f"Path traversal blocked: {note_path}")
    return resolved


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                return meta, parts[2].lstrip("\n")
            except yaml.YAMLError:
                pass
    return {}, content


def _format_note(metadata: dict, body: str) -> str:
    """Format note with YAML frontmatter."""
    if metadata:
        front = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
        return f"---\n{front}\n---\n\n{body}"
    return body


@mcp.tool()
async def obsidian_read_note(path: str) -> str:
    """Read a markdown note from the vault by relative path."""
    vault = _get_vault()
    note = _safe_path(vault, path)
    if not note.suffix:
        note = note.with_suffix(".md")
    if not note.exists():
        return json.dumps({"error": f"Note not found: {path}"})

    content = note.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(content)
    return json.dumps(
        {
            "success": True,
            "path": str(note.relative_to(vault)),
            "metadata": metadata,
            "content": body,
            "modified": datetime.fromtimestamp(note.stat().st_mtime).isoformat(),
        },
        indent=2,
        default=str,
    )


@mcp.tool()
async def obsidian_write_note(
    path: str, content: str, metadata: dict | None = None
) -> str:
    """Create or update a note. Optionally include YAML frontmatter metadata."""
    vault = _get_vault()
    note = _safe_path(vault, path)
    if not note.suffix:
        note = note.with_suffix(".md")

    note.parent.mkdir(parents=True, exist_ok=True)
    formatted = _format_note(metadata or {}, content)
    note.write_text(formatted, encoding="utf-8")

    return json.dumps(
        {
            "success": True,
            "path": str(note.relative_to(vault)),
            "size_bytes": note.stat().st_size,
            "message": f"{'Updated' if note.exists() else 'Created'} note: {path}",
        },
        indent=2,
    )


@mcp.tool()
async def obsidian_search(query: str, folder: str = "", case_sensitive: bool = False) -> str:
    """Full-text regex search across vault notes. Optionally restrict to a folder."""
    vault = _get_vault()
    search_root = _safe_path(vault, folder) if folder else vault
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return json.dumps({"error": f"Invalid regex: {e}"})

    results = []
    for md_file in search_root.rglob("*.md"):
        if md_file.name.startswith("."):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matches = []
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                matches.append({"line": i, "text": line.strip()})
        if matches:
            results.append(
                {
                    "path": str(md_file.relative_to(vault)),
                    "matches": matches[:10],
                    "total_matches": len(matches),
                }
            )
        if len(results) >= 50:
            break

    return json.dumps(
        {"success": True, "query": query, "results": results, "total_files": len(results)},
        indent=2,
    )


@mcp.tool()
async def obsidian_list_notes(folder: str = "", recursive: bool = True) -> str:
    """List notes in a vault folder."""
    vault = _get_vault()
    target = _safe_path(vault, folder) if folder else vault
    if not target.is_dir():
        return json.dumps({"error": f"Folder not found: {folder}"})

    glob_fn = target.rglob if recursive else target.glob
    notes = []
    for md_file in sorted(glob_fn("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        if md_file.name.startswith("."):
            continue
        rel = str(md_file.relative_to(vault))
        stat = md_file.stat()
        notes.append(
            {
                "path": rel,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
        if len(notes) >= 200:
            break

    return json.dumps(
        {"success": True, "folder": folder or "/", "notes": notes, "count": len(notes)},
        indent=2,
    )


@mcp.tool()
async def obsidian_get_links(path: str) -> str:
    """Extract [[wikilinks]] from a note and find backlinks to it."""
    vault = _get_vault()
    note = _safe_path(vault, path)
    if not note.suffix:
        note = note.with_suffix(".md")
    if not note.exists():
        return json.dumps({"error": f"Note not found: {path}"})

    content = note.read_text(encoding="utf-8")
    outgoing = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

    note_stem = note.stem
    backlinks = []
    for md_file in vault.rglob("*.md"):
        if md_file == note or md_file.name.startswith("."):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if f"[[{note_stem}]]" in text or f"[[{note_stem}|" in text:
            backlinks.append(str(md_file.relative_to(vault)))

    return json.dumps(
        {
            "success": True,
            "path": str(note.relative_to(vault)),
            "outgoing_links": outgoing,
            "backlinks": backlinks,
        },
        indent=2,
    )


@mcp.tool()
async def obsidian_recent_notes(limit: int = 20, folder: str = "") -> str:
    """Get most recently modified notes."""
    vault = _get_vault()
    search_root = _safe_path(vault, folder) if folder else vault

    notes = []
    for md_file in search_root.rglob("*.md"):
        if md_file.name.startswith("."):
            continue
        stat = md_file.stat()
        notes.append(
            {
                "path": str(md_file.relative_to(vault)),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size,
            }
        )

    notes.sort(key=lambda n: n["modified"], reverse=True)
    return json.dumps(
        {"success": True, "notes": notes[:limit], "total_in_vault": len(notes)},
        indent=2,
    )


@mcp.tool()
async def obsidian_create_from_template(
    template_name: str, output_path: str, variables: dict | None = None
) -> str:
    """Create a note from a vault template with {{variable}} substitution."""
    vault = _get_vault()
    template = _safe_path(vault, f"templates/{template_name}")
    if not template.suffix:
        template = template.with_suffix(".md")
    if not template.exists():
        return json.dumps({"error": f"Template not found: {template_name}"})

    content = template.read_text(encoding="utf-8")
    vars_ = variables or {}
    vars_.setdefault("date", datetime.now().strftime("%Y-%m-%d"))

    for key, value in vars_.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))

    output = _safe_path(vault, output_path)
    if not output.suffix:
        output = output.with_suffix(".md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")

    return json.dumps(
        {
            "success": True,
            "path": str(output.relative_to(vault)),
            "template": template_name,
            "variables_applied": list(vars_.keys()),
        },
        indent=2,
    )


# Import sync bridge tools (adds bridge tools to this FastMCP instance)
try:
    from sync_bridge import register_bridge_tools

    register_bridge_tools(mcp, _get_vault, _safe_path, _parse_frontmatter, _format_note)
    logger.info("Sync bridge tools registered")
except ImportError:
    logger.warning("sync_bridge module not found, bridge tools unavailable")
except Exception as e:
    logger.warning(f"Failed to load sync bridge: {e}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
