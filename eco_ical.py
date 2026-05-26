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
    if not FRED_API_KEY:
        raise ValueError("Please provide a valid FRED API key.")

    # Format today's date as YYYY-MM-DD to force FRED to look forward
    today_str = datetime.today().strftime("%Y-%m-%d")

    url = "https://api.stlouisfed.org/fred/releases/dates"
    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "realtime_start": today_str,
        "limit": 1000
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("release_dates", [])
    except Exception as e:
        print(f"Error fetching data from FRED: {e}")
        return []

def generate_ical():
    print("Starting FRED data fetch...")
    releases = fetch_fred_releases()
    
    if not releases:
        print("No release data found or failed to fetch.")
        return

    cal = Calendar()
    tz = pytz.timezone("US/Eastern")
    count = 0

    for r in releases:
        release_id = r.get("release_id")
        if release_id in MAJOR_RELEASES:
            event_name = MAJOR_RELEASES[release_id]
            date_str = r.get("date") # YYYY-MM-DD
            
            try:
                # Parse date and set event for 8:30 AM EST (standard release time)
                release_date = datetime.strptime(date_str, "%Y-%m-%d")
                localized_datetime = tz.localize(datetime(release_date.year, release_date.month, release_date.day, 8, 30))
                
                event = Event()
                event.name = f"⚠️ {event_name}"
                event.begin = localized_datetime
                event.duration = {"minutes": 30}
                event.description = f"Macro Data Release\nFRED Release ID: {release_id}"
                
                cal.events.add(event)
                count += 1
            except Exception as e:
                print(f"Skipping malformed event on date {date_str}: {e}")

    if count > 0:
        with open(OUTPUT_FILE, "w") as f:
            f.writelines(cal.serialize_iter())
        print(f"Success! Generated {OUTPUT_FILE} with {count} upcoming events.")
    else:
        print("No matching major release dates found to save.")

if __name__ == "__main__":
    generate_ical()
