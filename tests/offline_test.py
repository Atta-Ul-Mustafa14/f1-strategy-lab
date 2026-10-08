"""Runs the whole pipeline on synthetic API responses (no internet) in a temp folder."""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import etl, eda

rng = np.random.default_rng(0)


def fake(endpoint, **p):
    k = p.get("session_key", 0)
    if endpoint == "sessions":
        return [{"session_key": 100 + p["year"], "circuit_short_name": "X", "country_name": "Y", "date_start": "2024-03-01T12:00:00+00:00"}]
    drivers = range(1, 11)
    if endpoint == "drivers":
        return [{"driver_number": d, "team_name": f"Team {d % 5}"} for d in drivers]
    if endpoint == "laps":
        rows = [{"session_key": k, "driver_number": d, "lap_number": n, "is_pit_out_lap": n == 21,
                 "lap_duration": 90 + 0.05 * (n % 20) + rng.normal(0, .2) if n != 20 else 105.0,
                 "date_start": f"2024-03-01T12:{n:02d}:00+00:00"} for d in drivers for n in range(1, 51)]
        rows.append({"session_key": k, "driver_number": 1, "lap_number": 99, "lap_duration": 5.0})  # invalid on purpose
        return rows
    if endpoint == "stints":
        return [{"session_key": k, "driver_number": d, "stint_number": i + 1, "lap_start": a, "lap_end": b,
                 "compound": c, "tyre_age_at_start": 0} for d in drivers for i, (a, b, c) in enumerate([(1, 20, "SOFT"), (21, 50, "HARD")])]
    if endpoint == "pit":
        return [{"session_key": k, "driver_number": d, "lap_number": 20, "lane_duration": 21 + rng.normal(0, .5)} for d in drivers]
    if endpoint == "weather":
        return [{"session_key": k, "date": f"2024-03-01T12:{n:02d}:30+00:00", "air_temperature": 25, "track_temperature": 30 + n // 2,
                 "humidity": 50, "rainfall": int(k % 2 == 0 and n > 25)} for n in range(0, 55)]


os.chdir(tempfile.mkdtemp())
etl.get = fake
etl.main()
eda.main()
