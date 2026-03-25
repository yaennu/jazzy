"""
Tests for the email template rendering in email_template.py.
Covers render_recommendation_email() with various album data combinations.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from email_template import render_recommendation_email


def _make_album(**overrides):
    """Create a full album dict with sensible defaults, applying overrides."""
    album = {
        "title": "Kind of Blue",
        "artist": "Miles Davis",
        "release_year": 1959,
        "cover_image_url": "https://example.com/kind-of-blue.jpg",
        "streaming_link_spotify": "https://open.spotify.com/album/1weenld61qoidwYuZ1GESA",
        "streaming_link_apple": "https://music.apple.com/album/kind-of-blue/268443092",
        "artist_summary": "Miles Davis was a legendary trumpeter.",
        "album_summary": "Kind of Blue is the best-selling jazz album of all time.",
    }
    album.update(overrides)
    return album


class TestRenderRecommendationEmail:
    """Test HTML rendering of the recommendation email template."""

    def test_all_fields_present(self):
        """When all album fields are provided, all sections should appear in the HTML."""
        album = _make_album()
        html = render_recommendation_email("Alice", album, "https://example.com/unsub")

        assert "Hey Alice!" in html
        assert "Kind of Blue" in html
        assert "Miles Davis" in html
        assert "(1959)" in html
        assert "https://example.com/kind-of-blue.jpg" in html
        assert "Listen on Spotify" in html
        assert "Listen on Apple Music" in html
        assert "About this album" in html
        assert "About the artist" in html
        assert "best-selling jazz album" in html
        assert "legendary trumpeter" in html
        assert "https://example.com/unsub" in html
        assert "Unsubscribe" in html

    def test_missing_cover_image(self):
        """When cover_image_url is None, no <img> tag should appear."""
        album = _make_album(cover_image_url=None)
        html = render_recommendation_email("Bob", album)

        assert "Bob" in html
        assert "<img" not in html
        assert "Kind of Blue" in html

    def test_missing_streaming_links(self):
        """When both streaming links are None, no streaming buttons should appear."""
        album = _make_album(streaming_link_spotify=None, streaming_link_apple=None)
        html = render_recommendation_email("Carol", album)

        assert "Listen on Spotify" not in html
        assert "Listen on Apple Music" not in html
        # Album info should still be present
        assert "Kind of Blue" in html
        assert "Miles Davis" in html

    def test_only_spotify_link(self):
        """When only Spotify is available, only the Spotify button should appear."""
        album = _make_album(streaming_link_apple=None)
        html = render_recommendation_email("Dan", album)

        assert "Listen on Spotify" in html
        assert "Listen on Apple Music" not in html

    def test_only_apple_link(self):
        """When only Apple Music is available, only the Apple button should appear."""
        album = _make_album(streaming_link_spotify=None)
        html = render_recommendation_email("Eve", album)

        assert "Listen on Spotify" not in html
        assert "Listen on Apple Music" in html

    def test_missing_summaries(self):
        """When both summaries are None, the summaries block should not appear."""
        album = _make_album(artist_summary=None, album_summary=None)
        html = render_recommendation_email("Frank", album)

        assert "About this album" not in html
        assert "About the artist" not in html

    def test_only_album_summary(self):
        """When only album_summary is provided, only that section appears."""
        album = _make_album(artist_summary=None)
        html = render_recommendation_email("Grace", album)

        assert "About this album" in html
        assert "About the artist" not in html

    def test_only_artist_summary(self):
        """When only artist_summary is provided, only that section appears."""
        album = _make_album(album_summary=None)
        html = render_recommendation_email("Hank", album)

        assert "About this album" not in html
        assert "About the artist" in html

    def test_missing_release_year(self):
        """When release_year is None, no year parenthetical should appear."""
        album = _make_album(release_year=None)
        html = render_recommendation_email("Ivy", album)

        assert "(1959)" not in html
        assert "Miles Davis" in html

    def test_unsubscribe_url_present(self):
        """When an unsubscribe URL is given, the unsubscribe link should appear."""
        album = _make_album()
        html = render_recommendation_email("Jack", album, "https://example.com/unsub?token=abc")

        assert "https://example.com/unsub?token=abc" in html
        assert "Unsubscribe" in html

    def test_unsubscribe_url_absent(self):
        """When unsubscribe_url is empty, no unsubscribe link should appear."""
        album = _make_album()
        html = render_recommendation_email("Kate", album, "")

        assert "Unsubscribe" not in html

    def test_xss_in_user_name(self):
        """User name with HTML/script tags should appear as literal text in the output.

        Note: The current template does NOT escape HTML. This test documents
        the current behavior — the injected tag will appear in the output.
        If escaping is added later, update this test accordingly.
        """
        album = _make_album()
        malicious_name = '<script>alert("xss")</script>'
        html = render_recommendation_email(malicious_name, album)

        # The template uses f-string interpolation without escaping,
        # so the script tag will be present verbatim in the HTML.
        assert '<script>alert("xss")</script>' in html

    def test_default_values_for_missing_title_and_artist(self):
        """When title and artist are missing from the dict, defaults should be used."""
        album = {}
        html = render_recommendation_email("Leo", album)

        assert "Unknown Album" in html
        assert "Unknown Artist" in html

    def test_html_structure(self):
        """The rendered email should be a valid HTML document."""
        album = _make_album()
        html = render_recommendation_email("Mia", album)

        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html

    def test_is_rerun_shows_archives_label(self):
        """When is_rerun is True, a 'From the archives' label should appear."""
        album = _make_album()
        html = render_recommendation_email("Nina", album, is_rerun=True)

        assert "From the archives" in html

    def test_not_rerun_hides_archives_label(self):
        """When is_rerun is False (default), no archives label should appear."""
        album = _make_album()
        html = render_recommendation_email("Oscar", album, is_rerun=False)

        assert "From the archives" not in html
