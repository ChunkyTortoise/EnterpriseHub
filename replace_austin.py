import os


def replace_in_file(file_path, search_text, replace_text):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if search_text in content:
            new_content = content.replace(search_text, replace_text)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def global_replace(search_text, replace_text, exclude_dirs=['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
    count = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            if replace_in_file(file_path, search_text, replace_text):
                print(f"Replaced in: {file_path}")
                count += 1
    print(f"Total files updated for '{search_text}': {count}")

if __name__ == "__main__":
    global_replace("Rancho Cucamonga", "Rancho Cucamonga")
    global_replace("rancho_cucamonga", "rancho_cucamonga")
