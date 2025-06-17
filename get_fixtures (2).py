import requests
import json
import os
from datetime import datetime, timedelta
import pytz
from typing import Optional
from dateutil import parser as _p2

from config import BASE_URL

# Load local timezones mapping from JSON
LOCAL_TIMEZONES = {}
try:
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "local_time.json"), "r") as f:
        LOCAL_TIMEZONES = json.load(f)
except Exception as e:
    print(f"⚠️ Could not load local_time.json: {e}")

# Compose scoreboard URL from config
ESPN_FIXTURES_URL = f"{BASE_URL}/{{}}/scoreboard"
IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc


def is_within_custom_window(match_time_utc: datetime) -> bool:
    """
    Return True if match_time_utc falls between 14:00 IST today and 13:59 IST tomorrow.
    """
    now_ist = datetime.now(IST)
    start_window = now_ist.replace(hour=14, minute=0, second=0, microsecond=0)
    if now_ist.hour < 14:
        start_window -= timedelta(days=1)
    end_window = start_window + timedelta(days=1) - timedelta(minutes=1)
    match_time_ist = match_time_utc.astimezone(IST)
    return start_window <= match_time_ist <= end_window


def parse_date_to_utc(iso_time: str) -> Optional[datetime]:
    """
    Parse an ISO8601 timestamp to a timezone-aware UTC datetime.
    """
    try:
        utc_time = datetime.fromisoformat(iso_time.rstrip("Z")).replace(tzinfo=UTC)
    except Exception:
        try:
            utc_time = _p2.parse(iso_time)
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=UTC)
            else:
                utc_time = utc_time.astimezone(UTC)
        except Exception as e:
            print(f"⚠️ Time conversion error: {e}")
            return None
    return utc_time


def get_fixtures(
    league: str = "eng.1",
    filter_by_window: bool = False,
    espn_date: Optional[str] = None,
) -> list:
    """
    Fetch fixtures for a league on a specific date (YYYYMMDD). If filter_by_window is True,
    only include matches in the 14:00 IST → 13:59 IST window.
    """
    try:
        print(f"📡 Fetching fixtures for {league} (date={espn_date})…")
        params = {}
        if espn_date:
            params["dates"] = espn_date

        url = ESPN_FIXTURES_URL.format(league)
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        events = data.get("events", [])

        fixtures = []
        for event in events:
            try:
                comps = event.get("competitions") or []
                if not comps:
                    print(f"⚠️ No competition data for event {event.get('id')}")
                    continue
                comp = comps[0]

                iso_time = comp.get("date")
                if not iso_time:
                    print(f"⚠️ Missing date for event {event.get('id')}")
                    continue

                match_time_utc = parse_date_to_utc(iso_time)
                if not match_time_utc:
                    continue

                if filter_by_window and not is_within_custom_window(match_time_utc):
                    continue

                # Prefer event-level league name, fallback to response header
                league_name = (
                    event.get("league", {})
                         .get("name")
                    or data.get("leagues", [{}])[0].get("name", "Unknown League")
                )

                tz_name = LOCAL_TIMEZONES.get(league_name, "UTC")
                local_tz = pytz.timezone(tz_name)
                local_dt = match_time_utc.astimezone(local_tz)
                local_time_str = local_dt.strftime("%H:%M")

                home = next(t for t in comp["competitors"] if t.get("homeAway") == "home")
                away = next(t for t in comp["competitors"] if t.get("homeAway") == "away")

                # Safely extract status
                status = (
                    event.get("status", {})
                         .get("type", {})
                         .get("name")
                    or ""
                ).upper()

                fixtures.append({
                    "match_id":     event.get("id"),
                    "home":          home["team"]["displayName"],
                    "away":          away["team"]["displayName"],
                    "local_time":    local_time_str,
                    "utc_time":      match_time_utc.strftime("%H:%M"),
                    "status":        status,
                    "league_code":   league,
                    "league":        league_name,
                    "home_score":    int(home.get("score", 0)),
                    "away_score":    int(away.get("score", 0)),
                    "utc_datetime":  match_time_utc.isoformat(),
                })
            except Exception as e:
                print(f"⚠️ Skipping event due to parsing error: {e}")
                continue

        # Deduplicate by match_id
        unique = {m["match_id"]: m for m in fixtures}
        final = list(unique.values())
        print(f"✅ {len(final)} fixtures fetched.")
        return final

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching fixtures: {e}")
        return []
