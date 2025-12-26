import os


def generate_handoff():
    workspace_root = "/Users/Cave/Desktop/enterprise-hub/EnterpriseHub"
    app_data_dir = "/Users/Cave/.gemini/antigravity/brain/6f6ded6c-68dc-44bf-a16e-9a64d5d12c22"

    handoff_text = "# P-O RESUME: Strike Team Beta Deployment\n\n"
    handoff_text += "## 🚀 CONTEXT\n"
    handoff_text += "You are entering Phase 5 of the EnterpriseHub evolution. The Visual 4.0 'Cinematic UI' foundation is implemented. Goal: Transition to Production Readiness and Advanced Agency.\n\n"

    artifacts = [
        "task.md",
        "implementation_plan.md",
        "COMPREHENSIVE_GAMEPLAN.md",
        "agent_personas.md",
    ]

    handoff_text += "## 📂 STATE ARTIFACTS\n"
    for art in artifacts:
        path = os.path.join(app_data_dir, art)
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
                handoff_text += f"### {art}\n```markdown\n{content}\n```\n\n"

    handoff_text += "## 🛠️ RECENT CODE CHANGES\n"
    code_files = ["utils/ui.py", "app.py"]
    for cf in code_files:
        path = os.path.join(workspace_root, cf)
        if os.path.exists(path):
            # Just summarize the file stats/headers for brevity in handoff
            handoff_text += f"- `{cf}`: Updated with Cinematic UI v4.0 elements (Gradients, Animations, Fixed Layout Helpers).\n"

    handoff_text += "\n## 🎯 IMMEDIATE MISSION\n"
    handoff_text += "1. Read the artifacts above.\n"
    handoff_text += "2. Activate 'Strike Team Beta' (Strategy, Interaction, Agentic, Content).\n"
    handoff_text += "3. Execute Phase 4 completion (Mesh Gradients) and begin Phase 5 (Authentication UI & Memory).\n"

    print(handoff_text)


if __name__ == "__main__":
    generate_handoff()
