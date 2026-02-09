#!/usr/bin/env python3
"""
Bare Except Clause Finder and Fixer

Identifies all bare except: clauses in the codebase and generates
a report with recommendations for specific exception handling.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

def find_bare_excepts(file_path: str) -> List[Dict[str, any]]:
    """Find all bare except clauses in a Python file."""
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            # Match bare except: or except Exception:
            if re.match(r'^\s+except\s*:\s*$', line) or re.match(r'^\s+except\s+Exception\s*:\s*$', line):
                # Get context (previous 3 lines and next 3 lines)
                start = max(0, i - 4)
                end = min(len(lines), i + 3)
                context = ''.join(lines[start:end])
                
                results.append({
                    'line': i,
                    'code': line.strip(),
                    'context': context,
                    'type': 'bare' if 'except:' in line else 'generic'
                })
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return results

def scan_directory(root_dir: str, exclude_dirs: List[str] = None) -> Dict[str, List[Dict]]:
    """Scan directory for Python files with bare except clauses."""
    if exclude_dirs is None:
        exclude_dirs = ['venv', '.venv', '__pycache__', '.git', 'node_modules', '_archive']
    
    results = {}
    root_path = Path(root_dir)
    
    for py_file in root_path.rglob('*.py'):
        # Skip excluded directories
        if any(excluded in str(py_file) for excluded in exclude_dirs):
            continue
            
        bare_excepts = find_bare_excepts(str(py_file))
        if bare_excepts:
            rel_path = py_file.relative_to(root_path)
            results[str(rel_path)] = bare_excepts
            
    return results

def generate_report(results: Dict[str, List[Dict]]) -> str:
    """Generate markdown report of findings."""
    total_files = len(results)
    total_issues = sum(len(issues) for issues in results.values())
    
    report = f"""# Bare Except Clause Audit Report

## Summary
- **Total Files with Issues:** {total_files}
- **Total Bare Except Clauses:** {total_issues}

## Priority Files (Most Issues)

"""
    
    # Sort files by number of issues
    sorted_files = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
    
    for file_path, issues in sorted_files[:20]:  # Top 20 files
        report += f"\n### `{file_path}` ({len(issues)} issues)\n\n"
        
        for issue in issues:
            report += f"**Line {issue['line']}:** `{issue['code']}`\n"
            report += f"```python\n{issue['context']}```\n\n"
            
            # Suggest fix based on context
            if 'json' in issue['context'].lower():
                report += "**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`\n\n"
            elif 'http' in issue['context'].lower() or 'request' in issue['context'].lower():
                report += "**Suggested Fix:** `except (httpx.HTTPError, ConnectionError) as e:`\n\n"
            elif 'file' in issue['context'].lower() or 'open(' in issue['context'].lower():
                report += "**Suggested Fix:** `except (IOError, FileNotFoundError) as e:`\n\n"
            else:
                report += "**Suggested Fix:** `except Exception as e:` + add logging\n\n"
    
    return report

if __name__ == "__main__":
    import sys
    
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"Scanning {root_dir} for bare except clauses...")
    results = scan_directory(root_dir)
    
    report = generate_report(results)
    
    # Write report
    output_file = "bare_except_audit.md"
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport written to {output_file}")
    print(f"Found {sum(len(issues) for issues in results.values())} bare except clauses in {len(results)} files")
