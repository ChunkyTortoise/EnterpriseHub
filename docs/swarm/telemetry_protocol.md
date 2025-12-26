# 📡 Telemetry Protocol: Inter-Agent Handoffs

To prevent context drift and ensure 100% execution precision, all Strike Team Beta agents must use the following header when passing information to the next agent or the Conductor.

## Handoff Template

```markdown
### 📡 TELEMETRY BLOCK
- **SOURCE_AGENT**: [Painter | Builder | Scribe | Architect | Auditor]
- **TARGET_AGENT**: [Conductor | Auditor | User]
- **STATUS**: [SUCCESS | BLOCKED | REVISION_NEEDED]
- **OUTPUT_PATH**: [file:///path/to/asset_or_code]
- **DNA_ANCHOR**: [Skill from PORTFOLIO.md being expressed]
- **REASONING_SUMMARY**:
    - [Bullet 1: Why this decision was made]
    - [Bullet 2: Any assumptions made]
- **PROMPT_METADATA**: [Exact Gemini prompt used, if applicable]
```

## Usage Rules
1. **Mandatory**: Every turn must conclude with this block.
2. **Persistence**: The Conductor will aggregate these blocks into the `handoff_script.py` or a dedicated log.
3. **Verification**: The Auditor will cross-reference the `DNA_ANCHOR` against the `PORTFOLIO.md` to ensure truthfulness.
