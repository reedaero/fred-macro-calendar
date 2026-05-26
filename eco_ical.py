import os
import requests
from datetime import datetime
from ics import Calendar, Event
import pytz

# --- CONFIGURATION ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "167e15a7023c65abcfc5031b0a0d93c6")
OUTPUT_FILE = "major_us_eco_calendar.ics"

MAJOR_RELEASES = {
    175: "PCE Price Index (Personal Income & Outlays)",
    53:  "Gross Domestic Product (GDP)",
    10:  "Consumer Price Index (CPI)",
    46:  "Producer Price Index (PPI)",
    50:  "Employment Situation (Nonfarm Payrolls)",
    98:  "FOMC Meeting Minutes & Rate Decisions",
    323: "Advance Retail Sales"
}

def fetch_fred_releases():
    """Fetches upcoming and recent release dates from the FRED API."""
    if FRED_API_KEY == "YOUR_FRED_API_KEY_HERE" or not FRED_API_KEY:
        raise ValueError("Please provide a valid FRED API key.")

    # Format today's date as YYYY-MM-DD to force FRED to look forward
    today_str = datetime.today().strftime("%Y-%m-%d")

    url = "https://api.stlouisfed.org/fred/releases/dates"
    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": 1000,
        "include_release_dates_with_no_data": "true",
        "realtime_start": today_str,  # CRITICAL: Only pull data active from today forward
        "order_by": "release_date",
        "sort_order": "asc"          # Chronological order (soonest events first)
    }

    print(f"Fetching upcoming data from FRED API (Starting from {today_str})...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"FRED API Error ({response.status_code}): {response.text}")
        
    return response.json().get("release_dates", [])

def build_ical():
    """Filters FRED data and generates the .ics file."""
    try:
        raw_releases = fetch_fred_releases()
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return

    cal = Calendar()
    count = 0

    print("Filtering releases and generating iCal events...")
    for item in raw_releases:
        release_id = item.get("release_id")
        
        if release_id in MAJOR_RELEASES:
            release_name = MAJOR_RELEASES[release_id]
            date_str = item.get("date") 
            
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Double check to prevent any historical bleed-through
            if event_date.date() < datetime.today().date():
                continue
                
            event = Event()
            event.name = f"⚠️ ECO: {release_name}"
            event.begin = event_date.date()
            event.make_all_day()
            
            event.description = (
                f"Major US Government Economic Announcement.\n"
                f"FRED Release ID: {release_id}\n"
                f"Data Source: Federal Reserve Bank of St. Louis"
            )
            event.categories = {"Economic Calendar", "Macro"}
            
            cal.events.add(event)
            count += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())
        
    print(f"Success! Generated '{OUTPUT_FILE}' with {count} upcoming macro events.")

if __name__ == "__main__":
    build_ical()
