"""
Look up Spotify and Apple Music links for albums that are missing them.
Uses the Spotify Web API (Client Credentials) and the iTunes Search API.
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)
    return create_client(url, key)


def get_spotify_token() -> str | None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Warning: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set. Skipping Spotify lookups.")
        return None

    response = requests.post(
        SPOTIFY_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
    )
    if response.status_code != 200:
        print(f"Warning: Failed to get Spotify token: {response.text}")
        return None

    return response.json()["access_token"]


def search_spotify(token: str, title: str, artist: str, release_year: int | None) -> str | None:
    query = f"album:{title} artist:{artist}"
    response = requests.get(
        SPOTIFY_SEARCH_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "album", "limit": 10},
    )
    if response.status_code != 200:
        return None

    items = response.json().get("albums", {}).get("items", [])
    if not items:
        return None

    norm_title = _normalize(title)
    norm_artist = _normalize(artist)

    exact_match = None
    fuzzy_match = None

    for item in items:
        r_title = _normalize(item.get("name", ""))
        r_artists = [_normalize(a["name"]) for a in item.get("artists", [])]

        if norm_title not in r_title and r_title not in norm_title:
            continue
        if not any(norm_artist in ra or ra in norm_artist for ra in r_artists):
            continue

        url = item["external_urls"].get("spotify")
        r_date = item.get("release_date", "")
        if release_year and r_date:
            if int(r_date[:4]) == release_year and not exact_match:
                exact_match = url
            elif not fuzzy_match:
                fuzzy_match = url
        elif not fuzzy_match:
            fuzzy_match = url

    return exact_match or fuzzy_match


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


def _match_apple_result(results: list[dict], title: str, artist: str, release_year: int | None) -> str | None:
    """Find the best matching album from iTunes results. Prefers exact year match, falls back to title+artist match."""
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

        url = result.get("collectionViewUrl")

        # Check year match
        if release_year and r_date:
            if int(r_date[:4]) == release_year and not exact_match:
                exact_match = url
            elif not fuzzy_match:
                fuzzy_match = url
        elif not fuzzy_match:
            fuzzy_match = url

    # Prefer exact year match, but accept reissues
    return exact_match or fuzzy_match


def search_apple_music(title: str, artist: str, release_year: int | None) -> str | None:
    # Try title + artist first
    results = _search_itunes(f"{title} {artist}")
    url = _match_apple_result(results, title, artist, release_year)
    if url:
        return url

    # Fallback: search by title only (artist name may differ on Apple Music)
    if not results or artist.lower() != "various artists":
        results = _search_itunes(title)
        url = _match_apple_result(results, title, artist, release_year)
        if url:
            return url

    return None


def get_albums_missing_links(client: Client) -> list[dict]:
    response = (
        client.table("albums")
        .select("album_id, title, artist, release_year, streaming_link_spotify, streaming_link_apple")
        .or_("streaming_link_spotify.is.null,streaming_link_apple.is.null")
        .execute()
    )
    return response.data


def main():
    print("Looking up streaming links for albums...")

    client = get_supabase_client()
    spotify_token = get_spotify_token()

    albums = get_albums_missing_links(client)
    print(f"Found {len(albums)} album(s) with missing links.\n")

    if not albums:
        return

    updated = 0
    for album in albums:
        title = album["title"]
        artist = album["artist"]
        updates = {}

        print(f"  {title} — {artist}")

        if album["streaming_link_spotify"] is None and spotify_token:
            url = search_spotify(spotify_token, title, artist, album.get("release_year"))
            if url:
                updates["streaming_link_spotify"] = url
                print(f"    Spotify: {url}")
            else:
                print("    Spotify: not found")
            time.sleep(0.5)

        if album["streaming_link_apple"] is None:
            url = search_apple_music(title, artist, album.get("release_year"))
            if url:
                updates["streaming_link_apple"] = url
                print(f"    Apple Music: {url}")
            else:
                print("    Apple Music: not found")
            time.sleep(0.5)

        if updates:
            client.table("albums").update(updates).eq("album_id", album["album_id"]).execute()
            updated += 1

    print(f"\nDone. Updated {updated}/{len(albums)} album(s).")


if __name__ == "__main__":
    main()
