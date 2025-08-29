#!/usr/bin/env python3
"""
jntuk_notifier.py
Checks jntukresults.edu.in top table row for new BTECH entry and sends Telegram message.
Run once (for GitHub Actions): python jntuk_notifier.py --once
"""

import os
import time
import argparse
import requests
from bs4 import BeautifulSoup

# CONFIG (via env vars)
URL = os.getenv("JNTUK_URL", "https://jntukresults.edu.in/")
LAST_FILE = os.getenv("LAST_FILE", "last_result.txt")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "1800"))  # 30 minutes
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JNTUK-Result-Notifier/1.0)"
}

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: BOT_TOKEN or CHAT_ID not set.")
        return False
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(api_url, data=payload, timeout=15)
        r.raise_for_status()
        print("Telegram message sent.")
        return True
    except Exception as e:
        print("Failed to send Telegram message:", e)
        return False

def fetch_first_row():
    try:
        print(f"Fetching: {URL}")
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("table")
        if not table:
            print("No table element found on page.")
            return None, None, None
        tbody = table.find("tbody") or table
        first_tr = tbody.find("tr")
        if not first_tr:
            print("No rows found inside the results table.")
            return None, None, None
        cols = first_tr.find_all(["td", "th"])
        publish_date = cols[1].get_text(strip=True) if len(cols) > 1 else ""
        course = cols[2].get_text(strip=True) if len(cols) > 2 else ""
        details = cols[5].get_text(strip=True) if len(cols) > 5 else " ".join([c.get_text(strip=True) for c in cols[2:]])
        print("Extracted top row:", publish_date, "|", course, "|", (details[:80] + "..") if len(details)>80 else details)
        return publish_date, course, details
    except Exception as e:
        print("Error fetching/parsing site:", e)
        return None, None, None

def load_last():
    try:
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last(value):
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(value)

def check_and_notify():
    publish_date, course, details = fetch_first_row()
    if not any([publish_date, course, details]):
        print("Skipping: could not get valid row data.")
        return
    key = f"{publish_date}||{course}||{details}"
    last = load_last()
    if key != last and "BTECH" in course.upper():
        message = (
            "🔔 <b>New B.Tech Result Published</b>\n\n"
            f"📅 <b>Publish Date:</b> {publish_date}\n"
            f"📘 <b>Details:</b> {details}\n\n"
            f"🔗 <a href='{URL}'>Open results page</a>"
        )
        print("New B.Tech result detected. Sending Telegram message...")
        ok = send_telegram_message(message)
        if ok:
            save_last(key)
            print("Saved new latest result.")
        else:
            print("Failed to notify; will retry next run.")
    else:
        print("No new B.Tech result detected (or top row is not BTECH).")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit (use in GitHub Actions)")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL, help="Polling interval in seconds")
    args = parser.parse_args()

    if args.once:
        check_and_notify()
        return

    print(f"Starting daemon with interval {args.interval}s. Press Ctrl+C to stop.")
    while True:
        check_and_notify()
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
