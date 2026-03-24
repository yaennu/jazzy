"""
Look up album cover art for albums that have an Apple Music link but no cover image.
Uses the iTunes Search API to find artwork URLs.
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

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
ARTWORK_SIZE = "600x600"


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


def _normalize(text: str) -> str:
    """Lowercase and strip for fuzzy comparison."""
    return text.strip().lower()


def _itunes_get(url: str, params: dict, max_retries: int = 5) -> requests.Response | None:
    """GET request to iTunes API with exponential backoff on 429."""
    delay = 5
    for attempt in range(max_retries):
        response = requests.get(url, params=params)
        if response.status_code == 429:
            print(f"    iTunes rate limit (429), retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
            continue
        return response
    print(f"    iTunes rate limit persists after {max_retries} retries, skipping.")
    return None


def _search_itunes(query: str) -> list[dict]:
    """Run an iTunes Search API query and return album results."""
    response = _itunes_get(
        ITUNES_SEARCH_URL,
        params={"term": query, "media": "music", "entity": "album", "limit": 10},
    )
    if response is None or response.status_code != 200:
        return []
    return response.json().get("results", [])


def _match_artwork(
    results: list[dict], title: str, artist: str, release_year: int | None
) -> str | None:
    """Find the best matching album artwork from iTunes results."""
    norm_title = _normalize(title)
    norm_artist = _normalize(artist)

    exact_match = None
    fuzzy_match = None

    for result in results:
        r_title = _normalize(result.get("collectionName", ""))
        r_artist = _normalize(result.get("artistName", ""))
        r_date = result.get("releaseDate", "")

        print(
            f"      iTunes result: \"{result.get('collectionName')}\" by {result.get('artistName')} ({r_date[:4] if r_date else '?'})"
        )

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


def _extract_collection_id(apple_music_url: str) -> str | None:
    """Extract the numeric collection ID from an Apple Music URL.

    Example: 'https://music.apple.com/us/album/the-essence-of-errol-garner/190114850?uo=4'
    returns '190114850'.
    """
    match = re.search(r"/(\d+)(?:\?|$)", apple_music_url)
    return match.group(1) if match else None


def _lookup_cover_by_id(collection_id: str) -> str | None:
    """Look up album artwork directly via iTunes Lookup API using collection ID."""
    try:
        response = _itunes_get(ITUNES_LOOKUP_URL, params={"id": collection_id})
        if response is None or response.status_code != 200:
            return None
        results = response.json().get("results", [])
        for result in results:
            artwork_url = result.get("artworkUrl100")
            if artwork_url:
                return artwork_url.replace("100x100", ARTWORK_SIZE)
        return None
    except Exception:
        return None


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
        .select("album_id, title, artist, release_year, streaming_link_apple")
        .is_("cover_image_url", "null")
        .not_.is_("streaming_link_apple", "null")
        .execute()
    )
    return response.data


MAX_WORKERS = 1


def _process_album(album: dict, client) -> bool:
    """Look up and store cover art for a single album. Returns True if updated."""
    title = album["title"]
    artist = album["artist"]
    release_year = album.get("release_year")

    print(f"  {title} — {artist}")

    cover_url = None

    # Try direct iTunes lookup via collection ID from Apple Music URL
    apple_url = album.get("streaming_link_apple")
    if apple_url:
        collection_id = _extract_collection_id(apple_url)
        if collection_id:
            cover_url = _lookup_cover_by_id(collection_id)
            if cover_url:
                print(f"    Cover (via lookup): {cover_url}")

    # Fall back to search
    if not cover_url:
        cover_url = search_cover(title, artist, release_year)
        if cover_url:
            print(f"    Cover: {cover_url}")

    if cover_url:
        client.table("albums").update({"cover_image_url": cover_url}).eq(
            "album_id", album["album_id"]
        ).execute()
        time.sleep(0.5)
        return True

    print("    Cover: not found")
    time.sleep(0.5)
    return False


def main():
    print("Looking up album cover art...")

    client = get_supabase_client()
    albums = get_albums_missing_covers(client)
    print(f"Found {len(albums)} album(s) with missing cover art.\n")

    if not albums:
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(_process_album, album, client) for album in albums]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    updated = sum(1 for r in results if r)
    print(f"\nDone. Updated {updated}/{len(albums)} album(s).")


if __name__ == "__main__":
    main()
