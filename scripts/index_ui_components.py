
import os
from pathlib import Path
from ghl_real_estate_ai.agent_system.skills.base import registry

def index_frontend_assets():
    """
    Indexes Next.js components and Streamlit components for RAG retrieval.
    """
    print("🚀 Indexing frontend assets...")
    
    # 1. Index Next.js Components
    nextjs_root = Path("enterprise-ui/src/components")
    if nextjs_root.exists():
        for file_path in nextjs_root.glob("**/*.tsx"):
            if "ui" in file_path.parts: # Skip base ui components for now, or index them separately
                tags = ["shadcn", "base-ui"]
            else:
                tags = ["custom-component", "react"]
                
            with open(file_path, "r") as f:
                content = f.read()
                
            name = file_path.stem
            print(f"  Indexing Next.js component: {name}")
            registry.register_document(
                name=f"nextjs_{name}",
                content=content,
                tags=tags + ["nextjs", "typescript"]
            )

    # 2. Index Streamlit Components (for reference/porting)
    streamlit_root = Path("ghl_real_estate_ai/streamlit_demo/components")
    if streamlit_root.exists():
        for file_path in streamlit_root.glob("*.py"):
            with open(file_path, "r") as f:
                content = f.read()
                
            name = file_path.stem
            print(f"  Indexing Streamlit component: {name}")
            registry.register_document(
                name=f"streamlit_{name}",
                content=content,
                tags=["streamlit", "python", "legacy-reference"]
            )

    print("✅ Indexing complete.")

if __name__ == "__main__":
    index_frontend_assets()
