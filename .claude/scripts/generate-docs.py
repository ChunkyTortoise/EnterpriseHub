#!/usr/bin/env python3
"""
Auto-generate documentation for EnterpriseHub.

Generates:
- Skill catalog from MANIFEST.yaml
- API reference from MCP servers
- Hook documentation from hooks
- Metrics reports from usage data
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class DocumentationGenerator:
    """Generate comprehensive project documentation."""

    def __init__(self, root_path: Path):
        self.root = root_path
        self.docs_dir = root_path / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def generate_skill_catalog(self) -> str:
        """Generate skill catalog from MANIFEST.yaml."""
        manifest_path = self.root / ".claude" / "skills" / "MANIFEST.yaml"

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        md = f"""# Skills Catalog

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Version: {manifest['metadata']['version']}

---

## Overview

{manifest['metadata']['description']}

**Total Skills**: {len(manifest['skills'])}

---

## Skills by Category

"""

        # Group skills by category
        categories = manifest.get('categories', {})

        for category, category_data in categories.items():
            md += f"### {category.replace('-', ' ').title()}\n\n"
            md += f"{category_data.get('description', '')}\n\n"

            # Get skills in this category
            category_skills = [
                s for s in manifest['skills']
                if s['category'] == category
            ]

            for skill in category_skills:
                md += f"#### {skill['name']}\n\n"
                md += f"**Version**: {skill['version']}\n\n"
                md += f"**Description**: {skill['description']}\n\n"
                md += f"**Triggers**:\n"
                for trigger in skill.get('triggers', []):
                    md += f"- \"{trigger}\"\n"
                md += f"\n**Path**: `.claude/skills/{skill['path']}`\n\n"

                # Add time/cost savings if available
                if 'time_savings' in skill:
                    md += f"⚡ **Time Savings**: {skill['time_savings']}\n\n"
                if 'cost_savings' in skill:
                    md += f"💰 **Cost Savings**: {skill['cost_savings']}\n\n"

                md += "---\n\n"

        # Add quick reference
        md += """
## Quick Reference

| Skill | Category | Triggers | Path |
|-------|----------|----------|------|
"""

        for skill in manifest['skills']:
            triggers = skill.get('triggers', [])[:2]  # First 2 triggers
            trigger_str = ", ".join(f'"{t}"' for t in triggers)
            md += f"| {skill['name']} | {skill['category']} | {trigger_str} | `.claude/skills/{skill['path']}` |\n"

        return md

    def generate_hooks_documentation(self) -> str:
        """Generate hooks documentation."""
        hooks_dir = self.root / ".claude" / "hooks"

        md = f"""# Hooks Documentation

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Overview

Hooks provide event-driven automation in Claude Code. They execute at specific
points in the workflow to enforce rules, validate inputs, and capture learnings.

---

## Available Hooks

"""

        # Find all hook files
        hook_files = list(hooks_dir.glob("*.md")) + list(hooks_dir.glob("*.sh"))

        for hook_file in sorted(hook_files):
            if hook_file.name in ["README.md", "QUICK_REFERENCE.md"]:
                continue

            hook_name = hook_file.stem

            md += f"### {hook_name}\n\n"
            md += f"**Type**: {hook_file.suffix}\n\n"

            # Try to extract description from file
            try:
                content = hook_file.read_text()
                # Extract first comment or description
                if hook_file.suffix == ".sh":
                    lines = [l.strip() for l in content.split('\n') if l.strip().startswith('#')]
                    if lines:
                        desc = lines[0].lstrip('#').strip()
                        md += f"**Description**: {desc}\n\n"
                elif hook_file.suffix == ".md":
                    # Extract from frontmatter or first paragraph
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            try:
                                frontmatter = yaml.safe_load(parts[1])
                                if 'description' in frontmatter:
                                    md += f"**Description**: {frontmatter['description']}\n\n"
                            except:
                                pass
            except:
                pass

            md += f"**Path**: `.claude/hooks/{hook_file.name}`\n\n"
            md += "---\n\n"

        return md

    def generate_mcp_reference(self) -> str:
        """Generate MCP server reference."""
        mcp_dir = self.root / ".claude" / "mcp-profiles"

        md = f"""# MCP Server Reference

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Overview

Model Context Protocol (MCP) servers provide additional capabilities to Claude Code
through external integrations.

---

## Configured Profiles

"""

        # Read each profile
        if mcp_dir.exists():
            for profile_file in sorted(mcp_dir.glob("*.json")):
                profile_name = profile_file.stem

                try:
                    with open(profile_file) as f:
                        profile = json.load(f)

                    md += f"### {profile_name.title()}\n\n"

                    if 'description' in profile:
                        md += f"{profile['description']}\n\n"

                    if 'mcp_servers' in profile:
                        md += "**Enabled Servers**:\n\n"
                        for server, config in profile['mcp_servers'].items():
                            if config.get('enabled', True):
                                md += f"- **{server}**"
                                if 'description' in config:
                                    md += f": {config['description']}"
                                md += "\n"
                        md += "\n"

                    md += f"**Profile Path**: `.claude/mcp-profiles/{profile_file.name}`\n\n"
                    md += "---\n\n"

                except Exception as e:
                    print(f"Warning: Could not read profile {profile_file}: {e}")

        return md

    def generate_metrics_report(self) -> str:
        """Generate metrics report."""
        metrics_dir = self.root / ".claude" / "metrics"

        md = f"""# Metrics Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Overview

