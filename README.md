# crude-oil-analysis

Python tools for crude oil market analysis. Built to develop 
quantitative skills in the energy field.


## Projects

### Crude Oil Supply & Demand Balance
`crude_balance.py` — Pulls five weekly EIA series (production, imports, 
exports, refinery inputs, ending stocks), merges them into one balance 
sheet, and calculates the implied vs actual weekly stock change.

**What it shows:** Whether the US crude market is drawing or building, 
plus the "adjustment factor" — the gap between what the balance equation 
implies and what EIA actually reports. This is the same unaccounted-for 
crude metric EIA itself tracks internally.

**Concepts covered:** multi-series API pulls, DataFrame merges, unit 
conversion (rate vs level), custom functions, dictionaries, string 
formatting


### 2. 3-2-1 Crack Spread
`crack_spread.py` — Pulls WTI, Gulf Coast gasoline, and Gulf Coast diesel 
spot prices from EIA, converts products to $/barrel, and calculates the 
3-2-1 crack spread as a proxy for refinery margins.

**What it shows:** Whether refining margins are running normal, elevated, 
or under acute stress relative to the standard $10-25/bbl healthy range. 
As of late June 2026, the spread is running $40-60/bbl — well into acute 
stress territory, driven by the lagged recovery of refined product prices 
following the Hormuz-related crude spike earlier in the year.

**Concepts covered:** multi-series price pulls, unit conversion ($/gallon 
to $/barrel), threshold-based signal logic, rolling averages
