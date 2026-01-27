"""
Extracts album information from HEIC photos and generates a SQL script.

This script first converts all .HEIC images in a specified directory to PNG format,
then processes the PNG images to extract album title, artist, and release year using OCR,
and finally saves the structured data into a SQL script that can be used to insert data into a Supabase database.
"""

import os
import re
import pytesseract
import pillow_heif
from PIL import Image


# --- Configuration ---
# Ensure Tesseract OCR is installed on your system.
# On macOS: brew install tesseract
# You may also need to set the command path if it's not in your system's PATH.
# pytesseract.pytesseract.tesseract_cmd = r'/path/to/your/tesseract'

# Construct absolute paths from the script's location to make it runnable from anywhere
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

HEIC_PHOTOS_DIR = os.path.join(PROJECT_ROOT, "data", "heic-images")
PNG_PHOTOS_DIR = os.path.join(PROJECT_ROOT, "data", "png-images")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "albums.sql")


def convert_heic_to_png(source_dir, dest_dir):
    """Converts all HEIC images in the source directory to PNG format in the destination directory."""
    print(f"Starting HEIC to PNG conversion from {source_dir} to {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)
    heic_files = [f for f in os.listdir(source_dir) if f.upper().endswith(".HEIC")]

    if not heic_files:
        print(f"No .HEIC files found in {source_dir}")
        return

    for filename in heic_files:
        heic_path = os.path.join(source_dir, filename)
        png_filename = os.path.splitext(filename)[0] + ".png"
        png_path = os.path.join(dest_dir, png_filename)

        try:
            heif_file = pillow_heif.read_heif(heic_path)
            image = heif_file[0].to_pillow()
            image.save(png_path, "PNG")
            print(f"Converted {heic_path} to {png_path}")
        except Exception as e:
            print(f"Could not convert {heic_path}: {e}")
    print("HEIC to PNG conversion completed.")


def find_png_files(directory):
    """Finds all .PNG files in the specified directory."""
    png_files = []
    for filename in os.listdir(directory):
        if filename.upper().endswith(".PNG"):
            png_files.append(os.path.join(directory, filename))
    return png_files


def extract_album_info_from_image(image_path):
    """
    Extracts album title, artist, and release year from an image using OCR.
    """
    try:
        image = Image.open(image_path)

        # Crop the image to the text area on the right
        width, height = image.size
        left = int(width * 0.55)
        top = int(height * 0.2)
        right = int(width * 0.95)
        bottom = int(height * 0.8)
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
    Main function to extract album data from photos and create a SQL script.
    """
    # First, convert HEIC images to PNG
    convert_heic_to_png(HEIC_PHOTOS_DIR, PNG_PHOTOS_DIR)

    print("\nStarting album data extraction from PNG images...")
    png_files = find_png_files(PNG_PHOTOS_DIR)

    if not png_files:
        print(f"No .PNG files found in {PNG_PHOTOS_DIR}")
        return

    all_sql_inserts = []

    for image_path in png_files:
        print(f"Processing {image_path}...")
        album_info = extract_album_info_from_image(image_path)

        if album_info and album_info["title"] != "Unknown Title":
            # Escape single quotes in title and artist for SQL
            title = album_info["title"].replace("'", "''")
            artist = album_info["artist"].replace("'", "''")
            release_year = album_info["release_year"]

            # Construct the SQL INSERT statement
            sql_insert = (
                f"INSERT INTO albums (title, artist, release_year) "
                f"VALUES ('{title}', '{artist}', {release_year});"
            )
            all_sql_inserts.append(sql_insert)
        else:
            print(f"Could not extract valid information from {image_path}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for insert_statement in all_sql_inserts:
            f.write(insert_statement + "\n")

    print(f"\nSuccessfully generated {len(all_sql_inserts)} SQL INSERT statements.")
    print(f"Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
