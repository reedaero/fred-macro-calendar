#!/usr/bin/env python3
import yfinance as yf
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import time
import os

# ================== ALERT SETTINGS ==================
# Safely pulling from GitHub's secure encrypted vault
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO   = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")

ALERT_JUNK_BPS       = 50
ALERT_ARCC_YIELD     = 11.0
ALERT_ALL_IN_LOW     = 6.0
ALERT_ALL_IN_HIGH    = 10.0
# ====================================================

def send_email(subject, body):
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASS]):
        print("Skipping email: Credentials not set up in environment variables.")
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(EMAIL_FROM, EMAIL_PASS)
        s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        s.quit()
        print("Email alert successfully sent!")
    except Exception as e:
        print(f"Email failed: {e}")

def get_hy_oas():
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2"
    try:
        r = requests.get(url, timeout=10).text
        lines = [l for l in r.splitlines() if l and not l.startswith("DATE")]
        data = [l.split(',') for l in lines if len(l.split(',')) == 2 and l.split(',')[1] != '.']
        latest = float(data[-1][1])
        week = float(data[-8][1]) if len(data) >= 8 else latest
        return latest, round((latest - week) * 100, 1), data[-1][0]
    except Exception as e:
        print(f"FRED fetch failed ({e}), using default fallback parameters.")
        return 2.78, 0.0, datetime.now().strftime('%Y-%m-%d')

def get_arcc_yield():
    try:
        t = yf.Ticker("ARCC")
        price = t.history(period="5d")['Close'].iloc[-1]
        div = t.info.get('trailingAnnualDividendRate', 1.92)
        return round(div / price * 100, 2)
    except Exception as e:
        print(f"Yahoo Finance ARCC fetch failed ({e}), defaulting to standard 9.50%")
        return 9.50

def get_10y_yield():
    try:
        t = yf.Ticker("^TNX")
        yield_data = t.history(period="5d")['Close'].iloc[-1]
        return round(yield_data, 2)
    except Exception as e:
        print(f"Yahoo Finance ^TNX fetch failed ({e}), defaulting to 4.50%")
        return 4.50

# Fetch active data streams
hy_oas, hy_delta, hy_date = get_hy_oas()
arcc = get_arcc_yield()
ten_y = get_10y_yield()
all_in_hy = round(hy_oas + ten_y, 2)

# Structure the terminal log report
print("=" * 60)
print(f"JUNK & PRIVATE DEBT MONITOR — {datetime.now().strftime('%Y-%m-%d %H:%M')} EST")
print("=" * 60)
print(f"ICE BofA High Yield OAS: {hy_oas:.3f}% ({hy_date}) | 7-day Δ: {hy_delta:+.1f} bps")
print(f"10-Year Treasury Yield: {ten_y}%")
print(f"All-in High-Yield Yield (HY OAS + 10y): {all_in_hy}%")
print(f"Private Debt Proxy (ARCC yield): {arcc}%")
print("=" * 60)

alerts = []

if hy_delta >= ALERT_JUNK_BPS:
    alerts.append(f"⚠️ JUNK SPREADS WIDENED SIGNIFICANTLY: {hy_delta:+.1f} bps in 7 days!")

if arcc >= ALERT_ARCC_YIELD:
    alerts.append(
        f"🚨 PRIVATE CREDIT STRESS ACTIVE: ARCC yield reached {arcc}%\n"
        "Note: ARCC yield expansion typically signals structural friction in private direct lending pools."
    )

if all_in_hy <= ALERT_ALL_IN_LOW:
    alerts.append(f"🔍 MARKET COMPLACENCY SIGNAL: All-in HY yield is compressed to {all_in_hy}% (Below 6.00% threshold).")
elif all_in_hy >= ALERT_ALL_IN_HIGH:
    alerts.append(f"🚨 SYSTEMIC RISK ALERT: All-in corporate refinancing rates hitting {all_in_hy}%!")

if alerts:
    msg = "\n\n".join(alerts)
    print("!!! ALERT CONDITION DETECTED !!!")
    print(msg)
    
    # Broadcast report directly to your inbox
    email_body = f"{msg}\n\n=== RUN DIAGNOSTICS ===\nHigh Yield OAS: {hy_oas:.3f}% (7d Δ: {hy_delta:+.1f} bps)\n10-Year Treasury: {ten_y}%\nAll-in HY Cost: {all_in_hy}%\nARCC Proxy Yield: {arcc}%\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')} EST"
    send_email("🔴 CREDIT PLUMBING MONITOR: RISK DETECTED", email_body)
else:
    print("All quiet — credit metrics sitting completely within normal boundaries.")
print("=" * 60)
