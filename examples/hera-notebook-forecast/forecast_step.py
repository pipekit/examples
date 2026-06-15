"""The cluster step an analyst submits: a single Hera @script function.

It imports the platform's image and resource defaults from ``dataplatform`` and uses
Hera's ``@script`` decorator directly, so the analyst writes only their job. The body
is self-contained (Hera ships it to the cluster) and mirrors the pure logic in
``demand_forecast.py``, computed with pandas and numpy on the data image.
"""

from hera.workflows import script

from dataplatform import DATA_IMAGE, DATA_RESOURCES


@script(
    image=DATA_IMAGE,
    resources=DATA_RESOURCES,
    command=["python"],
    add_cwd_to_sys_path=False,
)
def forecast_demand():
    import math
    import random

    import numpy as np
    import pandas as pd

    regions = ["North", "Midlands", "South"]
    days, periods_per_day = 28, 48
    base_mw = {"North": 1800.0, "Midlands": 2400.0, "South": 3200.0}
    daily_trend_mw = {"North": 6.0, "Midlands": 9.0, "South": 4.0}

    rng = random.Random(42)
    rows = []
    for region in regions:
        for day in range(days):
            for period in range(periods_per_day):
                hour = period / 2.0
                intraday = 350.0 * math.sin((hour - 6.0) / 24.0 * 2.0 * math.pi)
                mw = (
                    base_mw[region]
                    + daily_trend_mw[region] * day
                    + intraday
                    + rng.uniform(-60.0, 60.0)
                )
                rows.append({"region": region, "day": day, "mw": mw})

    df = pd.DataFrame(rows)
    # Half-hourly MW to daily energy: each reading covers 0.5h.
    df["mwh"] = df["mw"] * 0.5
    daily = df.groupby(["region", "day"], as_index=False)["mwh"].sum().round(1)

    print("=== Daily demand (MWh) by region, last 5 days ===")
    recent = daily[daily["day"] >= days - 5]
    print(recent.pivot(index="day", columns="region", values="mwh").to_string())

    forecasts = {}
    for region in regions:
        series = daily[daily["region"] == region].sort_values("day")
        slope, intercept = np.polyfit(series["day"], series["mwh"], 1)
        forecasts[region] = round(float(slope * days + intercept), 1)

    print("=== Next-day demand forecast (MWh) by region ===")
    forecast_df = pd.DataFrame(
        {"region": list(forecasts), "forecast_mwh": list(forecasts.values())}
    )
    print(forecast_df.to_string(index=False))
