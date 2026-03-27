import os

def search_everywhere(target):
    for root, dirs, files in os.walk('.'):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if target in content:
                        print(f"Found '{target}' in {path}")
            except Exception:
                pass

if __name__ == "__main__":
    search_everywhere('metric-circle')
    search_everywhere("Seeker's Unique Styles")
    search_everywhere('conic-gradient')
    search_everywhere('futhurs')