This report provides an overview of system usage, performance, and costs.

---

"""

        # Try to read dashboard data
        dashboard_file = metrics_dir / "dashboard-data.json"

        if dashboard_file.exists():
            try:
                with open(dashboard_file) as f:
                    data = json.load(f)

                md += "## Current Metrics\n\n"

                # Skills
                if 'skills' in data:
                    skills = data['skills']
                    md += f"### Skills Usage\n\n"
                    md += f"- **Total Invocations**: {skills.get('total_invocations', 0):,}\n"
                    md += f"- **Unique Skills**: {skills.get('unique_skills_used', 0)}\n"
                    md += f"- **Success Rate**: {skills.get('success_rate', 0):.1f}%\n\n"

                # Costs
                if 'costs' in data:
                    costs = data['costs']
                    md += f"### Cost & Efficiency\n\n"
                    md += f"- **Monthly Tokens**: {costs.get('monthly_tokens', 0):,}\n"
                    md += f"- **Budget Usage**: {costs.get('monthly_budget_pct', 0):.1f}%\n"
                    md += f"- **Estimated Cost**: ${costs.get('estimated_monthly_cost_usd', 0):.2f}/month\n\n"

                # Recommendations
                if 'recommendations' in data:
                    recs = data['recommendations']
                    if recs:
                        md += "## Recommendations\n\n"
                        for i, rec in enumerate(recs, 1):
                            md += f"{i}. {rec}\n"
                        md += "\n"

            except Exception as e:
                print(f"Warning: Could not read dashboard data: {e}")
                md += "*No metrics data available*\n\n"
        else:
            md += "*No metrics data available*\n\n"

        return md

    def generate_all(self):
        """Generate all documentation files."""
        print("📚 Generating documentation...")

        # Skill catalog
        print("  - Skill catalog...")
        skill_catalog = self.generate_skill_catalog()
        (self.docs_dir / "SKILLS_CATALOG.md").write_text(skill_catalog)

        # Hooks documentation
        print("  - Hooks documentation...")
        hooks_doc = self.generate_hooks_documentation()
        (self.docs_dir / "HOOKS.md").write_text(hooks_doc)

        # MCP reference
        print("  - MCP server reference...")
        mcp_ref = self.generate_mcp_reference()
        (self.docs_dir / "MCP_SERVERS.md").write_text(mcp_ref)

        # Metrics report
        print("  - Metrics report...")
        metrics_report = self.generate_metrics_report()
        (self.docs_dir / "METRICS.md").write_text(metrics_report)

        # Generate index
        print("  - Documentation index...")
        self.generate_index()

        print(f"✅ Documentation generated in {self.docs_dir}")

    def generate_index(self):
        """Generate documentation index."""
        md = f"""# EnterpriseHub Documentation

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Welcome to the EnterpriseHub documentation.

---

## Core Documentation

- **[CLAUDE.md](../CLAUDE.md)**: Project-specific Claude Code instructions
- **[README.md](../README.md)**: Project overview and setup

---

## Generated Documentation

### Skills & Automation

- **[Skills Catalog](SKILLS_CATALOG.md)**: Complete catalog of all available skills
- **[Hooks Documentation](HOOKS.md)**: Event-driven automation hooks

### Integration & Configuration

- **[MCP Servers](MCP_SERVERS.md)**: Model Context Protocol server reference

### Monitoring & Analytics

- **[Metrics Report](METRICS.md)**: Usage metrics and performance data

---

## Plugin Documentation

- **[Plugin README](../claude-real-estate-ai-plugin/README.md)**: Plugin overview
- **[Plugin Structure](../claude-real-estate-ai-plugin/STRUCTURE.md)**: Plugin architecture
- **[Contributing](../claude-real-estate-ai-plugin/CONTRIBUTING.md)**: Contribution guidelines

---

## Configuration Files

- **[Settings](../.claude/settings.json)**: Claude Code configuration
- **[Quality Gates](../.claude/quality-gates.yaml)**: Quality thresholds and standards
- **[Pre-commit Hooks](../.pre-commit-config.yaml)**: Git pre-commit validation

---

*Documentation auto-generated by .claude/scripts/generate-docs.py*

Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        (self.docs_dir / "INDEX.md").write_text(md)


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent.parent
    generator = DocumentationGenerator(root)
    generator.generate_all()


if __name__ == "__main__":
    main()
