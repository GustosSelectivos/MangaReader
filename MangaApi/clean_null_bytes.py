import os

def clean_null_bytes(directory):
    print(f"Scanning {directory} for null bytes...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    
                    if b'\x00' in content:
                        print(f"Found null bytes in: {path}")
                        clean_content = content.replace(b'\x00', b'')
                        with open(path, 'wb') as f:
                            f.write(clean_content)
                        print(f"Cleaned {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    clean_null_bytes('ApiCore')
