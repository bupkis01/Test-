from datetime import datetime, timedelta
import pytz

from get_fixtures import get_fixtures
from storage import get_tracked_matches, remove_match_from_db
from telegram_bot import send_results

UTC = pytz.utc

def post_results():
    """Fetch and post any matches that have just finished (and clean up postponed)."""
    now_utc = datetime.now(UTC)
    finished = []

    for stored in get_tracked_matches():
        start_iso = stored.get("utc_datetime")
        league    = stored.get("league_code")
        match_id  = stored.get("match_id")

        if not (start_iso and league and match_id):
            print(f"⚠️ Skipping incomplete entry: {stored}")
            continue

        try:
            start_dt = datetime.fromisoformat(start_iso)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=UTC)
            else:
                start_dt = start_dt.astimezone(UTC)
        except Exception as e:
            print(f"⚠️ Bad utc_datetime `{start_iso}`: {e}")
            continue

        # 1) Not yet kicked off
        if now_utc < start_dt:
            continue

        # 2) Postponed cleanup: 15–110 min after start but still scheduled
        if now_utc < start_dt + timedelta(minutes=110):
            if now_utc >= start_dt + timedelta(minutes=15):
                espn_date = start_dt.strftime("%Y%m%d")
                events = get_fixtures(league=league, filter_by_window=False, espn_date=espn_date)
                evt = next((e for e in events if e.get("match_id") == match_id), None)
                status = (evt or {}).get("status", "").upper()
                if not evt or status in ("STATUS_SCHEDULED", "SCHEDULED"):
                    print(f"ℹ️ Match {match_id} seems postponed; removing from tracking.")
                    remove_match_from_db(stored)
            continue

        # 3) ≥110 minutes after start → check for any “ended” status
        espn_date = start_dt.strftime("%Y%m%d")
        events   = get_fixtures(league=league, filter_by_window=False, espn_date=espn_date)

        completed_codes = {
            "STATUS_FINAL", "FINAL",
            "STATUS_FULL_TIME", "FULL_TIME"
        }
        updated = next(
            (e for e in events
             if e.get("match_id") == match_id
             and (
                 e.get("status") in completed_codes
                 or e.get("status_type", {}).get("completed")
             )
            ),
            None
        )

        if updated:
            finished.append(updated)
            remove_match_from_db(stored)

    if finished:
        send_results(finished)
    else:
        print("ℹ️ No results to post right now.")
