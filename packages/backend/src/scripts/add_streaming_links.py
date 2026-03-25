"""
Look up Spotify and Apple Music links for albums that are missing them.
Uses the Spotify Web API (Client Credentials) and the iTunes Search API.
"""

import concurrent.futures
import os
import sys
import threading
import time
import unicodedata
import re

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
ARTWORK_SIZE = "600x600"

# Set when Spotify returns a long-term rate limit — signals all workers to skip Spotify
_spotify_rate_limited = threading.Event()


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


def get_spotify_token() -> str | None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(
            "Warning: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set. Skipping Spotify lookups."
        )
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


def _normalize(text: str) -> str:
    """Normalize text for fuzzy comparison: strip diacritics, standardize punctuation."""
    # Strip diacritics/accents (e.g. "Éthiopiques" → "ethiopiques")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    # Normalize apostrophes/quotes
    text = re.sub(r"[''`]", "'", text)
    # Normalize ampersand
    text = text.replace("&", "and")
    # Remove all punctuation except spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _to_search_query(text: str) -> str:
    """Strip accents and normalize for use as an iTunes search query."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.strip()


def _word_overlap(a: str, b: str) -> float:
    """Fraction of words in `a` that also appear in `b`."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a:
        return 0.0
    return len(words_a & words_b) / len(words_a)


def _match_spotify_result(
    items: list[dict], title: str, artist: str, release_year: int | None
) -> str | None:
    """Find the best matching album from Spotify results. Prefers exact year match."""
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


_SPOTIFY_RETRY_MAX = 30  # seconds — longer Retry-After means a hard ban, skip entirely


def _search_spotify_query(token: str, query: str) -> list[dict]:
    """Run a Spotify search and return album items."""
    if _spotify_rate_limited.is_set():
        return []
    for attempt in range(3):
        response = requests.get(
            SPOTIFY_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "album", "limit": 10},
        )
        if response.status_code == 200:
            return response.json().get("albums", {}).get("items", [])
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
            if retry_after > _SPOTIFY_RETRY_MAX:
                print(f"    Spotify hard rate limit ({retry_after}s). Skipping all Spotify lookups.")
                _spotify_rate_limited.set()
                return []
            print(f"    Spotify rate limited, retrying in {retry_after}s...")
            time.sleep(retry_after)
            continue
        print(f"    Spotify search error {response.status_code}: {response.text[:120]}")
        break
    return []


def search_spotify(
    token: str, title: str, artist: str, release_year: int | None
) -> tuple[str | None, bool]:
    """Try multiple Spotify search strategies with progressively looser queries.

    Returns (url, is_substitute) where is_substitute is True when the link is
    the artist's most popular album rather than an exact title match.
    """
    if not title or not artist:
        return None, False

    stripped_title = re.sub(r"\s*\(.*?\)", "", title).strip()
    ascii_title = _to_search_query(title)
    ascii_artist = _to_search_query(artist)
    ascii_stripped = _to_search_query(stripped_title)

    attempts = [
        (f"album:{title} artist:{artist}", title),         # 1. original
        (f"album:{ascii_title} artist:{ascii_artist}", title),  # 2. ascii
        (f"album:{ascii_stripped} artist:{ascii_artist}", stripped_title),  # 3. stripped parentheticals
        (f"{ascii_title} {ascii_artist}", title),          # 4. plain text
        (f"{ascii_artist} {ascii_title}", title),          # 5. artist-first plain
    ]

    for query, match_title in attempts:
        items = _search_spotify_query(token, query)
        url = _match_spotify_result(items, match_title, artist, release_year)
        if url:
            return url, False
        time.sleep(0.2)

    # Artist fallback: return first result that matches artist name
    items = _search_spotify_query(token, f"artist:{ascii_artist}")
    norm_artist = _normalize(artist)
    for item in items:
        r_artists = [_normalize(a["name"]) for a in item.get("artists", [])]
        if any(norm_artist in ra or ra in norm_artist for ra in r_artists):
            url = item["external_urls"].get("spotify")
            if url:
                return url, True

    return None, False


