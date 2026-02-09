"""
Backend startup script.
Checks if the albums table is empty, and if so, seeds it from CSV data.
"""

import os
import sys
import csv
import subprocess

from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, "..", ".."))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "albums.csv")
EXTRACT_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "extract_album_data.py")


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in packages/backend/.env")
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


def read_csv(path: str) -> list[dict]:
    albums = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            albums.append({
                "title": row["title"],
                "artist": row["artist"],
                "release_year": int(row["release_year"]) if row.get("release_year") else None,
            })
    return albums


def seed_albums(client: Client, albums: list[dict]) -> None:
    if not albums:
        print("No albums to insert.")
        return
    response = client.table("albums").insert(albums).execute()
    print(f"Inserted {len(response.data)} albums into the database.")


def main():
    print("Backend startup: checking albums table...")
    client = get_supabase_client()

    if not is_albums_table_empty(client):
        print("Albums table already has data. Skipping seed.")
        return

    print("Albums table is empty. Seeding...")

    if not os.path.exists(CSV_PATH):
        run_extract_script()

    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV not found at {CSV_PATH} after extraction.")
        sys.exit(1)

    albums = read_csv(CSV_PATH)
    seed_albums(client, albums)
    print("Seeding complete.")


if __name__ == "__main__":
    main()
