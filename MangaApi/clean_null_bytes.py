
import os

def clean_null_bytes(directory):
    print(f"Starting scan in: {directory}")
    for root, dirs, files in os.walk(directory):
        # Skip venv or .git directories to save time/avoid errors
        if '.git' in dirs:
            dirs.remove('.git')
        if 'venv' in dirs:
            dirs.remove('venv')
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    if b'\x00' in content:
                        print(f"Found null bytes in: {file_path}")
                        new_content = content.replace(b'\x00', b'')
                        with open(file_path, 'wb') as f:
                            f.write(new_content)
                        print(f"Fixed: {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    # Scan the directory where the script is located (MangaApi root)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clean_null_bytes(base_dir)
