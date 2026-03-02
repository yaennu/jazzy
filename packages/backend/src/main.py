"""
Backend startup script.
Checks if the albums table is empty, and if so, runs the extraction script
to populate it directly from PNG images.
"""

import os
import sys
import subprocess

from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
EXTRACT_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "extract_album_data.py")


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in packages/backend/.env.local")
        sys.exit(1)
    return create_client(url, key)


def is_albums_table_empty(client: Client) -> bool:
    response = client.table("albums").select("album_id", count="exact").limit(1).execute()
    return response.count == 0


def run_extract_script() -> None:
    print("Running album data extraction script...")
    result = subprocess.run(
        [sys.executable, EXTRACT_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"Extract script failed:\n{result.stderr}")
        sys.exit(1)


def main():
    print("Backend startup: checking albums table...")
    client = get_supabase_client()

    if not is_albums_table_empty(client):
        print("Albums table already has data. Skipping seed.")
        return

    print("Albums table is empty. Running extraction script to seed database...")
    run_extract_script()
    print("Seeding complete.")


if __name__ == "__main__":
    main()
