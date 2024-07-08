#!/usr/bin/env python3
"""Check preserved source bytes without importing or executing the project."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text())
    failed = []
    for item in manifest["files"]:
        path = root / item["path"]
        if not path.is_file():
            failed.append(f"MISSING {item['path']}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            failed.append(f"CHANGED {item['path']}")
    if failed:
        print("\n".join(failed))
        return 1
    print(f"Verified: all {len(manifest['files'])} preserved files match their original bytes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
