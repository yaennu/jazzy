"""
Generate short artist and album summaries for albums that are missing them.
Uses the Perplexity API (search-augmented LLM) so no separate Wikipedia fetch is needed —
Perplexity searches the web and summarizes in a single call.

Run manually after seeding the database:
    uv run python src/scripts/add_album_summaries.py
"""

import concurrent.futures
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar"
SUMMARY_TARGET_WORDS = "40-60"
REQUEST_DELAY_SECONDS = 1.5


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
    if os.environ.get("PRODUCTION") == "True":
        load_dotenv(os.path.join(BACKEND_ROOT, ".env.production"), override=True)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)
    return create_client(url, key)


def get_perplexity_api_key() -> str:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
    if os.environ.get("PRODUCTION") == "True":
        load_dotenv(os.path.join(BACKEND_ROOT, ".env.production"), override=True)
    key = os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        print("Error: PERPLEXITY_API_KEY must be set.")
        sys.exit(1)
    return key


def query_perplexity(api_key: str, prompt: str) -> str | None:
    """Send a prompt to Perplexity and return the response text, or None on failure."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"""\
You are a knowledgeable jazz music writer. \
Write factual, engaging summaries in plain prose. \
Keep each summary to {SUMMARY_TARGET_WORDS} words. \
Do not use bullet points or headings. Do not include citations or footnotes. \
Link every person, musician, band, record label, album and record \
mentioned in your text as an HTML anchor tag (<a href="URL">name</a>) \
pointing to their Wikipedia page. Only use URLs you are confident exist. \
Do not use [] for source referencing. \
Your entire response must be a single line of text with no newline characters.""",
            },
            {"role": "user", "content": prompt},
        ],
    }
    for attempt in range(4):
        response = None
        try:
            response = requests.post(
                PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
            return re.sub(r"\[\d+\]", "", text).strip()
        except Exception as e:
            if response is not None and response.status_code == 429 and attempt < 3:
                wait = 10 * (2 ** attempt)  # 10s, 20s, 40s
                print(f"    Rate limited, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Perplexity error: {e}")
                return None


def get_albums_missing_summaries(client: Client) -> list[dict]:
    """Return albums where at least one summary column is NULL."""
    response = (
        client.table("albums")
        .select("album_id, title, artist, release_year, artist_summary")
        .or_("artist_summary.is.null,album_summary.is.null")
        .execute()
    )
    return response.data


MAX_WORKERS = 2


def _process_album(album: dict, client: Client, api_key: str) -> bool:
    """Generate and store summaries for a single album. Returns True if updated."""
    title = album["title"]
    artist = album["artist"]
    release_year = album.get("release_year")
    year_str = f" ({release_year})" if release_year else ""

    print(f"  {title}{year_str} — {artist}")

    updates: dict = {}

    if album.get("artist_summary") is None:
        prompt = f"""\
Write a {SUMMARY_TARGET_WORDS}-word biographical summary of the jazz musician \
"{artist}". Cover their background, musical style, and significance in jazz history. \
Search for accurate information from Wikipedia and music reference sources."""
        summary = query_perplexity(api_key, prompt)
        if summary:
            updates["artist_summary"] = summary
            print(f"    Artist summary: {len(summary.split())} words")
        else:
            print("    Artist summary: failed")
        time.sleep(REQUEST_DELAY_SECONDS)

    if album.get("album_summary") is None:
        artist_summary = updates.get("artist_summary") or album.get("artist_summary") or ""
        artist_context = ""
        if artist_summary:
            artist_context = f"""

The reader will already see this artist bio alongside the album summary, \
so do NOT repeat biographical details:
\"{artist_summary}\""""
        prompt = f"""\
Write a {SUMMARY_TARGET_WORDS}-word summary of the jazz album \
"{title}"{year_str} by {artist}. Cover its musical style, recording context, \
key tracks, and why it matters in the jazz canon. \
Search for accurate information from Wikipedia and music reference sources. \
If you do not find any specific information about the above mentioned jazz album, \
then write something about his general musical style.{artist_context}"""
        summary = query_perplexity(api_key, prompt)
        if summary:
            updates["album_summary"] = summary
            print(f"    Album summary: {len(summary.split())} words")
        else:
            print("    Album summary: failed")
        time.sleep(REQUEST_DELAY_SECONDS)

    if updates:
        client.table("albums").update(updates).eq("album_id", album["album_id"]).execute()
        return True

    return False


def main():
    print("Generating album and artist summaries via Perplexity...")

    client = get_supabase_client()
    api_key = get_perplexity_api_key()

    albums = get_albums_missing_summaries(client)
    print(f"Found {len(albums)} album(s) with missing summaries.\n")

    if not albums:
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(_process_album, album, client, api_key)
            for album in albums
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    updated = sum(1 for r in results if r)
    print(f"\nDone. Updated {updated}/{len(albums)} album(s).")


if __name__ == "__main__":
    main()
