"""Pure-Python logic for the energy demand forecast job. No Hera, no cluster.

It generates synthetic half-hourly demand readings (MW) for a few regions, rolls them
up to daily energy totals (MWh), and fits a simple linear trend to forecast the next
day's demand per region.

These functions are the tested source of truth (see ``test_demand_forecast.py``); they
run in milliseconds with the standard library alone. ``forecast_step.py`` mirrors this
computation with pandas and numpy to run on the cluster.
"""

import math
import random

REGIONS = ["North", "Midlands", "South"]
DAYS = 28
PERIODS_PER_DAY = 48  # half-hourly settlement periods
_BASE_MW = {"North": 1800.0, "Midlands": 2400.0, "South": 3200.0}
_DAILY_TREND_MW = {"North": 6.0, "Midlands": 9.0, "South": 4.0}


def make_readings(days=DAYS, periods_per_day=PERIODS_PER_DAY, seed=42):
    """Return synthetic half-hourly demand readings as a list of dicts. Deterministic.

    Each reading is {"region", "day", "period", "mw"}. Demand follows a regional base
    load, a slow upward daily trend, an intraday peak around the evening, and noise.
    """
    rng = random.Random(seed)
    readings = []
    for region in REGIONS:
        for day in range(days):
            for period in range(periods_per_day):
                hour = period / 2.0
                intraday = 350.0 * math.sin((hour - 6.0) / 24.0 * 2.0 * math.pi)
                mw = (
                    _BASE_MW[region]
                    + _DAILY_TREND_MW[region] * day
                    + intraday
                    + rng.uniform(-60.0, 60.0)
                )
                readings.append(
                    {"region": region, "day": day, "period": period, "mw": mw}
                )
    return readings


def daily_totals(readings):
    """Aggregate half-hourly MW readings into daily energy totals (MWh) per region.

    Each reading covers a half-hour, so its energy is mw * 0.5. Returns a list of
    {"region", "day", "mwh"} sorted by region then day.
    """
    totals = {}
    for r in readings:
        key = (r["region"], r["day"])
        totals[key] = totals.get(key, 0.0) + r["mw"] * 0.5
    rows = [
        {"region": region, "day": day, "mwh": round(mwh, 1)}
        for (region, day), mwh in totals.items()
    ]
    return sorted(rows, key=lambda row: (row["region"], row["day"]))


def forecast_next_day(daily, region):
    """Forecast the next day's MWh for a region from a linear least-squares trend."""
    series = sorted(
        (row for row in daily if row["region"] == region), key=lambda row: row["day"]
    )
    if not series:
        raise ValueError(f"no daily data for region {region}")
    xs = [row["day"] for row in series]
    ys = [row["mwh"] for row in series]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    variance = sum((x - mean_x) ** 2 for x in xs)
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = covariance / variance if variance else 0.0
    intercept = mean_y - slope * mean_x
    next_day = xs[-1] + 1
    return round(slope * next_day + intercept, 1)
