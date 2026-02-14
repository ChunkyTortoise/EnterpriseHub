# Obsidian MCP Server

Filesystem-based Obsidian vault integration for Claude Code. No Obsidian desktop required.

## Setup
```bash
pip install -r requirements.txt
export OBSIDIAN_VAULT_PATH=/path/to/.obsidian-vault
```

## Tools
- `obsidian_read_note` — Read note by path
- `obsidian_write_note` — Create/update with YAML frontmatter
- `obsidian_search` — Regex search across vault
- `obsidian_list_notes` — List notes in folder
- `obsidian_get_links` — Extract wikilinks
- `obsidian_recent_notes` — Recently modified notes
- `obsidian_create_from_template` — Create from template with variable substitution

## Sync Bridge
- `sync_notebook_to_vault` — NotebookLM query → vault note
- `sync_note_to_notebook` — Vault note → NotebookLM source
- `sync_study_guide` — NotebookLM study guide → structured vault note
