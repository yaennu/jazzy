"""
Spec: recommendations.md > Frequency eligibility, Album selection, History reset

Tests for the core recommendation logic in send_recommendations.py.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from send_recommendations import get_eligible_frequencies, get_unsent_album


class TestGetEligibleFrequencies:
    """Spec: recommendations.md > Frequency eligibility"""

    def test_daily_is_always_eligible(self, mocker):
        """daily subscribers are always eligible."""
        # Pick a Wednesday
        fake_now = datetime(2026, 3, 4, 4, 0, tzinfo=timezone.utc)  # Wednesday
        mocker.patch("send_recommendations.datetime")
        mocker.patch("send_recommendations.datetime").now.return_value = fake_now
        # Re-import to patch properly
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = fake_now

        result = get_eligible_frequencies()
        assert "daily" in result

    def test_weekly_eligible_on_monday(self, mocker):
        """weekly subscribers are eligible only on Mondays."""
        monday = datetime(2026, 3, 2, 4, 0, tzinfo=timezone.utc)  # Monday
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = monday

        result = get_eligible_frequencies()
        assert "weekly" in result

    def test_weekly_not_eligible_on_tuesday(self, mocker):
        """weekly subscribers are NOT eligible on non-Mondays."""
        tuesday = datetime(2026, 3, 3, 4, 0, tzinfo=timezone.utc)  # Tuesday
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = tuesday

        result = get_eligible_frequencies()
        assert "weekly" not in result

    def test_monthly_eligible_on_first(self, mocker):
        """monthly subscribers are eligible only on the 1st."""
        first = datetime(2026, 3, 1, 4, 0, tzinfo=timezone.utc)
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = first

        result = get_eligible_frequencies()
        assert "monthly" in result

    def test_monthly_not_eligible_on_second(self, mocker):
        """monthly subscribers are NOT eligible on other days."""
        second = datetime(2026, 3, 2, 4, 0, tzinfo=timezone.utc)
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = second
        # March 2 is a Monday, so weekly will be there but monthly should not
        result = get_eligible_frequencies()
        assert "monthly" not in result

    def test_monday_first_has_all_frequencies(self, mocker):
        """When the 1st falls on a Monday, all three frequencies are eligible."""
        # June 1 2026 is a Monday
        monday_first = datetime(2026, 6, 1, 4, 0, tzinfo=timezone.utc)
        import send_recommendations
        mocker.patch.object(send_recommendations, "datetime")
        send_recommendations.datetime.now.return_value = monday_first

        result = get_eligible_frequencies()
        assert set(result) == {"daily", "weekly", "monthly"}


class TestGetUnsentAlbum:
    """Spec: recommendations.md > Album selection, History reset"""

    def _make_album(self, album_id, calendar_order):
        return {
            "album_id": album_id,
            "title": f"Album {album_id}",
            "artist": "Artist",
            "calendar_order": calendar_order,
        }

    def _mock_client(self, sent_ids, all_albums, last_order=None):
        """Create a mock Supabase client with canned responses."""
        client = MagicMock()

        # Mock: recommendations.select("album_id").eq("user_id", ...).execute()
        sent_chain = MagicMock()
        sent_chain.execute.return_value = MagicMock(
            data=[{"album_id": sid} for sid in sent_ids]
        )
        client.table.return_value.select.return_value.eq.return_value = sent_chain

        # Mock: albums.select("*").execute()
        albums_chain = MagicMock()
        albums_chain.execute.return_value = MagicMock(data=all_albums)

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "recommendations":
                mock_table.select.return_value.eq.return_value = sent_chain
                # For history reset: delete().eq().execute()
                mock_table.delete.return_value.eq.return_value.execute.return_value = None
            elif name == "albums":
                mock_table.select.return_value = albums_chain
            return mock_table

        client.table.side_effect = table_side_effect

        return client

    def test_picks_first_album_for_new_user(self, mocker):
        """First unsent album in calendar_order for a user with no history."""
        albums = [
            self._make_album("a1", 1),
            self._make_album("a2", 2),
            self._make_album("a3", 3),
        ]
        client = self._mock_client(sent_ids=[], all_albums=albums)

        # Mock _get_last_sent_order to return None (no history)
        mocker.patch("send_recommendations._get_last_sent_order", return_value=None)

        result = get_unsent_album(client, "user-1")
        assert result is not None
        assert result["album_id"] == "a1"

    def test_picks_next_album_after_last_sent(self, mocker):
        """Picks the next album whose calendar_order > last sent order."""
        albums = [
            self._make_album("a1", 1),
            self._make_album("a2", 2),
            self._make_album("a3", 3),
        ]
        client = self._mock_client(sent_ids=["a1"], all_albums=albums)

        mocker.patch("send_recommendations._get_last_sent_order", return_value=1)

        result = get_unsent_album(client, "user-1")
        assert result is not None
        assert result["album_id"] == "a2"

    def test_returns_none_when_no_albums_exist(self, mocker):
        """No albums available returns None."""
        client = self._mock_client(sent_ids=[], all_albums=[])
        mocker.patch("send_recommendations._get_last_sent_order", return_value=None)

        result = get_unsent_album(client, "user-1")
        assert result is None
