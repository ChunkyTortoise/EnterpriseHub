
import sys

file_path = "ghl_real_estate_ai/streamlit_demo/analytics.py"
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
in_main = False
found_start = False

for line in lines:
    if line.strip() == 'st.title("📊 GHL Real Estate AI - Analytics Dashboard")':
        found_start = True
        new_lines.append("def main():\n")
        new_lines.append("    setup_ui()\n")
        new_lines.append("    " + line)
        in_main = True
        continue
    
    if in_main:
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

# Add calling block at the end
if found_start:
    new_lines.append("\n")
    new_lines.append("if __name__ == \"__main__\":\n")
    new_lines.append("    main()\n")
    new_lines.append("elif \"streamlit\" in sys.modules:\n")
    new_lines.append("    try:\n")
    new_lines.append("        from streamlit.runtime.scriptrunner import get_script_run_ctx\n")
    new_lines.append("        if get_script_run_ctx():\n")
    new_lines.append("            main()\n")
    new_lines.append("    except ImportError:\n")
    new_lines.append("        pass\n")

with open(file_path, "w") as f:
    f.writelines(new_lines)
