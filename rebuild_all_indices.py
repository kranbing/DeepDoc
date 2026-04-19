import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.services.vector_store import rebuild_project_vector_index

def main():
    data_dir = ROOT / "data" / "projects"
    if not data_dir.exists():
        print("No projects found.")
        return
        
    projects = [p for p in data_dir.iterdir() if p.is_dir() and (p / "meta.json").exists()]
    for p in projects:
        print(f"Rebuilding vector index for project: {p.name}")
        try:
            res = rebuild_project_vector_index(p)
            print(f"Success! Indexed {res.get('chunkCount')} chunks from {res.get('docCount')} docs.")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == '__main__':
    main()
