import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("EIA_API_KEY")

url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"

SERIES = {
    "wti": "RWTC",
    "gasoline": "EER_EPMRU_PF4_RGC_DPG",
    "diesel": "EER_EPD2DXL0_PF4_RGC_DPG",
}



def fetch_series(series_id, length=60):
    
#Pulls the most recent `length` daily records for a given EIA series ID. (similar to crude_balance.py)
#Returns a pandas DataFrame with columns: period, value

    params = [
        ("api_key", API_KEY),
        ("frequency", "daily"),
        ("data[0]", "value"),
        ("facets[series][]", series_id),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "desc"),
        ("length", length),
    ]

    response = requests.get(url, params=params)
    raw = response.json()["response"]["data"]

    df = pd.DataFrame(raw)
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = df["value"].astype(float)
    df = df[["period", "value"]].sort_values("period").reset_index(drop=True)

    return df

#  pulling all three series
prices = {}

for name, series_id in SERIES.items():
    print(f"Fetching {name} ({series_id})...")
    prices[name] = fetch_series(series_id)

# --- Merge into one table, aligned by date ---
crack = prices["wti"][["period", "value"]].rename(columns={"value": "wti"})

for name in ["gasoline", "diesel"]:
    temp = prices[name][["period", "value"]].rename(columns={"value": name})
    crack = crack.merge(temp, on="period", how="inner")

print(crack.tail(10))

# Calculate a simplified 3-2-1 crack spread
# had to convert gasoline and diesel from $/gallon to $/barrel (42 gallons per barrel)
crack["gasoline_bbl"] = crack["gasoline"] * 42
crack["diesel_bbl"] = crack["diesel"] * 42

# 3-2-1 crack spread: 2 barrels gasoline + 1 barrel diesel, minus 3 barrels WTI, divided by 3
crack["crack_321"] = (
    (2 * crack["gasoline_bbl"] + crack["diesel_bbl"]) / 3
) - crack["wti"]

###raw data print -> print(crack[["period", "wti", "gasoline_bbl", "diesel_bbl", "crack_321"]].tail(10))

# Clean summary report
latest = crack.iloc[-1]
avg_30day = crack["crack_321"].tail(30).mean()
min_30day = crack["crack_321"].tail(30).min()
max_30day = crack["crack_321"].tail(30).max()

print("\n" + "=" * 60)
print("  3-2-1 CRACK SPREAD — REFINING MARGIN PROXY")
print("=" * 60)
print(f"Date: {latest['period'].strftime('%Y-%m-%d')}")
print(f"  WTI crude:        ${latest['wti']:>7,.2f} /bbl")
print(f"  Gasoline:         ${latest['gasoline_bbl']:>7,.2f} /bbl equiv")
print(f"  Diesel:           ${latest['diesel_bbl']:>7,.2f} /bbl equiv")
print("-" * 60)
print(f"  3-2-1 crack spread: ${latest['crack_321']:>7,.2f} /bbl")
print(f"  30-day average:     ${avg_30day:>7,.2f} /bbl")
print(f"  30-day range:       ${min_30day:.2f} to ${max_30day:.2f}")
print("=" * 60)

if latest["crack_321"] > 40:
    signal = "ACUTE STRESS — well above historical norm ($10-25)"
elif latest["crack_321"] > 30:
    signal = "ELEVATED — above the $30 stress threshold"
elif latest["crack_321"] < 10:
    signal = "COMPRESSED — thin refining margins"
else:
    signal = "NORMAL — within healthy historical range"

print(f"\nSignal: {signal}")
print("=" * 60)
