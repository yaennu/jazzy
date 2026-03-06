# Feature: Album Data Pipeline

The album seeding pipeline populates the `albums` table from source images and enriches records with streaming links, cover art, and LLM-generated summaries.

## Behavior: Conditional seeding

The pipeline only runs when the albums table is empty.

- Given the seeding script (`main.py`) is executed
- When the `albums` table already contains rows:
  - Then the script prints "Albums table already has data. Skipping seed." and exits
- When the `albums` table is empty:
  - Then all four enrichment scripts run in sequence

## Behavior: Extraction pipeline order

The enrichment scripts run in a fixed sequence because each step depends on the previous.

- Given the albums table is empty and seeding begins
- When the pipeline runs:
  - Then Step 1: `extract_album_data.py` — extracts album metadata from source images using Google Gemini vision
  - Then Step 2: `add_streaming_links.py` — looks up Spotify and Apple Music links for each album
  - Then Step 3: `add_album_covers.py` — fetches album cover art URLs from iTunes
  - Then Step 4: `add_album_summaries.py` — generates artist and album summaries using Perplexity API

## Behavior: Pipeline failure handling

If any script in the pipeline fails, the entire process stops.

- Given the pipeline is running
- When a script exits with a non-zero return code:
  - Then the pipeline prints a failure message with the script name and exit code
  - Then the pipeline exits immediately without running subsequent scripts

## Behavior: Album data extraction (Step 1)

Album metadata is extracted from PNG images using vision AI.

- Given PNG images exist in the `data/` directory
- When `extract_album_data.py` runs:
  - Then it uses Google Gemini 2.0 Flash to read album information from images
  - Then it inserts rows into the `albums` table with: title, artist, release_year, label_name, cover_artists, calendar_order

## Behavior: Streaming link enrichment (Step 2)

Each album gets Spotify and Apple Music streaming links.

- Given albums exist in the database without streaming links
- When `add_streaming_links.py` runs:
  - Then it queries Spotify Web API for each album's title + artist
  - Then it queries iTunes Search API for Apple Music links
  - Then it updates `streaming_link_spotify` and `streaming_link_apple` columns

## Behavior: Album cover art (Step 3)

Each album gets a cover image URL.

- Given albums exist in the database without cover images
- When `add_album_covers.py` runs:
  - Then it queries iTunes Search API for album artwork
  - Then it updates the `cover_image_url` column

## Behavior: Album summaries (Step 4)

Each album gets LLM-generated artist and album summaries.

- Given albums exist in the database without summaries
- When `add_album_summaries.py` runs:
  - Then it uses Perplexity API to generate contextual summaries
  - Then it updates the `artist_summary` and `album_summary` columns
