"""
Album seeding orchestrator.
Runs all pipeline scripts in sequence. Each script handles its own idempotency.
"""

import concurrent.futures
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
        raise RuntimeError(f"{label} failed (exit code {result.returncode})")


def main():
    try:
        run_script(EXTRACT_SCRIPT, "album data extraction")

        # Streaming links must run first: substitutions replace title/artist/release_year
        # and clear summaries, so summaries must see the final metadata.
        run_script(STREAMING_LINKS_SCRIPT, "streaming links lookup")

        # Covers and summaries are independent — run them in parallel.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_covers = executor.submit(run_script, ALBUM_COVERS_SCRIPT, "album covers lookup")
            f_summaries = executor.submit(run_script, ALBUM_SUMMARIES_SCRIPT, "album summaries generation")
            for future in concurrent.futures.as_completed([f_covers, f_summaries]):
                future.result()
        print("Seeding complete.")
    except RuntimeError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
