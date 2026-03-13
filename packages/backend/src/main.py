"""
Album seeding orchestrator.
Runs all pipeline scripts in sequence. Each script handles its own idempotency.
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACT_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "extract_album_data.py")
STREAMING_LINKS_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "add_streaming_links.py")
ALBUM_COVERS_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "add_album_covers.py")
ALBUM_SUMMARIES_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "add_album_summaries.py")


def run_script(script_path: str, label: str) -> None:
    print(f"Running {label}...")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"{label} failed (exit code {result.returncode})")
        sys.exit(1)


def main():
    run_script(EXTRACT_SCRIPT, "album data extraction")
    run_script(STREAMING_LINKS_SCRIPT, "streaming links lookup")
    run_script(ALBUM_COVERS_SCRIPT, "album covers lookup")
    run_script(ALBUM_SUMMARIES_SCRIPT, "album summaries generation")
    print("Seeding complete.")


if __name__ == "__main__":
    main()
