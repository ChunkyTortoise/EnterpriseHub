# Claude Skills Installation Guide

This directory contains scripts to help you install Claude skills from repositories or from the local `awesome-claude-skills` directory.

## Quick Start

### Install from a Remote Repository

```bash
./install-claude-skill.sh <REPO_URL> <SKILL_NAME>
```

**Example:**
```bash
./install-claude-skill.sh https://github.com/anthropics/claude-skills.git document-skills
```

### Install from Local awesome-claude-skills Directory

```bash
./install-local-skill.sh <SKILL_NAME>
```

**Example:**
```bash
./install-local-skill.sh document-skills
```

## Manual Installation Steps

If you prefer to install manually, follow these steps:

### 1. Download/Clone the Skills Repository

```bash
git clone <REPO_URL>
cd <repo-root>
```

### 2. Create Claude Skills Directory

The script automatically detects the correct location. Claude Code uses:
- `~/.config/claude-code/skills/` (default)
- `~/.claude/skills/` (alternative)

Create it manually if needed:
```bash
mkdir -p ~/.config/claude-code/skills
# or
mkdir -p ~/.claude/skills
```

### 3. Copy the Skill

```bash
cp -R skills/<skill-name> ~/.config/claude-code/skills/
# or
cp -R awesome-claude-skills/<skill-name> ~/.config/claude-code/skills/
```

### 4. Start Claude Code

```bash
claude
```

The skill will be automatically loaded and available when relevant.

## Available Skills in This Repository

The `awesome-claude-skills` directory contains many example skills. To see what's available:

```bash
./install-local-skill.sh
```

This will list all available skills without installing anything.

## Script Features

### `install-claude-skill.sh`
- Clones any Git repository
- Auto-detects skill location in repository
- Supports multiple repository structures
- Lists available skills if the specified one isn't found
- Verifies installation

### `install-local-skill.sh`
- Installs from local `awesome-claude-skills` directory
- Lists available skills
- Quick installation without cloning

## Troubleshooting

### Skill Not Found
If a skill isn't found, the script will list available skills in the repository. Common locations:
- `skills/<skill-name>/`
- `<skill-name>/`
- `awesome-claude-skills/<skill-name>/`

### Skill Already Exists
The script will prompt before overwriting an existing skill installation.

### Wrong Directory
If skills aren't loading in Claude Code, verify the installation path:
```bash
ls ~/.config/claude-code/skills/
# or
ls ~/.claude/skills/
```

## Notes

- Skills require a `SKILL.md` file to work properly
- The skill name should match the directory name
- Skills are automatically loaded when Claude Code starts
- You can install multiple skills - they'll all be available






