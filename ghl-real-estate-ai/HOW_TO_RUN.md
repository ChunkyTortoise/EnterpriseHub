# How to Run the Demo

## Quick Start (30 seconds)

```bash
cd /Users/cave/enterprisehub/ghl-real-estate-ai
source venv/bin/activate
streamlit run streamlit_demo/app.py
```

**Then open:** http://localhost:8501

---

## What to Try

1. **Cold Lead:**
   - Type: `"Looking for a house in Austin"`
   - Watch score stay low (~0-30)

2. **Warm Lead:**
   - Type: `"I have a budget of $400k and need 3 bedrooms"`
   - Watch score jump to ~40-60
   - See property matches appear

3. **Hot Lead:**
   - Type: `"I'm pre-approved for $400k, need to move ASAP, love Hyde Park"`
   - Watch score jump to 70-90
   - See Hot-Lead tag appear

4. **Objection:**
   - Type: `"Your prices are too high"`
   - See empathetic response

---

## Stop the Demo

Press `Ctrl+C` in terminal

---

That's it! 🎉
