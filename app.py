import streamlit as st
import sys

# Log to console for debugging
print(">>> APP.PY STARTING", file=sys.stderr)

st.title("EnterpriseHub Live Demo")
st.success("App is online.")

# The simplest possible check
if st.button("Initialize Financial Engine"):
    try:
        from modules.market_pulse import render
        render()
    except Exception as e:
        st.error(f"Error: {e}")

print(">>> APP.PY FINISHED LOADING", file=sys.stderr)
