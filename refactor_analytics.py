
import sys

file_path = "ghl_real_estate_ai/streamlit_demo/analytics.py"
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
in_main = False
for line in lines:
    if line.strip() == "def main():":
        in_main = True
        new_lines.append(line)
        continue
    
    if in_main:
        # Check if line is already indented
        if line.startswith("    ") or line.strip() == "":
            new_lines.append(line)
        elif line.strip() == "# Footer":
            # Stop indenting at footer or end of file
            # Actually we want to indent the footer too
            new_lines.append("    " + line)
        else:
            new_lines.append("    " + line)
    else:
        new_lines.append(line)

# Add calling block at the end
if not lines[-1].strip().startswith("if __name__"):
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
