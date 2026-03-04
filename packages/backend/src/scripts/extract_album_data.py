"""
Extracts album information from PNG images and inserts records into the database.

Processes PNG images to extract album title, artist, release year, record label,
and cover artists using Google Gemini 2.0 Flash via the Gen AI SDK, and inserts
the structured data directly into the albums table.

Requires GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY to be set
in packages/backend/.env.local
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from supabase import create_client, Client


# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
load_dotenv(os.path.join(BACKEND_ROOT, ".env"))

MODEL_NAME = "gemini-2.0-flash"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

EXTRACTION_PROMPT = """\
This is a photo of a jazz calendar page.

In the bottom-LEFT corner, there is a calendar date in the format "DD MON" \
(e.g. "02 JAN", "14 FEB"). Read this date.

In the bottom-RIGHT area below the album cover, there are a few lines of small \
printed text. The text follows this format:
  Line 1: Artist name
  Line 2: Album title
  Line 3: Record label, release year
  Lines 4+: Cover artist(s) — one or more lines listing who created the cover artwork

IMPORTANT: Read ONLY the small printed text in the bottom-right area for album info. \
Do NOT read text from the album cover artwork itself. The release year is the 4-digit \
year next to the record label name (e.g. "Blue Note Records, 1975"), NOT the calendar date.

Return ONLY a JSON object with these keys:
- "calendar_date": the calendar date from the bottom-left corner (e.g. "02 JAN")
- "artist": the artist or band name (from line 1 of the text area)
- "title": the album title (from line 2 of the text area)
- "label_name": the record label name (from line 3, e.g. "Blue Note Records")
- "release_year": the original album release year as an integer (from line 3)
- "cover_artists": all remaining lines after line 3, joined with ", " as a single string

Return ONLY valid JSON, no other text.\
"""

PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, "..", ".."))

PNG_PHOTOS_DIR = os.path.join(PROJECT_ROOT, "data", "png-images")


def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)
    return create_client(url, key)


def find_png_files(directory):
    """Finds all .PNG files in the specified directory."""
    png_files = sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.upper().endswith(".PNG")
    )
    return png_files


def _parse_json_from_response(text):
    """Extracts and parses a JSON object from the model's response text."""
    # Try direct JSON parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON within markdown code fences or surrounding text
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def _calendar_date_to_day_of_year(date_str: str) -> int | None:
    """Convert a calendar date like '02 JAN' to a day-of-year integer (e.g. 2)."""
    try:
        dt = datetime.strptime(f"{date_str.strip()} 2000", "%d %b %Y")
        return dt.timetuple().tm_yday
    except ValueError:
        return None


def _crop_text_area(image_path):
    """Crops to the bottom portion of the image where the text metadata lives.

    The cropped area is upscaled 2x so the small printed text is easier for
    the vision model to read accurately.
    """
    img = Image.open(image_path)
    width, height = img.size
    # The text area is always in the bottom ~50% of the calendar page
    cropped = img.crop((0, int(height * 0.5), width, height))
    # Upscale 2x for better character recognition on small text
    cropped = cropped.resize(
        (cropped.width * 2, cropped.height * 2), Image.Resampling.LANCZOS
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cropped.save(tmp.name, "PNG")
    return tmp.name


def extract_album_info_from_image(image_path, model=MODEL_NAME):
    """
    Extracts album title, artist, and release year from an image using a vision LLM.
    """
    cropped_path = None
    try:
        cropped_path = _crop_text_area(image_path)

        with open(cropped_path, "rb") as f:
            image_bytes = f.read()

        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                EXTRACTION_PROMPT,
            ],
        )

        raw_text = response.text
        data = _parse_json_from_response(raw_text)

        if data is None:
            print(f"Could not parse JSON from model response for {image_path}:")
            print(f"  Response: {raw_text}")
            return None

        release_year = data.get("release_year", 0)
        if isinstance(release_year, str):
            year_match = re.search(r"\d{4}", release_year)
            release_year = int(year_match.group()) if year_match else 0

        calendar_date = str(data.get("calendar_date", "")).strip().upper()
        calendar_order = _calendar_date_to_day_of_year(calendar_date) if calendar_date else None

        return {
            "title": str(data.get("title", "Unknown Title")).strip(),
            "artist": str(data.get("artist", "Unknown Artist")).strip(),
            "label_name": str(data.get("label_name", "")).strip(),
            "release_year": int(release_year),
            "cover_artists": str(data.get("cover_artists", "")).strip(),
            "calendar_order": calendar_order,
        }

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None
    finally:
        if cropped_path:
            os.unlink(cropped_path)


def insert_albums_to_db(client: Client, albums: list[dict]) -> None:
    if not albums:
        print("No albums to insert.")
        return
    records = [
        {
            "title": a["title"],
            "artist": a["artist"],
            "release_year": a["release_year"] or None,
            "label_name": a["label_name"] or None,
            "cover_artists": a["cover_artists"] or None,
            "calendar_order": a.get("calendar_order"),
        }
        for a in albums
    ]
    response = client.table("albums").insert(records).execute()
    print(f"Inserted {len(response.data)} albums into the database.")


def main():
    """
    Main function to extract album data from photos and insert into the database.
    """
    print("Starting album data extraction from PNG images...")
    png_files = find_png_files(PNG_PHOTOS_DIR)

    if not png_files:
        print(f"No .PNG files found in {PNG_PHOTOS_DIR}")
        return

    all_albums_data = []

    total = len(png_files)
    for i, image_path in enumerate(png_files, 1):
        print(f"Processing {i}/{total}: {os.path.basename(image_path)}...")
        album_info = extract_album_info_from_image(image_path)

        if (
            album_info
            and album_info["title"].strip()
            and album_info["title"] != "Unknown Title"
        ):
            all_albums_data.append(album_info)
        else:
            print(f"Could not extract valid information from {image_path}")

    db_client = get_supabase_client()
    insert_albums_to_db(db_client, all_albums_data)
    print(f"\nSuccessfully extracted data for {len(all_albums_data)} albums.")


if __name__ == "__main__":
    main()
