"""
Sync Bridge: Obsidian <-> NotebookLM
Adds bridge tools to the Obsidian MCP server for bidirectional sync.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# Add project root for notebooklm import
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(root_dir)

try:
    from notebooklm import NotebookLMClient
except ImportError:
    NotebookLMClient = None
    logger.warning("notebooklm-py not installed, sync bridge tools will be limited")

_nlm_client = None


async def _get_nlm_client():
    """Lazy init NotebookLM client."""
    global _nlm_client
    if _nlm_client is not None:
        return _nlm_client
    if NotebookLMClient is None:
        raise RuntimeError("notebooklm-py not installed. Run: pip install notebooklm-py")
    _nlm_client = await NotebookLMClient.from_storage()
    return _nlm_client


def _load_sync_map(vault: Path) -> dict:
    """Load sync state tracking."""
    sync_file = vault / ".sync-map.json"
    if sync_file.exists():
        return json.loads(sync_file.read_text(encoding="utf-8"))
    return {"syncs": []}


def _save_sync_map(vault: Path, sync_map: dict):
    """Save sync state tracking."""
    sync_file = vault / ".sync-map.json"
    sync_file.write_text(json.dumps(sync_map, indent=2, default=str), encoding="utf-8")


def register_bridge_tools(mcp, get_vault: Callable, safe_path: Callable, parse_frontmatter: Callable, format_note: Callable):
    """Register sync bridge tools on the Obsidian MCP server."""

    @mcp.tool()
    async def sync_notebook_to_vault(
        notebook_id: str,
        query: str,
        output_path: str,
        include_citations: bool = True,
    ) -> str:
        """Query a NotebookLM notebook and save the answer as a vault note."""
        vault = get_vault()
        client = await _get_nlm_client()

        result = await client.chat.ask(notebook_id=notebook_id, query=query)

        metadata = {
            "type": "notebooklm-sync",
            "source_notebook": notebook_id,
            "query": query,
            "synced_at": datetime.now().isoformat(),
            "tags": ["sync", "notebooklm"],
        }

        body_parts = [f"# {query}\n", result.answer]
        if include_citations and result.references:
            body_parts.append("\n\n## Citations")
            for i, ref in enumerate(result.references, 1):
                body_parts.append(f"{i}. {ref}")

        body_parts.append(f"\n\n---\n*Synced from NotebookLM on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        note = safe_path(vault, output_path)
        if not note.suffix:
            note = note.with_suffix(".md")
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(format_note(metadata, "\n".join(body_parts)), encoding="utf-8")

        # Track sync
        sync_map = _load_sync_map(vault)
        sync_map["syncs"].append({
            "direction": "nlm_to_vault",
            "notebook_id": notebook_id,
            "vault_path": str(note.relative_to(vault)),
            "query": query,
            "synced_at": datetime.now().isoformat(),
        })
        _save_sync_map(vault, sync_map)

        return json.dumps({
            "success": True,
            "path": str(note.relative_to(vault)),
            "answer_length": len(result.answer),
            "citations": len(result.references) if result.references else 0,
        }, indent=2)

    @mcp.tool()
    async def sync_note_to_notebook(
        note_path: str,
        notebook_id: str,
        title: str = "",
    ) -> str:
        """Push a vault note as a text source to a NotebookLM notebook."""
        vault = get_vault()
        client = await _get_nlm_client()

        note = safe_path(vault, note_path)
        if not note.suffix:
            note = note.with_suffix(".md")
        if not note.exists():
            return json.dumps({"error": f"Note not found: {note_path}"})

        content = note.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(content)
        source_title = title or metadata.get("title", note.stem)

        source = await client.sources.add_text(
            notebook_id, text=body, title=source_title
        )

        # Track sync
        sync_map = _load_sync_map(vault)
        sync_map["syncs"].append({
            "direction": "vault_to_nlm",
            "notebook_id": notebook_id,
            "vault_path": str(note.relative_to(vault)),
            "source_id": source.id,
            "synced_at": datetime.now().isoformat(),
        })
        _save_sync_map(vault, sync_map)

        return json.dumps({
            "success": True,
            "source_id": source.id,
            "notebook_id": notebook_id,
            "note_path": str(note.relative_to(vault)),
            "title": source_title,
            "content_length": len(body),
        }, indent=2)

    @mcp.tool()
    async def sync_study_guide(
        notebook_id: str,
        output_path: str,
        notebook_title: str = "Notebook",
    ) -> str:
        """Generate a NotebookLM study guide and save as a structured vault note."""
        vault = get_vault()
        client = await _get_nlm_client()

        guide = await client.artifacts.get_guide(notebook_id=notebook_id)

        metadata = {
            "type": "study-guide",
            "source_notebook": notebook_id,
            "notebook_title": notebook_title,
            "generated_at": datetime.now().isoformat(),
            "tags": ["study-guide", "notebooklm", "training"],
        }

        body = f"# Study Guide: {notebook_title}\n\n{guide}\n\n---\n*Generated from NotebookLM on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"

        note = safe_path(vault, output_path)
        if not note.suffix:
            note = note.with_suffix(".md")
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(format_note(metadata, body), encoding="utf-8")

        # Track sync
        sync_map = _load_sync_map(vault)
        sync_map["syncs"].append({
            "direction": "nlm_to_vault",
            "notebook_id": notebook_id,
            "vault_path": str(note.relative_to(vault)),
            "type": "study_guide",
            "synced_at": datetime.now().isoformat(),
        })
        _save_sync_map(vault, sync_map)

        return json.dumps({
            "success": True,
            "path": str(note.relative_to(vault)),
            "guide_length": len(str(guide)),
            "notebook_title": notebook_title,
        }, indent=2)

    logger.info("Sync bridge tools registered: sync_notebook_to_vault, sync_note_to_notebook, sync_study_guide")
