"""
Tests for email template rendering in email_template.py.
Covers render_recommendation_email() with various combinations of fields.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scripts"))

from email_template import render_recommendation_email


def _make_album(**overrides):
    """Create a full album dict with sensible defaults, applying any overrides."""
    album = {
        "title": "Kind of Blue",
        "artist": "Miles Davis",
        "release_year": 1959,
        "cover_image_url": "https://example.com/cover.jpg",
        "streaming_link_spotify": "https://open.spotify.com/album/abc",
        "streaming_link_apple": "https://music.apple.com/album/xyz",
        "artist_summary": "Miles Davis was a legendary trumpeter.",
        "album_summary": "Kind of Blue is a masterpiece of modal jazz.",
    }
    album.update(overrides)
    return album


class TestRenderRecommendationEmail:
    """Test the HTML output of render_recommendation_email()."""

    def test_all_fields_present(self):
        """With all fields provided, the email includes title, artist, year, cover, links, summaries."""
        album = _make_album()
        html = render_recommendation_email("Alice", album, "https://example.com/unsub")

        assert "Hey Alice!" in html
        assert "Kind of Blue" in html
        assert "Miles Davis" in html
        assert "(1959)" in html
        assert 'src="https://example.com/cover.jpg"' in html
        assert "Listen on Spotify" in html
        assert "https://open.spotify.com/album/abc" in html
        assert "Listen on Apple Music" in html
        assert "https://music.apple.com/album/xyz" in html
        assert "About this album" in html
        assert "Kind of Blue is a masterpiece of modal jazz." in html
        assert "About the artist" in html
        assert "Miles Davis was a legendary trumpeter." in html

    def test_missing_cover_image(self):
        """When cover_image_url is None, the cover image element should be absent."""
        album = _make_album(cover_image_url=None)
        html = render_recommendation_email("Bob", album, "")

        assert "Hey Bob!" in html
        assert "Kind of Blue" in html
        assert "album cover" not in html

    def test_missing_streaming_links(self):
        """When both streaming links are None, no streaming buttons should appear."""
        album = _make_album(streaming_link_spotify=None, streaming_link_apple=None)
        html = render_recommendation_email("Charlie", album, "")

        assert "Listen on Spotify" not in html
        assert "Listen on Apple Music" not in html

    def test_only_spotify_link(self):
        """When only Spotify link is present, only the Spotify button should appear."""
        album = _make_album(streaming_link_apple=None)
        html = render_recommendation_email("Dana", album, "")

        assert "Listen on Spotify" in html
        assert "Listen on Apple Music" not in html

    def test_only_apple_music_link(self):
        """When only Apple Music link is present, only the Apple button should appear."""
        album = _make_album(streaming_link_spotify=None)
        html = render_recommendation_email("Eve", album, "")

        assert "Listen on Spotify" not in html
        assert "Listen on Apple Music" in html

    def test_missing_summaries(self):
        """When both summaries are None, the editorial block should be absent."""
        album = _make_album(artist_summary=None, album_summary=None)
        html = render_recommendation_email("Frank", album, "")

        assert "About this album" not in html
        assert "About the artist" not in html

    def test_only_album_summary(self):
        """When only album_summary is present, only 'About this album' appears."""
        album = _make_album(artist_summary=None)
        html = render_recommendation_email("Grace", album, "")

        assert "About this album" in html
        assert "About the artist" not in html

    def test_only_artist_summary(self):
        """When only artist_summary is present, only 'About the artist' appears."""
        album = _make_album(album_summary=None)
        html = render_recommendation_email("Hank", album, "")

        assert "About this album" not in html
        assert "About the artist" in html

    def test_unsubscribe_url_included(self):
        """When an unsubscribe URL is provided, it should appear as a link."""
        album = _make_album()
        html = render_recommendation_email("Ivy", album, "https://example.com/unsub?token=abc")

        assert "Unsubscribe" in html
        assert "https://example.com/unsub?token=abc" in html

    def test_no_unsubscribe_url(self):
        """When unsubscribe_url is empty, the unsubscribe link should be absent."""
        album = _make_album()
        html = render_recommendation_email("Jack", album, "")

        assert "Unsubscribe" not in html

    def test_xss_in_user_name(self):
        """User name with HTML/script tags should appear literally (template uses f-string, not escaped).

        Note: The current template does NOT escape HTML. This test documents the
        current behavior. If escaping is added later, this test should be updated.
        """
        album = _make_album()
        malicious_name = '<script>alert("xss")</script>'
        html = render_recommendation_email(malicious_name, album, "")

        # The f-string template inserts the name as-is, so the script tag appears literally
        assert '<script>alert("xss")</script>' in html

    def test_missing_title_and_artist_use_defaults(self):
        """When title and artist are missing from the album dict, defaults are used."""
        album = {}
        html = render_recommendation_email("Kim", album, "")

        assert "Unknown Album" in html
        assert "Unknown Artist" in html

    def test_no_release_year(self):
        """When release_year is None, no year parenthetical should appear."""
        album = _make_album(release_year=None)
        html = render_recommendation_email("Leo", album, "")

        assert "Miles Davis" in html
        # The year text should not include parentheses with nothing
        assert "()" not in html

    def test_is_rerun_shows_from_archives(self):
        """When is_rerun is True, 'From the archives' banner should appear."""
        album = _make_album()
        html = render_recommendation_email("Mia", album, "", is_rerun=True)

        assert "From the archives" in html

    def test_not_rerun_hides_archives_banner(self):
        """When is_rerun is False, 'From the archives' should not appear."""
        album = _make_album()
        html = render_recommendation_email("Mia", album, "", is_rerun=False)

        assert "From the archives" not in html

    def test_html_structure(self):
        """The output should be a well-formed HTML document."""
        album = _make_album()
        html = render_recommendation_email("Test", album, "")

        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html
