"""Local tests for the demand forecast logic. Standard library only, no cluster.

Run with ``pytest``, or directly with ``python test_demand_forecast.py``.
"""

from demand_forecast import (
    DAYS,
    PERIODS_PER_DAY,
    REGIONS,
    daily_totals,
    forecast_next_day,
    make_readings,
)


def test_daily_totals_small_case():
    readings = [
        {"region": "North", "day": 0, "period": 0, "mw": 100.0},
        {"region": "North", "day": 0, "period": 1, "mw": 200.0},
        {"region": "North", "day": 1, "period": 0, "mw": 50.0},
        {"region": "South", "day": 0, "period": 0, "mw": 80.0},
    ]
    assert daily_totals(readings) == [
        {"region": "North", "day": 0, "mwh": 150.0},
        {"region": "North", "day": 1, "mwh": 25.0},
        {"region": "South", "day": 0, "mwh": 40.0},
    ]


def test_forecast_extends_a_linear_trend():
    daily = [{"region": "X", "day": day, "mwh": 10.0 * day + 5.0} for day in range(5)]
    assert forecast_next_day(daily, "X") == 55.0


def test_make_readings_is_deterministic():
    assert make_readings(days=3, seed=7) == make_readings(days=3, seed=7)


def test_readings_cover_every_region_day_period():
    readings = make_readings()
    assert len(readings) == len(REGIONS) * DAYS * PERIODS_PER_DAY
    assert len(daily_totals(readings)) == len(REGIONS) * DAYS


def test_forecast_follows_the_upward_trend():
    daily = daily_totals(make_readings())
    for region in REGIONS:
        series = [row["mwh"] for row in daily if row["region"] == region]
        assert forecast_next_day(daily, region) > series[0]


def test_forecast_raises_on_unknown_region():
    daily = daily_totals(make_readings(days=3))
    try:
        forecast_next_day(daily, "Atlantis")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for an unknown region")


if __name__ == "__main__":
    test_daily_totals_small_case()
    test_forecast_extends_a_linear_trend()
    test_make_readings_is_deterministic()
    test_readings_cover_every_region_day_period()
    test_forecast_follows_the_upward_trend()
    test_forecast_raises_on_unknown_region()
    print("all tests passed")
