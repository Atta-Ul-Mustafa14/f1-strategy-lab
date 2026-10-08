"""Writes SAMPLE (synthetic) data so the dashboard can be previewed. Real data comes from etl.py + eda.py."""
import json
import numpy as np
r = np.random.default_rng(1)
slope = {"SOFT": 0.09, "MEDIUM": 0.05, "HARD": 0.03}
deg = {c: [[a, round(float(s * a + r.normal(0, .04)), 3)] for a in range(1, 31 if c != "SOFT" else 21)] for c, s in slope.items()}
teams = [f"Team {x}" for x in "ABCDEFGH"]
pits = [{"team": t, "median": round(21 + .35 * i + float(r.normal(0, .1)), 2), "n": 60 + i} for i, t in enumerate(teams)]
d = {"demo": True, "generated": "sample", "years": [2023, 2024, 2025],
     "health": {"sessions": 72, "laps": 78000, "stints": 4100, "pit": 3300, "weather": 9800, "rejected": 412, "rejection_rate": 0.43},
     "degradation": deg, "pit_by_team": pits,
     "pace_by_stops": [{"stops": 0, "pace": .9, "n": 90}, {"stops": 1, "pace": .15, "n": 900}, {"stops": 2, "pace": -.05, "n": 700}, {"stops": 3, "pace": .2, "n": 80}],
     "pace_by_temp": [{"band": b, "pace": round(float(.02 * (b - 35) + r.normal(0, .03)), 3)} for b in range(20, 55, 5)],
     "compound_by_rain": {"Dry": {"SOFT": 28, "MEDIUM": 41, "HARD": 31}, "Rain": {"INTERMEDIATE": 62, "WET": 18, "MEDIUM": 12, "HARD": 8}}}
json.dump(d, open("public/data.json", "w"))
