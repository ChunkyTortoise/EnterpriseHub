#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path

# Configuration
GEMINI_MD = Path("GEMINI.md")
TASK_ASSIGNMENTS = Path("AGENT_TASK_ASSIGNMENTS.md")
PROJECT_ROOT = Path(".")

class AgentDirector:
    def __init__(self):
        self.personas = self._load_personas()
        self.tasks = self._load_tasks()

    def _load_personas(self):
        if not GEMINI_MD.exists():
            return {}
        
        content = GEMINI_MD.read_text()
        personas = {}
        sections = content.split("### Task: ")
        for section in sections[1:]:
            lines = section.split("\n")
            name = lines[0].strip()
            desc = []
            for line in lines[1:]:
                if line.startswith("##"): break
                desc.append(line)
            personas[name] = "\n".join(desc).strip()
        return personas

    def _load_tasks(self):
        if not TASK_ASSIGNMENTS.exists():
            return {}
        # Simple parser for the markdown tasks
        return {} # Placeholder for now

    def list_personas(self):
        print("\n🎭 Available Agent Personas:")
        for name in self.personas:
            print(f"  - {name}")

    def get_context_for_role(self, role_name):
        if not TASK_ASSIGNMENTS.exists():
            return []
        
        content = TASK_ASSIGNMENTS.read_text()
        # Find the section that contains the role name
        sections = content.split("### **")
        target_section = None
        for s in sections:
            if role_name.lower() in s.lower():
                target_section = s
                break
        
        if not target_section:
            return []

        # Extract files from the code block under 'Files to Focus On'
        if "Files to Focus On" in target_section:
            try:
                files_block = target_section.split("```")[1].split("```")[0]
                paths = []
                for line in files_block.split("\n"):
                    if not line.strip(): continue
                    # Handle both "Category: path, path" and just "path, path"
                    parts = line.split(":")
                    p_list = parts[1] if len(parts) > 1 else parts[0]
                    paths.extend([p.strip() for p in p_list.split(",") if p.strip()])
                return paths
            except IndexError:
                return []
        return []

    def find_file(self, filename):
        if (PROJECT_ROOT / filename).exists():
            return filename
        
        # Try common subdirectories
        for parent in ["ghl_real_estate_ai", "src", "ghl_real_estate_ai/streamlit_demo", "ghl_real_estate_ai/streamlit_demo/components"]:
            if (PROJECT_ROOT / parent / filename).exists():
                return f"{parent}/{filename}"
        
        # Last resort: simple basename search (might be slow if too many files)
        # For simplicity, just return the original if not found
        return filename

    def list_skills(self):
        skills_dir = PROJECT_ROOT / "ghl_real_estate_ai/agent_system/skills"
        if not skills_dir.exists():
            return []
        return [f.stem for f in skills_dir.glob("*.py") if f.stem != "__init__"]

    def activate_persona(self, persona_name):
        if persona_name not in self.personas:
            print(f"❌ Persona '{persona_name}' not found.")
            return

        print(f"\n🚀 Activating Persona: {persona_name}")
        print("-" * 40)
        print(self.personas[persona_name])
        print("-" * 40)
        
        skills = self.list_skills()
        if skills:
            print("\n🛠️ Available Agent Skills:")
            # Filter skills that match the role (basic keyword matching)
            role_keywords = persona_name.lower().split()
            relevant_skills = [s for s in skills if any(k in s.lower() for k in role_keywords)]
            display_skills = relevant_skills if relevant_skills else skills[:5] # Fallback to first 5
            for s in display_skills:
                print(f"  - {s}")

        context_files = self.get_context_for_role(persona_name)
        if context_files:
            print("\n📂 Key Files for this Role:")
            for f in context_files:
                if "*" in f:
                    print(f"  - {f} (Glob pattern)")
                    continue
                
                actual_path = self.find_file(f)
                status = "✅ Found" if (PROJECT_ROOT / actual_path).exists() else "❌ Missing"
                print(f"  - {actual_path} ({status})")
        
        print("\n💡 Suggested next step: 'Gemini, adopt this persona and review the listed files.'")

def main():
    parser = argparse.ArgumentParser(description="EnterpriseHub Agent Director")
    parser.add_argument("command", choices=["list", "activate", "status"], help="Command to run")
    parser.add_argument("--role", help="Specific role for activate/status")

    args = parser.parse_args()
    director = AgentDirector()

    if args.command == "list":
        director.list_personas()
    elif args.command == "activate":
        if not args.role:
            print("Error: --role is required for activate")
        else:
            director.activate_persona(args.role)
    elif args.command == "status":
        print("Status tracking coming soon...")

if __name__ == "__main__":
    main()
