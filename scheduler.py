# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import json

from telegram_bot import send_fixtures, send_keepalive, send_message
from get_fixtures import get_fixtures
from get_results import post_results
from storage import save_match_to_db
from config import PERSONAL_CHAT_ID

IST = pytz.timezone("Asia/Kolkata")

def load_leagues():
    try:
        with open("league_ids.json") as f:
            return json.load(f)["leagues"]
    except Exception as e:
        print(f"[{datetime.now(IST)}] ❌ Failed to load league IDs: {e}")
        return []

def post_daily_fixtures():
    fixtures = []
    for league in load_leagues():
        fixtures.extend(
            get_fixtures(league=league, filter_by_window=True)
        )

    if not fixtures:
        print(f"[{datetime.now(IST)}] ℹ️ No fixtures to post in this window.")
        return

    send_fixtures(fixtures)
    for m in fixtures:
        # Save only the fields post_results needs
        save_match_to_db({
            "match_id":     m["match_id"],
            "league_code":  m["league_code"],
            "home":         m["home"],
            "away":         m["away"],
            "utc_datetime": m["utc_datetime"],
        })
        send_message(
            text=f"🔖 Tracking match: {m['home']} vs {m['away']} at {m['local_time']}",
            chat_id=PERSONAL_CHAT_ID
        )

def start():
    try:
        scheduler = BackgroundScheduler(timezone=IST)
        # Your custom 24 h window start (e.g. 14:00 IST as in your get_fixtures)
        scheduler.add_job(post_daily_fixtures, "cron", hour=14, minute=0)
        # Every 15 min, check for finished/postponed matches
        scheduler.add_job(post_results, "interval", minutes=15)
        # Heartbeat every 4 min
        scheduler.add_job(send_keepalive, "interval", minutes=4)
        scheduler.start()
        print(f"[{datetime.now(IST)}] ⏱️ Scheduler started...")
    except Exception as e:
        print(f"[{datetime.now(IST)}] ❌ Scheduler failed to start: {e}")

if __name__ == "__main__":
    start()
