import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("EIA_API_KEY")

url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"

SERIES = {
    "production": "WCRFPUS2",
    "imports": "WCRIMUS2",
    "exports": "WCREXUS2",
    "refinery_inputs": "WCRRIUS2",
    "ending_stocks": "WCRSTUS1",
}

# pulls most recent 'length' of weekly records for each EIA series ID.
# Then returns a pandas DataFrame with columns: period and value. -V
def fetch_series(series_id, length=12):
    params = [
        ("api_key", API_KEY),
        ("frequency", "weekly"),
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

# used float instead of int to avoid rounding errors dealing in 000s.

# pulling all 5 series
balance_data = {}
for name, series_id in SERIES.items():
    print(f"Fetching {name} ({series_id})...")
    balance_data[name] = fetch_series(series_id)

print("\nALL series fetched:")
for name, df in balance_data.items():
    print(f"{name}: {len(df)} rows")

# merge all five series into one table, aligned by date
balance = balance_data["production"][["period", "value"]].rename(columns={"value": "production"})

for name in ["imports", "exports", "refinery_inputs", "ending_stocks"]:
    temp = balance_data[name][["period", "value"]].rename(columns={"value": name})
    balance = balance.merge(temp, on="period", how="inner")

# calculate the implied balance ---
# all flow series are in thousand barrels PER DAY — multiply by 7 to get weekly volume
balance["production_weekly"] = balance["production"] * 7
balance["imports_weekly"] = balance["imports"] * 7
balance["exports_weekly"] = balance["exports"] * 7
balance["refinery_inputs_weekly"] = balance["refinery_inputs"] * 7

# implied weekly stock change = supply in - demand out
balance["implied_change"] = (
    balance["production_weekly"]
    + balance["imports_weekly"]
    - balance["exports_weekly"]
    - balance["refinery_inputs_weekly"]
)

# actual reported stock change, week over week
balance["actual_change"] = balance["ending_stocks"].diff()

# The gap between what the balance says should have happened,
# and what actually got reported — this is the "adjustment factor"
balance["adjustment"] = balance["actual_change"] - balance["implied_change"]

# Clean summary report
latest = balance.iloc[-1]
avg_adjustment = balance["adjustment"].mean()
total_draw_12wk = balance["actual_change"].sum()

print("\n" + "=" * 60)
print("  US CRUDE OIL SUPPLY & DEMAND BALANCE")
print("=" * 60)
print(f"Week of {latest['period'].strftime('%Y-%m-%d')}")
print(f"  Production:        {latest['production']:>9,.0f} kbd")
print(f"  Imports:           {latest['imports']:>9,.0f} kbd")
print(f"  Exports:           {latest['exports']:>9,.0f} kbd")
print(f"  Refinery inputs:   {latest['refinery_inputs']:>9,.0f} kbd")
print(f"  Ending stocks:     {latest['ending_stocks']:>9,.0f} kbbl")
print("-" * 60)
print(f"  This week's draw:  {latest['actual_change']:>+9,.0f} kbbl")
print(f"  12-week total:     {total_draw_12wk:>+9,.0f} kbbl")
print(f"  Avg adjustment:    {avg_adjustment:>+9,.0f} kbbl/week")
print("=" * 60)

if latest["actual_change"] < 0:
    signal = "BULLISH — stocks drawing"
else:
    signal = "BEARISH — stocks building"

print(f"\nSignal: {signal}")
print(f"Context: {'demand outpacing supply' if latest['actual_change'] < 0 else 'supply outpacing demand'} this week")
print("=" * 60)