def _get_spotify_album_upc(token: str, spotify_url: str) -> str | None:
    """Fetch the UPC barcode for a Spotify album URL."""
    album_id = spotify_url.split("/album/")[-1].split("?")[0]
    try:
        response = requests.get(
            f"https://api.spotify.com/v1/albums/{album_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            return None
        return response.json().get("external_ids", {}).get("upc")
    except Exception:
        return None


def _get_itunes_album_upc(apple_url: str) -> str | None:
    """Fetch the UPC barcode for an Apple Music album URL."""
    match = re.search(r"/id(\d+)", apple_url)
    if not match:
        return None
    collection_id = match.group(1)
    try:
        response = requests.get(ITUNES_LOOKUP_URL, params={"id": collection_id})
        if response.status_code != 200:
            return None
        results = response.json().get("results", [])
        for result in results:
            upc = result.get("upc")
            if upc:
                return upc
        return None
    except Exception:
        return None


def _search_spotify_by_upc(token: str, upc: str) -> str | None:
    """Search Spotify by UPC barcode and return the album URL if found."""
    items = _search_spotify_query(token, f"upc:{upc}")
    if items:
        return items[0].get("external_urls", {}).get("spotify")
    return None


def _lookup_itunes_by_upc(upc: str) -> tuple[str, str | None] | None:
    """Look up an Apple Music album URL and artwork by UPC barcode."""
    try:
        response = requests.get(ITUNES_LOOKUP_URL, params={"upc": upc, "country": "ch"})
        if response.status_code != 200:
            return None
        results = response.json().get("results", [])
        for result in results:
            url = result.get("collectionViewUrl")
            if url:
                artwork = result.get("artworkUrl100")
                if artwork:
                    artwork = artwork.replace("100x100", ARTWORK_SIZE)
                return url, artwork
        return None
    except Exception:
        return None


def _search_itunes(query: str, country: str = "ch") -> list[dict]:
    """Run an iTunes Search API query and return album results."""
    response = requests.get(
        ITUNES_SEARCH_URL,
        params={"term": query, "media": "music", "entity": "album", "limit": 25, "country": country},
    )
    if response.status_code != 200:
        print(f"    iTunes search error {response.status_code} (country={country}): {response.text[:120]}")
        return []
    return response.json().get("results", [])


def _title_matches(norm_title: str, r_title: str) -> bool:
    """True if titles are similar enough: substring or ≥60% word overlap."""
    if norm_title in r_title or r_title in norm_title:
        return True
    return _word_overlap(norm_title, r_title) >= 0.6


def _match_apple_result(
    results: list[dict], title: str, artist: str, release_year: int | None
) -> tuple[str, str | None] | None:
    """Find the best matching album from iTunes results. Prefers exact year match, falls back to title+artist match.

    Returns (collectionViewUrl, artworkUrl) or None.
    """
    norm_title = _normalize(title)
    norm_artist = _normalize(artist)

    exact_match = None
    fuzzy_match = None

    for result in results:
        r_title = _normalize(result.get("collectionName", ""))
        r_artist = _normalize(result.get("artistName", ""))
        r_date = result.get("releaseDate", "")

        if not _title_matches(norm_title, r_title):
            continue
        if norm_artist not in r_artist and r_artist not in norm_artist:
            continue

        url = result.get("collectionViewUrl")
        artwork = result.get("artworkUrl100")
        if artwork:
            artwork = artwork.replace("100x100", ARTWORK_SIZE)

        # Check year match
        if release_year and r_date:
            if int(r_date[:4]) == release_year and not exact_match:
                exact_match = (url, artwork)
            elif not fuzzy_match:
                fuzzy_match = (url, artwork)
        elif not fuzzy_match:
            fuzzy_match = (url, artwork)

    # Prefer exact year match, but accept reissues
    return exact_match or fuzzy_match


def _match_apple_result_loose(
    results: list[dict], artist: str, release_year: int | None
) -> tuple[str, str | None, str | None, str | None, int | None] | None:
    """Match iTunes results on artist + release year only (no title check).

    Returns (collectionViewUrl, artworkUrl, title, artist, year) or None.
    """
    if not release_year:
        return None
    norm_artist = _normalize(artist)
    for result in results:
        r_artist = _normalize(result.get("artistName", ""))
        r_date = result.get("releaseDate", "")
        if norm_artist not in r_artist and r_artist not in norm_artist:
            continue
        if r_date and int(r_date[:4]) == release_year:
            url = result.get("collectionViewUrl")
            if url:
                artwork = result.get("artworkUrl100")
                if artwork:
                    artwork = artwork.replace("100x100", ARTWORK_SIZE)
                sub_year = int(r_date[:4]) if r_date else None
                return url, artwork, result.get("collectionName"), result.get("artistName"), sub_year
    return None


def _pick_artist_top_album(artist: str, country: str = "ch") -> tuple[str, str | None, str | None, str | None, int | None] | None:
    """Return the collectionViewUrl, artworkUrl, title, artist, year of the artist's most popular album on iTunes."""
    ascii_artist = _to_search_query(artist)
    norm_artist = _normalize(artist)
    results = _search_itunes(ascii_artist, country)
    for result in results:
        r_artist = _normalize(result.get("artistName", ""))
        if norm_artist in r_artist or r_artist in norm_artist:
            url = result.get("collectionViewUrl")
            if url:
                artwork = result.get("artworkUrl100")
                if artwork:
                    artwork = artwork.replace("100x100", ARTWORK_SIZE)
                r_date = result.get("releaseDate", "")
                sub_year = int(r_date[:4]) if r_date else None
                return url, artwork, result.get("collectionName"), result.get("artistName"), sub_year
    return None


def search_apple_music(
    title: str, artist: str, release_year: int | None, country: str = "ch"
) -> tuple[str | None, str | None, bool, dict | None]:
    """Try multiple iTunes search strategies with progressively looser queries.

    Searches the given storefront first; falls back to the US store if nothing is found.
    Returns (url, artwork_url, is_substitute, sub_meta) where sub_meta is a dict
    with {title, artist, release_year} when is_substitute is True, else None.
    """
    if not title or not artist:
        return None, None, False, None

    # Strip parenthetical subtitles (e.g. "... (Bande Originale Du Film)" → "...")
    stripped_title = re.sub(r"\s*\(.*?\)", "", title).strip()
    # ASCII versions (strip accents) so the iTunes API doesn't choke on special chars
    ascii_title = _to_search_query(title)
    ascii_stripped = _to_search_query(stripped_title)
    # First word of artist for partial matches (e.g. "Erroll" from "Erroll Garner")
    artist_first = artist.split()[0] if artist else artist
    ascii_artist = _to_search_query(artist)

    # Build ordered list of (search_query, match_title, match_artist) attempts
    attempts = [
        (f"{title} {artist}", title, artist),  # 1. original title + artist
        (f"{ascii_title} {ascii_artist}", title, artist),  # 2. ascii title + artist
        (ascii_title, title, artist),  # 3. ascii title only
    ]
    if stripped_title and stripped_title != title:
        attempts += [
            (
                f"{ascii_stripped} {ascii_artist}",
                stripped_title,
                artist,
            ),  # 4. ascii stripped + artist
            (ascii_stripped, stripped_title, artist),  # 5. ascii stripped only
        ]
    attempts += [
        (f"{ascii_artist} {ascii_title}", title, artist),  # 6. artist-first query
        (ascii_artist, title, artist),  # 7. search by artist, match title
        (
            f"{artist_first} {ascii_stripped}",
            stripped_title,
            artist,
        ),  # 8. first name + stripped
    ]

    for query, match_title, match_artist in attempts:
        results = _search_itunes(query, country)
        match = _match_apple_result(results, match_title, match_artist, release_year)
        if match:
            url, artwork = match
            return url, artwork, False, None
        time.sleep(0.2)

    # Strategy 9: artist + year loose match
    if release_year:
        results = _search_itunes(f"{ascii_artist} {release_year}", country)
        match = _match_apple_result_loose(results, artist, release_year)
        if match:
            url, artwork, sub_title, sub_artist, sub_year = match
            return url, artwork, True, {"title": sub_title, "artist": sub_artist, "release_year": sub_year}
        time.sleep(0.2)

    # Fall back to artist's most popular album
    match = _pick_artist_top_album(artist, country)
    if match:
        url, artwork, sub_title, sub_artist, sub_year = match
        return url, artwork, True, {"title": sub_title, "artist": sub_artist, "release_year": sub_year}

    # Nothing found in this storefront — retry in the US store
    if country != "us":
        return search_apple_music(title, artist, release_year, country="us")

    return None, None, False, None


def get_albums_missing_links(client: Client) -> list[dict]:
    response = (
        client.table("albums")
        .select(
            "album_id, title, artist, release_year, streaming_link_spotify, streaming_link_apple, apple_link_is_substitute, spotify_link_is_substitute, cover_image_url, original_title"
        )
        .or_("streaming_link_spotify.is.null,streaming_link_apple.is.null")
        .execute()
    )
    return response.data


MAX_WORKERS = 1


def _process_album(album: dict, client: Client, spotify_token: str | None) -> tuple[bool, bool, bool]:
    """Process a single album's streaming links. Returns (updated, apple_sub, spotify_sub)."""
    title = album["title"]
    artist = album["artist"]
    release_year = album.get("release_year")
    updates = {}

    print(f"  {title} — {artist}")

    if album["streaming_link_apple"] is None and not album.get("apple_link_is_substitute"):
        # Try Spotify → Apple UPC bridge first (high confidence)
        spotify_url = updates.get("streaming_link_spotify") or album.get("streaming_link_spotify")
        apple_url = None
        if spotify_url and spotify_token:
            upc = _get_spotify_album_upc(spotify_token, spotify_url)
            if upc:
                upc_result = _lookup_itunes_by_upc(upc)
                if upc_result:
                    apple_url, artwork_url = upc_result
                    updates["streaming_link_apple"] = apple_url
                    updates["apple_link_is_substitute"] = False
                    if artwork_url and not album.get("cover_image_url"):
                        updates["cover_image_url"] = artwork_url
                    print(f"    Apple Music (via UPC): {apple_url}")

        if not apple_url:
            url, artwork_url, is_sub, sub_meta = search_apple_music(title, artist, release_year)
            if url:
                updates["streaming_link_apple"] = url
                updates["apple_link_is_substitute"] = is_sub
                if artwork_url and not album.get("cover_image_url"):
                    updates["cover_image_url"] = artwork_url
                if is_sub and sub_meta:
                    # Preserve original calendar data on first substitution
                    if not album.get("original_title"):
                        updates["original_title"] = album["title"]
                        updates["original_artist"] = album["artist"]
                    # Replace album metadata with the substitute album's data
                    if sub_meta.get("title"):
                        updates["title"] = sub_meta["title"]
                        title = sub_meta["title"]
                    if sub_meta.get("artist"):
                        updates["artist"] = sub_meta["artist"]
                        artist = sub_meta["artist"]
                    if sub_meta.get("release_year"):
                        updates["release_year"] = sub_meta["release_year"]
                        release_year = sub_meta["release_year"]
                    # Clear fields tied to the original album (regenerated by later pipeline steps)
                    updates["label_name"] = None
                    updates["cover_artists"] = None
                    updates["artist_summary"] = None
                    updates["album_summary"] = None
                    print(f"    Apple Music (substitute): {sub_meta.get('title')} by {sub_meta.get('artist')} → {url}")
                else:
                    print(f"    Apple Music: {url}")
            else:
                print("    Apple Music: not found")
        time.sleep(0.5)

    apple_sub = updates.get("apple_link_is_substitute", False)

    if album["streaming_link_spotify"] is None and not album.get("spotify_link_is_substitute") and spotify_token and not _spotify_rate_limited.is_set():
        # Try Apple Music → Spotify UPC bridge first (high confidence)
        # Use Apple link just found above, or one already in the DB
        apple_url = updates.get("streaming_link_apple") or album.get("streaming_link_apple")
        spotify_url = None
        if apple_url:
            upc = _get_itunes_album_upc(apple_url)
            if upc:
                spotify_url = _search_spotify_by_upc(spotify_token, upc)
                if spotify_url:
                    updates["streaming_link_spotify"] = spotify_url
                    updates["spotify_link_is_substitute"] = False
                    print(f"    Spotify (via UPC): {spotify_url}")

        if not spotify_url:
            url, is_sub = search_spotify(spotify_token, title, artist, release_year)
            if url:
                updates["streaming_link_spotify"] = url
                updates["spotify_link_is_substitute"] = is_sub
                if is_sub:
                    print(f"    Spotify (substitute): {url}")
                else:
                    print(f"    Spotify: {url}")
            else:
                print("    Spotify: not found")
        time.sleep(0.5)

    spotify_sub = updates.get("spotify_link_is_substitute", False)

    if updates:
        client.table("albums").update(updates).eq("album_id", album["album_id"]).execute()
        return True, apple_sub, spotify_sub

    return False, False, False


def main():
    print("Looking up streaming links for albums...")

    client = get_supabase_client()
    spotify_token = get_spotify_token()

    albums = get_albums_missing_links(client)
    print(f"Found {len(albums)} album(s) with missing links.\n")

    if not albums:
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(_process_album, album, client, spotify_token)
            for album in albums
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    updated = sum(1 for was_updated, _, _ in results if was_updated)
    apple_substitute_count = sum(1 for _, apple_sub, _ in results if apple_sub)
    spotify_substitute_count = sum(1 for _, _, spotify_sub in results if spotify_sub)

    summary = f"\nDone. Updated {updated}/{len(albums)} album(s)."
    parts = []
    if apple_substitute_count:
        parts.append(f"{apple_substitute_count} Apple substitute(s)")
    if spotify_substitute_count:
        parts.append(f"{spotify_substitute_count} Spotify substitute(s)")
    if parts:
        summary += f" ({', '.join(parts)})"
    print(summary)


if __name__ == "__main__":
    main()
