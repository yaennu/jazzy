"""
Tests for the recommendation selection algorithm in send_recommendations.py.
Covers get_eligible_frequencies() and get_unsent_album().
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from send_recommendations import get_eligible_frequencies, get_unsent_album


# ---------------------------------------------------------------------------
# get_eligible_frequencies
# ---------------------------------------------------------------------------

class TestGetEligibleFrequencies:
    """Test that get_eligible_frequencies returns correct frequencies based on the current date."""

    @patch("send_recommendations.datetime")
    def test_daily_always_included(self, mock_datetime):
        """Daily frequency should always be present regardless of date."""
        # Wednesday, March 12, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 12, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "daily" in result

    @patch("send_recommendations.datetime")
    def test_weekly_on_monday(self, mock_datetime):
        """Weekly frequency should be included on Mondays."""
        # Monday, March 10, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 10, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "weekly" in result
        assert "daily" in result

    @patch("send_recommendations.datetime")
    def test_weekly_not_on_tuesday(self, mock_datetime):
        """Weekly frequency should NOT be included on non-Monday weekdays."""
        # Tuesday, March 11, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 11, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "weekly" not in result

    @patch("send_recommendations.datetime")
    def test_weekly_not_on_sunday(self, mock_datetime):
        """Weekly frequency should NOT be included on Sunday."""
        # Sunday, March 16, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "weekly" not in result

    @patch("send_recommendations.datetime")
    def test_monthly_on_first(self, mock_datetime):
        """Monthly frequency should be included on the 1st of the month."""
        # Saturday, March 1, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "monthly" in result
        assert "daily" in result

    @patch("send_recommendations.datetime")
    def test_monthly_not_on_second(self, mock_datetime):
        """Monthly frequency should NOT be included on days other than the 1st."""
        # Sunday, March 2, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 2, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert "monthly" not in result

    @patch("send_recommendations.datetime")
    def test_all_frequencies_on_monday_first(self, mock_datetime):
        """All three frequencies should be included when the 1st falls on a Monday."""
        # Monday, September 1, 2025
        mock_datetime.now.return_value = datetime(2025, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily", "weekly", "monthly"]

    @patch("send_recommendations.datetime")
    def test_only_daily_on_midweek_midmonth(self, mock_datetime):
        """Only daily should be returned on a non-Monday, non-1st date."""
        # Wednesday, March 19, 2025
        mock_datetime.now.return_value = datetime(2025, 3, 19, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily"]


# ---------------------------------------------------------------------------
# get_unsent_album  — helpers
# ---------------------------------------------------------------------------

def _make_album(album_id, title="Album", artist="Artist", calendar_order=None,
                spotify=None, apple=None):
    """Create a minimal album dict for testing."""
    return {
        "album_id": album_id,
        "title": title,
        "artist": artist,
        "calendar_order": calendar_order,
        "streaming_link_spotify": spotify,
        "streaming_link_apple": apple,
    }


def _mock_supabase(sent_ids, albums, last_sent_order=None):
    """Build a mock Supabase client with controlled responses.

    Parameters
    ----------
    sent_ids : list[str]
        Album IDs already recommended to the user.
    albums : list[dict]
        All albums returned by the albums query (should already have streaming links).
    last_sent_order : int | None
        The calendar_order of the most recently sent album.
    """
    client = MagicMock()

    # recommendations.select("album_id").eq("user_id", ...).execute()
    sent_response = MagicMock()
    sent_response.data = [{"album_id": aid} for aid in sent_ids]

    # albums.select("*").or_(...).execute()
    albums_response = MagicMock()
    albums_response.data = albums

    # recommendations.select(...).eq(...).order(...).limit(1).execute()  (last sent order)
    last_sent_response = MagicMock()
    if last_sent_order is not None:
        last_sent_response.data = [{"album_id": "x", "albums": {"calendar_order": last_sent_order}}]
    else:
        last_sent_response.data = []

    # Wire up the chained calls
    recommendations_table = MagicMock()
    albums_table = MagicMock()

    # recommendations.select("album_id").eq(...).execute()
    # recommendations.select("album_id, albums(calendar_order)").eq(...).order(...).limit(1).execute()
    def select_side_effect(columns):
        chain = MagicMock()
        if columns == "album_id":
            chain.eq.return_value.execute.return_value = sent_response
        else:
            chain.eq.return_value.order.return_value.limit.return_value.execute.return_value = last_sent_response
        return chain
    recommendations_table.select.side_effect = select_side_effect
    recommendations_table.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    # albums.select("*").or_(...).execute()
    albums_table.select.return_value.or_.return_value.execute.return_value = albums_response

    def table_side_effect(name):
        if name == "recommendations":
            return recommendations_table
        elif name == "albums":
            return albums_table
        return MagicMock()

    client.table.side_effect = table_side_effect
    client._recommendations_table = recommendations_table  # exposed for assertions
    return client


# ---------------------------------------------------------------------------
# get_unsent_album  — tests
# ---------------------------------------------------------------------------

class TestGetUnsentAlbum:
    """Test album selection logic for a given user."""

    def test_basic_selection_first_album(self):
        """When no albums have been sent, return the first album by calendar_order."""
        albums = [
            _make_album("a1", calendar_order=2, spotify="https://spotify/a1"),
            _make_album("a2", calendar_order=1, spotify="https://spotify/a2"),
            _make_album("a3", calendar_order=3, apple="https://apple/a3"),
        ]
        client = _mock_supabase(sent_ids=[], albums=albums, last_sent_order=None)
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        assert album["album_id"] == "a2"  # calendar_order=1 comes first
        assert is_rerun is False

    def test_calendar_ordering_picks_next(self):
        """After sending album with calendar_order=2, the next should be calendar_order=3."""
        albums = [
            _make_album("a1", calendar_order=1, spotify="https://spotify/a1"),
            _make_album("a2", calendar_order=2, spotify="https://spotify/a2"),
            _make_album("a3", calendar_order=3, spotify="https://spotify/a3"),
        ]
        client = _mock_supabase(
            sent_ids=["a1", "a2"],
            albums=albums,
            last_sent_order=2,
        )
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        assert album["album_id"] == "a3"
        assert is_rerun is False

    def test_wraparound_when_all_sent(self):
        """When all albums have been sent, history is cleared and the first album is returned."""
        albums = [
            _make_album("a1", calendar_order=1, spotify="https://spotify/a1"),
            _make_album("a2", calendar_order=2, apple="https://apple/a2"),
        ]
        client = _mock_supabase(
            sent_ids=["a1", "a2"],
            albums=albums,
            last_sent_order=2,
        )
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        # After clearing, all albums are unsent; first by calendar_order wins
        assert album["album_id"] == "a1"
        assert is_rerun is True
        # Verify delete was called on the recommendations table
        client._recommendations_table.delete.assert_called()

    def test_skips_albums_without_streaming_links(self):
        """Albums without any streaming link should not appear in the query results.

        The Supabase or_() filter ensures only albums with at least one link are returned.
        We verify the function handles a result set that already excludes linkless albums.
        """
        albums_with_links = [
            _make_album("a2", calendar_order=2, spotify="https://spotify/a2"),
        ]
        client = _mock_supabase(sent_ids=[], albums=albums_with_links, last_sent_order=None)
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        assert album["album_id"] == "a2"
        assert is_rerun is False

    def test_returns_none_when_no_albums_exist(self):
        """When there are no albums at all, return (None, False)."""
        client = _mock_supabase(sent_ids=[], albums=[], last_sent_order=None)
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is None
        assert is_rerun is False

    def test_null_calendar_order_sorted_last(self):
        """Albums with calendar_order=None should come after albums with a calendar_order."""
        albums = [
            _make_album("a1", calendar_order=None, spotify="https://spotify/a1"),
            _make_album("a2", calendar_order=5, spotify="https://spotify/a2"),
            _make_album("a3", calendar_order=3, apple="https://apple/a3"),
        ]
        client = _mock_supabase(sent_ids=[], albums=albums, last_sent_order=None)
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        assert album["album_id"] == "a3"  # calendar_order=3 is lowest non-null
        assert is_rerun is False

    def test_wraps_to_first_when_last_order_is_highest(self):
        """When last_sent_order exceeds all unsent albums, wrap to the first unsent."""
        albums = [
            _make_album("a1", calendar_order=1, spotify="https://spotify/a1"),
            _make_album("a2", calendar_order=2, spotify="https://spotify/a2"),
            _make_album("a3", calendar_order=3, spotify="https://spotify/a3"),
        ]
        # a3 was last sent (order=3), a1 and a2 already sent too — but a2 is still unsent
        client = _mock_supabase(
            sent_ids=["a1", "a3"],
            albums=albums,
            last_sent_order=3,
        )
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        # No unsent album has calendar_order > 3, so it wraps to first unsent
        assert album["album_id"] == "a2"
        assert is_rerun is False

    def test_only_one_album_sent_repeatedly(self):
        """When there is only one album, it wraps around and returns it again."""
        albums = [
            _make_album("a1", calendar_order=1, spotify="https://spotify/a1"),
        ]
        client = _mock_supabase(
            sent_ids=["a1"],
            albums=albums,
            last_sent_order=1,
        )
        album, is_rerun = get_unsent_album(client, "user-1")
        assert album is not None
        assert album["album_id"] == "a1"
        assert is_rerun is True
