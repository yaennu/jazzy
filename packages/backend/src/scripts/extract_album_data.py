"""
Extracts album information from PNG images and generates a CSV file.

Processes PNG images to extract album title, artist, and release year
using a local vision language model via Ollama, and saves the structured
data into a CSV file.
"""

import csv
import json
import os
import re
import tempfile

from ollama import chat
from PIL import Image


# --- Configuration ---
# Vision model used for OCR extraction. Swap to a larger model for better accuracy:
#   granite3.2-vision  (~2 GB) — compact, fast
#   llama3.2-vision    (~7 GB) — higher accuracy
MODEL_NAME = "granite3.2-vision"

EXTRACTION_PROMPT = """\
This is a photo of a jazz calendar page. In the bottom-right area below the album \
cover, there are a few lines of small printed text. The text follows this format:
  Line 1: Artist name
  Line 2: Album title
  Line 3: Record label, release year

IMPORTANT: Read ONLY the small printed text in the bottom-right area. Do NOT read \
text from the album cover artwork itself. The release year is the 4-digit year next \
to the record label name (e.g. "Blue Note Records, 1975"), NOT any calendar date.

Return ONLY a JSON object with these keys:
- "artist": the artist or band name (from line 1 of the text area)
- "title": the album title (from line 2 of the text area)
- "release_year": the original album release year as an integer (from line 3)

Return ONLY valid JSON, no other text.\
"""

# Construct absolute paths from the script's location to make it runnable from anywhere
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

PNG_PHOTOS_DIR = os.path.join(PROJECT_ROOT, "data", "png-images")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "albums.csv")


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


def _crop_text_area(image_path):
    """Crops to the bottom portion of the image where the text metadata lives.

    The cropped area is upscaled 2x so the small printed text is easier for
    the vision model to read accurately.
    """
    img = Image.open(image_path)
    width, height = img.size
    # The text area is always in the bottom ~35% of the calendar page
    cropped = img.crop((0, int(height * 0.65), width, height))
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
        response = chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT,
                    "images": [cropped_path],
                }
            ],
        )

        raw_text = response.message.content
        data = _parse_json_from_response(raw_text)

        if data is None:
            print(f"Could not parse JSON from model response for {image_path}:")
            print(f"  Response: {raw_text}")
            return None

        release_year = data.get("release_year", 0)
        if isinstance(release_year, str):
            year_match = re.search(r"\d{4}", release_year)
            release_year = int(year_match.group()) if year_match else 0

        return {
            "title": str(data.get("title", "Unknown Title")).strip(),
            "artist": str(data.get("artist", "Unknown Artist")).strip(),
            "release_year": int(release_year),
        }

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None
    finally:
        if cropped_path:
            os.unlink(cropped_path)


def main():
    """
    Main function to extract album data from photos and create a CSV file.
    """
    print("Starting album data extraction from PNG images...")
    png_files = find_png_files(PNG_PHOTOS_DIR)

    if not png_files:
        print(f"No .PNG files found in {PNG_PHOTOS_DIR}")
        return

    all_albums_data = []

    for image_path in png_files:
        print(f"Processing {image_path}...")
        album_info = extract_album_info_from_image(image_path)

        if album_info and album_info["title"].strip() and album_info["title"] != "Unknown Title":
            album_info["source_file"] = os.path.basename(image_path)
            all_albums_data.append(album_info)
        else:
            print(f"Could not extract valid information from {image_path}")

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "artist", "release_year", "source_file"])
        for album in all_albums_data:
            writer.writerow([album["title"], album["artist"], album["release_year"], album["source_file"]])

    print(f"\nSuccessfully extracted data for {len(all_albums_data)} albums.")
    print(f"Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
