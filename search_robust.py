import os

def search_files(directory, keyword):
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'latin-1']
    for root, dirs, files in os.walk(directory):
        if '.git' in dirs:
            dirs.remove('.git')
        for file in files:
            file_path = os.path.join(root, file)
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        if keyword in content:
                            print(f"FOUND in {file_path} (encoding: {encoding})")
                            # Find the line
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if keyword in line:
                                    print(f"  Line {i+1}: {line.strip()}")
                            break
                except:
                    continue

if __name__ == "__main__":
    search_files('.', 'metric-circle')
    search_files('.', 'futhurs')
    search_files('.', 'change the futhurs')
