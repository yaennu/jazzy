"""
Tests for album data extraction using Ollama vision model.

These tests require a running Ollama instance with the granite3.2-vision model.
To run:  pytest tests/test_extract_album_data.py -v
To skip: pytest -m "not slow"
"""

import os
import pytest

# Allow imports from src/scripts/
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "scripts")
)

from extract_album_data import extract_album_info_from_image

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
PNG_DIR = os.path.join(PROJECT_ROOT, "data", "png-images")


def _image_path(filename):
    path = os.path.join(PNG_DIR, filename)
    if not os.path.exists(path):
        pytest.skip(f"Image not found: {path}")
    return path


# Expected values for each calendar page image
EXPECTED = {
    "IMG_7093.png": {
        "artist": "Various Artists",
        "title": "The Soul Of Jazz",
        "release_year": 1975,
    },
    "IMG_7094.png": {
        "artist": "Erroll Garner",
        "title": "The Best Of Garner",
        "release_year": 1963,
    },
    "IMG_7095.png": {
        "artist": "Wilbert Longmire",
        "title": "Sunny Side Up",
        "release_year": 1978,
    },
    "IMG_7905.png": {
        "artist": "Esther Phillips",
        "title": "Alone Again, Naturally",
        "release_year": 1972,
    },
}


@pytest.mark.slow
@pytest.mark.parametrize(
    "filename,expected",
    list(EXPECTED.items()),
    ids=list(EXPECTED.keys()),
)
def test_extract_album_info(filename, expected):
    image_path = _image_path(filename)
    result = extract_album_info_from_image(image_path)

    assert result is not None, f"Extraction returned None for {filename}"
    assert result["artist"] == expected["artist"], (
        f"Artist mismatch for {filename}: got '{result['artist']}', "
        f"expected '{expected['artist']}'"
    )
    assert result["title"] == expected["title"], (
        f"Title mismatch for {filename}: got '{result['title']}', "
        f"expected '{expected['title']}'"
    )
    assert result["release_year"] == expected["release_year"], (
        f"Year mismatch for {filename}: got {result['release_year']}, "
        f"expected {expected['release_year']}"
    )
