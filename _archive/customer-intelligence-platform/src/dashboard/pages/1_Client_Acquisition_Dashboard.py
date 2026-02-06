
import streamlit as st
import sys
from pathlib import Path

# Add components to path
components_path = Path(__file__).parent.parent / "components"
sys.path.insert(0, str(components_path))

from client_acquisition_dashboard import main

if __name__ == "__main__":
    main()
