import os
import requests
from bs4 import BeautifulSoup

# Telegram credentials from secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# JNTUK results site
URL = "https://jntukresults.edu.in/"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Failed to send message: {e}")

def check_results():
    try:
        resp = requests.get(URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        send_message(f"❌ Failed to fetch JNTUK site: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the first table
    table = soup.find("table")
    if not table:
        send_message("❌ Could not find results table on JNTUK site.")
        return

    # Get all rows
    rows = table.find_all("tr")

    # Skip header if needed
    first_row = None
    for row in rows:
        cols = row.find_all("td")
        if cols and row.find("a"):  # ensure it has a link
            first_row = row
            break

    if not first_row:
        send_message("❌ Could not extract the first result row.")
        return

    # Extract text + link
    title = first_row.get_text(strip=True)
    link = first_row.find("a")["href"]

    # Make full URL if relative
    if not link.startswith("http"):
        link = URL.rstrip("/") + "/" + link.lstrip("/")

    # Store last seen result
    state_file = "last_result.txt"
    last_result = None
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last_result = f.read().strip()

    # Compare and notify
    if title != last_result:
        message = f"📢 New JNTUK Result Released:\n\n{title}\n🔗 {link}"
        send_message(message)
        with open(state_file, "w") as f:
            f.write(title)
    else:
        print("No new result found.")

if __name__ == "__main__":
    check_results()
