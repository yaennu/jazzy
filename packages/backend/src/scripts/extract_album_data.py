"""
Extracts album information from HEIC photos and generates a JSON file.

This script processes all .HEIC images in a specified directory, uses OCR to
extract album title, artist, and release year, and then saves the structured
data into a JSON file that matches the Supabase database schema.
"""

import os
import json
import uuid
import re
import pillow_heif
import pytesseract

# --- Configuration ---
# Ensure Tesseract OCR is installed on your system.
# On macOS: brew install tesseract
# On Debian/Ubuntu: sudo apt-get install tesseract-ocr
# You may also need to set the command path if it's not in your system's PATH.
# pytesseract.pytesseract.tesseract_cmd = r'/path/to/your/tesseract'

# Construct absolute paths from the script's location to make it runnable from anywhere
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

PHOTOS_DIR = os.path.join(PROJECT_ROOT, "data", "photos")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "albums.json")


def find_heic_files(directory):
    """Finds all .HEIC files in the specified directory."""
    heic_files = []
    for filename in os.listdir(directory):
        if filename.upper().endswith(".HEIC"):
            heic_files.append(os.path.join(directory, filename))
    return heic_files


def extract_album_info_from_image(image_path):
    """
    Extracts album title, artist, and release year from an image using OCR.
    """
    try:
        heif_file = pillow_heif.read_heif(image_path)
        if not heif_file:
            print(f"Could not read HEIF file or no images found in: {image_path}")
            return None
        image = heif_file[0].to_pillow()

        # Crop the image to the text area on the right
        width, height = image.size
        left = width * 0.55
        top = height * 0.2
        right = width * 0.95
        bottom = height * 0.8
        image_cropped = image.crop((left, top, right, bottom))

        extracted_text = pytesseract.image_to_string(image_cropped)
        lines = [
            line.strip() for line in extracted_text.strip().split("\n") if line.strip()
        ]

        title = "Unknown Title"
        artist = "Unknown Artist"
        release_year = 0

        if len(lines) >= 3:
            artist = lines[0]
            title = lines[1]
            # The third line contains the label and year
            year_search = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", lines[2])
            if year_search:
                release_year = int(year_search.group(1))

        return {
            "title": title.strip(),
            "artist": artist.strip(),
            "release_year": release_year,
        }

    except (IOError, pytesseract.TesseractError) as e:
        print(f"Error processing {image_path}: {e}")
        return None


def main():
    """
    Main function to extract album data from photos and create a JSON file.
    """
    print("Starting album data extraction...")
    heic_files = find_heic_files(PHOTOS_DIR)

    if not heic_files:
        print(f"No .HEIC files found in {PHOTOS_DIR}")
        return

    all_albums_data = []

    for image_path in heic_files:
        print(f"Processing {image_path}...")
        album_info = extract_album_info_from_image(image_path)

        if album_info and album_info["title"] != "Unknown Title":
            album_record = {
                "album_id": str(uuid.uuid4()),
                "title": album_info["title"],
                "artist": album_info["artist"],
                "release_year": album_info["release_year"],
                "cover_image_url": None,
                "streaming_link_spotify": None,
                "streaming_link_apple": None,
            }
            all_albums_data.append(album_record)
        else:
            print(f"Could not extract valid information from {image_path}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_albums_data, f, indent=4)

    print(f"Successfully extracted data for {len(all_albums_data)} albums.")
    print(f"Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
