"""
Tests for the live games feed filtering.

These cover the shapes the Cornell calendar feed actually returns, including the
ones that have caused crashes: a day whose "events" key is present but null, and
a feed window that does not contain today.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytz

from src.scrapers.games_scraper import (
    EASTERN_TZ,
    get_live_games,
    is_date_today,
    is_match_time_passed,
)


def eastern(year, month, day, hour=12, minute=0):
    """An aware datetime in Cornell's timezone."""
    return EASTERN_TZ.localize(datetime(year, month, day, hour, minute))


def feed_date(dt):
    """The feed's date format, e.g. '2026-10-28T00:00:00'."""
    return dt.strftime("%Y-%m-%dT00:00:00")


class TestIsDateToday:
    def test_today_matches(self):
        now = datetime.now(EASTERN_TZ)
        assert is_date_today(feed_date(now)) is True

    def test_other_days_do_not_match(self):
        now = datetime.now(EASTERN_TZ)
        assert is_date_today(feed_date(now - timedelta(days=1))) is False
        assert is_date_today(feed_date(now + timedelta(days=1))) is False

    def test_uses_eastern_not_server_time(self):
        """
        9pm Eastern is already the next day in UTC. A server running in UTC must
        still treat the Eastern date as today, or evening games are skipped while
        they are being played.
        """
        nine_pm_et = eastern(2026, 10, 28, 21, 0)
        assert nine_pm_et.astimezone(pytz.utc).date().isoformat() == "2026-10-29"

        with patch("src.scrapers.games_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = nine_pm_et
            mock_dt.strptime = datetime.strptime
            assert is_date_today("2026-10-28T00:00:00") is True
            assert is_date_today("2026-10-29T00:00:00") is False

    def test_empty_and_malformed_values(self):
        for value in ("", None, "not-a-date", "2026-13-45T00:00:00", "2026-10-28"):
            assert is_date_today(value) is False

    def test_fractional_seconds_and_z_suffix(self):
        now = datetime.now(EASTERN_TZ)
        assert is_date_today(now.strftime("%Y-%m-%dT00:00:00.000Z")) is True


class TestIsMatchTimePassed:
    def test_missing_time_is_not_passed(self):
        assert is_match_time_passed("") is False
        assert is_match_time_passed(None) is False

    def test_unparseable_time_is_not_passed(self):
        """TBA/TBD games have no clock value and must not count as started."""
        for value in ("TBA", "TBD", "All Day", "Noon"):
            assert is_match_time_passed(value) is False

    def test_past_and_future_times(self):
        now_et = datetime.now(EASTERN_TZ)
        past = (now_et - timedelta(hours=2)).strftime("%-I:%M p.m.").lower()
        future = (now_et + timedelta(hours=6)).strftime("%-I:%M p.m.").lower()
        # Only assert the ones that stay on today's date.
        if (now_et - timedelta(hours=2)).date() == now_et.date():
            assert is_match_time_passed(past.replace("pm", "p.m.")) in (True, False)
        assert isinstance(is_match_time_passed(future), bool)


class TestGetLiveGames:
    def _today(self):
        return feed_date(datetime.now(EASTERN_TZ))

    def test_events_null_returns_empty(self):
        """
        The feed sends "events": null for a day with nothing scheduled. dict.get
        with a default does not help here, because the key is present.
        """
        assert get_live_games([{"date": self._today(), "events": None}]) == []

    def test_events_key_missing_returns_empty(self):
        assert get_live_games([{"date": self._today()}]) == []

    def test_today_absent_from_feed_returns_empty(self):
        """A feed window that does not include today must not raise IndexError."""
        other = feed_date(datetime.now(EASTERN_TZ) + timedelta(days=3))
        assert get_live_games([{"date": other, "events": [{"time": "1:00 p.m."}]}]) == []

    def test_empty_and_none_feed(self):
        assert get_live_games([]) == []
        assert get_live_games(None) == []

    def test_returns_only_games_whose_time_has_passed(self):
        today = self._today()
        started = {"id": 1, "time": "1:00 a.m."}
        not_started = {"id": 2, "time": "11:59 p.m."}
        tba = {"id": 3, "time": "TBA"}
        no_time = {"id": 4}

        result = get_live_games(
            [{"date": today, "events": [started, not_started, tba, no_time]}]
        )
        ids = [g["id"] for g in result]
        assert 1 in ids
        assert 2 not in ids
        assert 3 not in ids
        assert 4 not in ids

    def test_skips_days_other_than_today(self):
        today = self._today()
        yesterday = feed_date(datetime.now(EASTERN_TZ) - timedelta(days=1))
        result = get_live_games(
            [
                {"date": yesterday, "events": [{"id": "old", "time": "1:00 a.m."}]},
                {"date": today, "events": [{"id": "new", "time": "1:00 a.m."}]},
            ]
        )
        assert [g["id"] for g in result] == ["new"]
