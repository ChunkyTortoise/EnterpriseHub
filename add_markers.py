import os
import re


def add_markers():
    test_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                if 'venv' in root or 'node_modules' in root or '.git' in root or 'advanced_rag_system/venv312' in root:
                    continue
                test_files.append(os.path.join(root, file))

    integration_keywords = ['redis', 'sqlalchemy', 'requests', 'aiohttp', 'httpx', 'database', 'db', 'integration', 'client', 'api_client']
    
    for file_path in test_files:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if '@pytest.mark.unit' in content or '@pytest.mark.integration' in content:
            continue
            
        marker = 'unit'
        if any(keyword in file_path.lower() for keyword in ['integration', 'e2e']):
            marker = 'integration'
        elif any(keyword in content.lower() for keyword in integration_keywords):
            marker = 'integration'
            
        import_marker = f'import pytest\n\n@pytest.mark.{marker}\n'
        if 'import pytest' in content:
            # Add marker after imports
            lines = content.splitlines()
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    last_import_idx = i
            
            if last_import_idx != -1:
                lines.insert(last_import_idx + 1, f'\n@pytest.mark.{marker}')
                new_content = '\n'.join(lines)
            else:
                new_content = f'@pytest.mark.{marker}\n' + content
        else:
            new_content = import_marker + content
            
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Added @pytest.mark.{marker} to {file_path}")

if __name__ == "__main__":
    add_markers()
