#!/usr/bin/env python3
"""
Check all Wikipedia URLs in album/artist summaries for soft-404s.

Usage (from project root):
    python3 scripts/check_wikipedia_urls.py

Outputs a dry-run report and writes /tmp/broken_wikipedia_urls.json
for use by fix_wikipedia_urls.py.
"""

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

CONCURRENCY = 5
USER_AGENT = "jazzy-wiki-checker/1.0"
BROKEN_URLS_FILE = "/tmp/broken_wikipedia_urls.json"
SOFT_404_MARKER = "Wikipedia does not have an article with this exact name"


def query_db(sql: str) -> list[dict]:
    """Run a SQL query against the linked Supabase project via the CLI."""
    result = subprocess.run(
        ["npx", "supabase", "db", "query", "--linked", "--", sql],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"DB query failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    outer = json.loads(result.stdout)
    return outer.get("rows", [])


def extract_wikipedia_urls(html: str) -> list[str]:
    """Return all Wikipedia href values found in an HTML string."""
    return re.findall(r'href="(https://en\.wikipedia\.org/wiki/[^"]+)"', html or "")


def check_url(url: str) -> tuple[str, bool]:
    """Return (url, is_missing) — True if page is a soft-404 or hard error."""
    for _ in range(2):
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "20", "-A", USER_AGENT, url],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
        if result.returncode == 28:
            continue  # timeout — retry once
        if result.returncode != 0:
            return url, True
        return url, SOFT_404_MARKER in result.stdout
    return url, True  # both attempts timed out


def collect_urls(records: list[dict]) -> dict[str, list[dict]]:
    """Map each unique Wikipedia URL to the album records that reference it."""
    url_to_albums: dict[str, list[dict]] = {}
    for rec in records:
        album_id = rec.get("album_id")
        title = rec.get("title", "")
        artist = rec.get("artist", "")
        for field in ("artist_summary", "album_summary"):
            for url in extract_wikipedia_urls(rec.get(field) or ""):
                url_to_albums.setdefault(url, []).append(
                    {"album_id": album_id, "title": title, "artist": artist, "field": field}
                )
    return url_to_albums


def check_all(url_to_albums: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Return subset of url_to_albums containing only missing-article URLs."""
    unique_urls = list(url_to_albums.keys())
    total = len(unique_urls)
    print(f"Found {total} unique Wikipedia URLs — checking with {CONCURRENCY} workers...\n")

    broken: dict[str, list[dict]] = {}
    checked = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(check_url, url): url for url in unique_urls}
        for future in as_completed(futures):
            url, is_missing = future.result()
            checked += 1
            if checked % 50 == 0:
                print(f"  Progress: {checked}/{total}", flush=True)
            if is_missing:
                broken[url] = url_to_albums[url]

    return broken


def print_report(broken: dict[str, list[dict]], total_checked: int) -> None:
    """Print a human-readable dry-run report."""
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"DRY RUN — {len(broken)} missing articles found across {total_checked} checked")
    print(f"{sep}\n")

    if not broken:
        print("No missing Wikipedia articles found.")
        return

    for url in sorted(broken):
        print(f"  MISSING  {url}")
        for src in broken[url]:
            print(
                f"           -> [{src['field']}] {src['artist']}"
                f" — {src['title']}  ({src['album_id']})"
            )
        print()


def main() -> None:
    """Entry point."""
    sql = (
        "SELECT album_id, title, artist, artist_summary, album_summary "
        "FROM albums WHERE artist_summary IS NOT NULL OR album_summary IS NOT NULL;"
    )
    print("Querying database...")
    records = query_db(sql)
    print(f"Loaded {len(records)} album records")

    url_to_albums = collect_urls(records)
    broken = check_all(url_to_albums)

    print_report(broken, len(url_to_albums))

    if broken:
        output = {"broken_urls": list(broken.keys()), "url_to_albums": broken}
        with open(BROKEN_URLS_FILE, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
        print(f"Results saved to {BROKEN_URLS_FILE}")
        print("Run scripts/fix_wikipedia_urls.py to apply fixes.")


if __name__ == "__main__":
    main()
