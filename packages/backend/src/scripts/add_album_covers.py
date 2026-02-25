"""
Look up album cover art for albums that have an Apple Music link but no cover image.
Uses the iTunes Search API to find artwork URLs.
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ARTWORK_SIZE = "600x600"


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)
    return create_client(url, key)


def _normalize(text: str) -> str:
    """Lowercase and strip for fuzzy comparison."""
    return text.strip().lower()


def _search_itunes(query: str) -> list[dict]:
    """Run an iTunes Search API query and return album results."""
    response = requests.get(
        ITUNES_SEARCH_URL,
        params={"term": query, "media": "music", "entity": "album", "limit": 10},
    )
    if response.status_code != 200:
        return []
    return response.json().get("results", [])


def _match_artwork(results: list[dict], title: str, artist: str, release_year: int | None) -> str | None:
    """Find the best matching album artwork from iTunes results."""
    norm_title = _normalize(title)
    norm_artist = _normalize(artist)

    exact_match = None
    fuzzy_match = None

    for result in results:
        r_title = _normalize(result.get("collectionName", ""))
        r_artist = _normalize(result.get("artistName", ""))
        r_date = result.get("releaseDate", "")

        print(f"      iTunes result: \"{result.get('collectionName')}\" by {result.get('artistName')} ({r_date[:4] if r_date else '?'})")

        if norm_title not in r_title and r_title not in norm_title:
            continue
        if norm_artist not in r_artist and r_artist not in norm_artist:
            continue

        artwork_url = result.get("artworkUrl100")
        if not artwork_url:
            continue

        # Upsize from 100x100 to target resolution
        artwork_url = artwork_url.replace("100x100", ARTWORK_SIZE)

        if release_year and r_date:
            if int(r_date[:4]) == release_year and not exact_match:
                exact_match = artwork_url
            elif not fuzzy_match:
                fuzzy_match = artwork_url
        elif not fuzzy_match:
            fuzzy_match = artwork_url

    return exact_match or fuzzy_match


def search_cover(title: str, artist: str, release_year: int | None) -> str | None:
    """Search iTunes for album cover art. Returns artwork URL or None."""
    # Try title + artist first
    results = _search_itunes(f"{title} {artist}")
    url = _match_artwork(results, title, artist, release_year)
    if url:
        return url

    # Fallback: search by title only (artist name may differ on Apple Music)
    if not results or artist.lower() != "various artists":
        results = _search_itunes(title)
        url = _match_artwork(results, title, artist, release_year)
        if url:
            return url

    return None


def get_albums_missing_covers(client: Client) -> list[dict]:
    response = (
        client.table("albums")
        .select("album_id, title, artist, release_year")
        .is_("cover_image_url", "null")
        .not_.is_("streaming_link_apple", "null")
        .execute()
    )
    return response.data


def main():
    print("Looking up album cover art...")

    client = get_supabase_client()
    albums = get_albums_missing_covers(client)
    print(f"Found {len(albums)} album(s) with missing cover art.\n")

    if not albums:
        return

    updated = 0
    for album in albums:
        title = album["title"]
        artist = album["artist"]
        release_year = album.get("release_year")

        print(f"  {title} — {artist}")

        cover_url = search_cover(title, artist, release_year)
        if cover_url:
            print(f"    Cover: {cover_url}")
            client.table("albums").update({"cover_image_url": cover_url}).eq(
                "album_id", album["album_id"]
            ).execute()
            updated += 1
        else:
            print("    Cover: not found")

        time.sleep(0.5)

    print(f"\nDone. Updated {updated}/{len(albums)} album(s).")


if __name__ == "__main__":
    main()
