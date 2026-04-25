#!/usr/bin/env python3
"""
Strip broken Wikipedia <a> tags from album/artist summaries.

Reads /tmp/broken_wikipedia_urls.json produced by check_wikipedia_urls.py,
fetches current summaries from the DB, applies fixes, and runs the UPDATEs.

Usage (from project root):
    python3 scripts/check_wikipedia_urls.py   # produces broken_wikipedia_urls.json
    python3 scripts/fix_wikipedia_urls.py      # applies fixes to the DB
"""

import json
import re
import subprocess
import sys

BROKEN_URLS_FILE = "/tmp/broken_wikipedia_urls.json"


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


def execute_sql(sql: str) -> None:
    """Execute a SQL statement against the linked Supabase project via the CLI."""
    result = subprocess.run(
        ["npx", "supabase", "db", "query", "--linked", "--", sql],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"DB execute failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def strip_broken_links(html: str, broken_urls: set[str]) -> str:
    """Replace <a href="BROKEN">text</a> with just text for each broken URL."""
    for url in broken_urls:
        escaped = re.escape(url)
        html = re.sub(
            rf'<a\s+href="{escaped}">(.*?)</a>',
            r"\1",
            html,
            flags=re.DOTALL,
        )
    return html


def escape_sql_string(s: str) -> str:
    """Escape a string for use in a SQL single-quoted literal."""
    return s.replace("'", "''")


def build_update(rec: dict, broken_urls: set[str]) -> str | None:
    """Return an UPDATE statement for a record, or None if nothing changed."""
    album_id = rec.get("album_id")
    original_artist = rec.get("artist_summary") or ""
    original_album = rec.get("album_summary") or ""
    fixed_artist = strip_broken_links(original_artist, broken_urls)
    fixed_album = strip_broken_links(original_album, broken_urls)

    if fixed_artist == original_artist and fixed_album == original_album:
        return None

    set_clauses = []
    if fixed_artist != original_artist:
        set_clauses.append(f"artist_summary = '{escape_sql_string(fixed_artist)}'")
    if fixed_album != original_album:
        set_clauses.append(f"album_summary = '{escape_sql_string(fixed_album)}'")
    return f"UPDATE albums SET {', '.join(set_clauses)} WHERE album_id = '{album_id}';"


def load_broken_data() -> dict:
    """Load the broken-URLs report produced by check_wikipedia_urls.py."""
    try:
        with open(BROKEN_URLS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(
            f"'{BROKEN_URLS_FILE}' not found. "
            "Run scripts/check_wikipedia_urls.py first.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Entry point."""
    broken_data = load_broken_data()
    broken_urls: set[str] = set(broken_data["broken_urls"])
    affected_ids: set[str] = {
        src["album_id"]
        for sources in broken_data["url_to_albums"].values()
        for src in sources
    }

    print(f"Fetching {len(affected_ids)} affected albums from DB...")
    ids_list = ", ".join(f"'{aid}'" for aid in affected_ids)
    records = query_db(
        f"SELECT album_id, artist_summary, album_summary "
        f"FROM albums WHERE album_id IN ({ids_list});"
    )

    statements = [s for rec in records if (s := build_update(rec, broken_urls))]

    if not statements:
        print("Nothing to fix.")
        return

    print(f"Applying {len(statements)} UPDATE statements...")
    batch_size = 10
    for i in range(0, len(statements), batch_size):
        execute_sql("\n".join(statements[i : i + batch_size]))
        print(f"  Applied {min(i + batch_size, len(statements))}/{len(statements)}")

    print(f"\nDone. {len(statements)} albums updated.")


if __name__ == "__main__":
    main()
