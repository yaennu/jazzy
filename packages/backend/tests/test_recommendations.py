"""
Tests for the recommendation selection algorithm in send_recommendations.py.
Covers get_eligible_frequencies() and get_unsent_album().
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Add source directories to sys.path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scripts"))

from send_recommendations import get_eligible_frequencies, get_unsent_album


# ---------------------------------------------------------------------------
# get_eligible_frequencies
# ---------------------------------------------------------------------------

class TestGetEligibleFrequencies:
    """Test that the correct frequencies are returned based on the current date."""

    @patch("send_recommendations.datetime")
    def test_regular_weekday_returns_daily_only(self, mock_dt):
        """A normal Tuesday should only include 'daily'."""
        # 2026-03-10 is a Tuesday
        mock_dt.now.return_value = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily"]

    @patch("send_recommendations.datetime")
    def test_monday_returns_daily_and_weekly(self, mock_dt):
        """Mondays should include both 'daily' and 'weekly'."""
        # 2026-03-09 is a Monday
        mock_dt.now.return_value = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily", "weekly"]

    @patch("send_recommendations.datetime")
    def test_first_of_month_non_monday_returns_daily_and_monthly(self, mock_dt):
        """The 1st of the month (not a Monday) should include 'daily' and 'monthly'."""
        # 2026-04-01 is a Wednesday
        mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily", "monthly"]

    @patch("send_recommendations.datetime")
    def test_first_of_month_monday_returns_all_three(self, mock_dt):
        """The 1st of the month that is also a Monday should include all three."""
        # 2026-06-01 is a Monday
        mock_dt.now.return_value = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily", "weekly", "monthly"]

    @patch("send_recommendations.datetime")
    def test_daily_always_present(self, mock_dt):
        """'daily' should always be in the returned list regardless of day."""
        for day in range(1, 8):
            mock_dt.now.return_value = datetime(2026, 3, day, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = get_eligible_frequencies()
            assert "daily" in result, f"'daily' missing on 2026-03-{day:02d}"

    @patch("send_recommendations.datetime")
    def test_saturday_returns_daily_only(self, mock_dt):
        """Saturday should only return 'daily'."""
        # 2026-03-14 is a Saturday
        mock_dt.now.return_value = datetime(2026, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily"]

    @patch("send_recommendations.datetime")
    def test_sunday_returns_daily_only(self, mock_dt):
        """Sunday should only return 'daily'."""
        # 2026-03-15 is a Sunday
        mock_dt.now.return_value = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert result == ["daily"]

    @patch("send_recommendations.datetime")
    def test_second_of_month_no_monthly(self, mock_dt):
        """The 2nd of the month should not include 'monthly'."""
        # 2026-03-02 is a Monday
        mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = get_eligible_frequencies()
        assert "monthly" not in result


# ---------------------------------------------------------------------------
# Helpers for get_unsent_album tests
# ---------------------------------------------------------------------------

def _make_album(album_id, title, artist, calendar_order=None, spotify=None, apple=None):
    """Create a minimal album dict for testing."""
    return {
        "album_id": album_id,
        "title": title,
        "artist": artist,
        "calendar_order": calendar_order,
        "streaming_link_spotify": spotify,
        "streaming_link_apple": apple,
        "release_year": 2000,
    }


def _make_mock_client(sent_ids, albums, last_sent_album=None):
    """Build a mock Supabase client that returns controlled data.

    Parameters
    ----------
    sent_ids : list[str]
        Album IDs already sent to the user.
    albums : list[dict]
        All albums returned by the albums query (already filtered to have links).
    last_sent_album : dict | None
        The album data for the most recently sent recommendation
        (used by _get_last_sent_order).
    """
    client = MagicMock()

    # Mock recommendations select (sent album IDs)
    sent_response = MagicMock()
    sent_response.data = [{"album_id": aid} for aid in sent_ids]

    # Mock albums select (albums with streaming links)
    albums_response = MagicMock()
    albums_response.data = albums

    # Mock _get_last_sent_order query
    last_sent_response = MagicMock()
    if last_sent_album is not None:
        last_sent_response.data = [{
            "album_id": last_sent_album["album_id"],
            "albums": {"calendar_order": last_sent_album.get("calendar_order")},
        }]
    else:
        last_sent_response.data = []

    # Chain mock: client.table("recommendations").select(...).eq(...).execute()
    # and        client.table("albums").select(...).or_(...).execute()
    # and        client.table("recommendations").select(...).eq(...).order(...).limit(...).execute()
    def table_side_effect(table_name):
        mock_table = MagicMock()

        if table_name == "recommendations":
            # We need to differentiate between the two recommendation queries:
            # 1. select("album_id").eq("user_id", ...).execute() — sent IDs
            # 2. select("album_id, albums(calendar_order)").eq(...).order(...).limit(...).execute() — last sent
            # 3. delete().eq(...).execute() — clear history
            def select_side_effect(columns):
                chain = MagicMock()
                if "albums(calendar_order)" in columns:
                    # _get_last_sent_order query
                    chain.eq.return_value = chain
                    chain.order.return_value = chain
                    chain.limit.return_value = chain
                    chain.execute.return_value = last_sent_response
                else:
                    # sent album IDs query
                    chain.eq.return_value = chain
                    chain.execute.return_value = sent_response
                return chain

            mock_table.select.side_effect = select_side_effect

            # delete chain for wraparound
            delete_chain = MagicMock()
            delete_chain.eq.return_value = delete_chain
            delete_chain.execute.return_value = MagicMock()
            mock_table.delete.return_value = delete_chain
        elif table_name == "albums":
            chain = MagicMock()
            chain.select.return_value = chain
            chain.or_.return_value = chain
            chain.execute.return_value = albums_response
            return chain

        return mock_table

    client.table.side_effect = table_side_effect
    return client


# ---------------------------------------------------------------------------
# get_unsent_album
# ---------------------------------------------------------------------------

class TestGetUnsentAlbum:
    """Test the algorithm that picks the next album for a user."""

    def test_basic_selection_first_album(self):
        """With no previous recommendations, should return the album with lowest calendar_order."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=2, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=1, spotify="http://sp/a2"),
            _make_album("a3", "Album C", "Artist C", calendar_order=3, apple="http://am/a3"),
        ]
        client = _make_mock_client(sent_ids=[], albums=albums, last_sent_album=None)

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert album["album_id"] == "a2"  # calendar_order=1 comes first
        assert is_rerun is False

    def test_calendar_ordering_respects_last_sent(self):
        """Should pick the next album after the last sent one in calendar_order."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=1, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=2, spotify="http://sp/a2"),
            _make_album("a3", "Album C", "Artist C", calendar_order=3, spotify="http://sp/a3"),
        ]
        last_sent = _make_album("a1", "Album A", "Artist A", calendar_order=1)
        client = _make_mock_client(
            sent_ids=["a1"],
            albums=albums,
            last_sent_album=last_sent,
        )

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert album["album_id"] == "a2"  # next after calendar_order=1
        assert is_rerun is False

    def test_wraparound_when_all_sent(self):
        """When all albums have been sent, history is cleared and cycle restarts."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=1, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=2, spotify="http://sp/a2"),
        ]
        last_sent = _make_album("a2", "Album B", "Artist B", calendar_order=2)
        client = _make_mock_client(
            sent_ids=["a1", "a2"],
            albums=albums,
            last_sent_album=last_sent,
        )

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert is_rerun is True
        # After clearing, all albums are unsent; last_order=2, so it wraps to first
        assert album["album_id"] == "a1"

    def test_skips_albums_without_streaming_links(self):
        """Albums with no streaming links are not included (they are excluded by the DB query)."""
        # Only albums with at least one link are returned by the query mock
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=1, spotify="http://sp/a1"),
            # a2 has no links so it would not be in the query results
        ]
        client = _make_mock_client(sent_ids=[], albums=albums, last_sent_album=None)

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert album["album_id"] == "a1"
        assert is_rerun is False

    def test_returns_none_when_no_albums_exist(self):
        """If there are no albums at all, should return (None, False)."""
        client = _make_mock_client(sent_ids=[], albums=[], last_sent_album=None)

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is None
        assert is_rerun is False

    def test_null_calendar_order_sorted_last(self):
        """Albums with no calendar_order should be sorted after those with one."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=None, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=2, spotify="http://sp/a2"),
            _make_album("a3", "Album C", "Artist C", calendar_order=1, spotify="http://sp/a3"),
        ]
        client = _make_mock_client(sent_ids=[], albums=albums, last_sent_album=None)

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert album["album_id"] == "a3"  # calendar_order=1 first

    def test_picks_next_after_gap_in_calendar_order(self):
        """When some albums in the sequence have been sent, the next unsent one is picked."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=1, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=2, spotify="http://sp/a2"),
            _make_album("a3", "Album C", "Artist C", calendar_order=5, spotify="http://sp/a3"),
            _make_album("a4", "Album D", "Artist D", calendar_order=10, spotify="http://sp/a4"),
        ]
        last_sent = _make_album("a2", "Album B", "Artist B", calendar_order=2)
        client = _make_mock_client(
            sent_ids=["a1", "a2"],
            albums=albums,
            last_sent_album=last_sent,
        )

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        assert album["album_id"] == "a3"  # next unsent with calendar_order > 2
        assert is_rerun is False

    def test_wraps_to_first_when_last_order_past_all_unsent(self):
        """When last_order is higher than all unsent albums, wraps around to the first."""
        albums = [
            _make_album("a1", "Album A", "Artist A", calendar_order=1, spotify="http://sp/a1"),
            _make_album("a2", "Album B", "Artist B", calendar_order=5, spotify="http://sp/a2"),
            _make_album("a3", "Album C", "Artist C", calendar_order=10, spotify="http://sp/a3"),
        ]
        # a2 and a3 have been sent; last sent was a3 (order=10). Only a1 (order=1) is unsent.
        last_sent = _make_album("a3", "Album C", "Artist C", calendar_order=10)
        client = _make_mock_client(
            sent_ids=["a2", "a3"],
            albums=albums,
            last_sent_album=last_sent,
        )

        album, is_rerun = get_unsent_album(client, "user-1")

        assert album is not None
        # a1 has calendar_order=1, which is not > 10, so it falls through to unsent[0]
        assert album["album_id"] == "a1"
        assert is_rerun is False
