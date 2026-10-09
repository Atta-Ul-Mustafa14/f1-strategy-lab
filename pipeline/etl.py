import hashlib, json, sqlite3, time
from pathlib import Path
import pandas as pd
import requests
from pydantic import ValidationError
import models

BASE, CACHE, YEARS = "https://api.openf1.org/v1", Path("cache"), [2023, 2024, 2025]
_last = 0.0


def get(endpoint, **params):
    """Extract: one throttled, cached API call (raw JSON is saved so re-runs cost no requests)."""
    global _last
    f = CACHE / f"{endpoint}_{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:10]}.json"
    if f.exists():
        return json.loads(f.read_text())
    for attempt in range(6):
        time.sleep(max(0, 2.2 - (time.time() - _last)))  # about 27 requests/minute
        _last = time.time()
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        data = [] if r.status_code == 404 else r.json()  # 404 = "no results"
        if r.status_code not in (200, 404):
            r.raise_for_status()
        f.write_text(json.dumps(data))
        return data
    raise RuntimeError(f"rate limited too often on {endpoint}")


def validate(model, rows, name, bad):
    """Transform: keep valid rows, send the rest to the rejected table with the reason."""
    ok = []
    for r in rows:
        try:
            ok.append(model.model_validate(r).model_dump())
        except ValidationError as e:
            bad.append({"table": name, "error": e.errors()[0]["msg"], "raw": json.dumps(r)[:300]})
    return ok


def main():
    CACHE.mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    bad, T = [], {k: [] for k in ("sessions", "drivers", "laps", "stints", "pit", "weather")}
    for y in YEARS:
        for s in get("sessions", year=y, session_name="Race"):
            k = s["session_key"]
            T["sessions"].append({"session_key": k, "year": y, "circuit": s.get("circuit_short_name"),
                                  "country": s.get("country_name"), "date_start": s.get("date_start")})
            T["drivers"] += [{"session_key": k, "driver_number": d["driver_number"], "team_name": d.get("team_name")}
                             for d in get("drivers", session_key=k)]
            T["laps"] += validate(models.Lap, get("laps", session_key=k), "laps", bad)
            T["stints"] += validate(models.Stint, get("stints", session_key=k), "stints", bad)
            pits = [{**p, "pit_duration": p.get("lane_duration") or p.get("pit_duration")} for p in get("pit", session_key=k)]
            T["pit"] += validate(models.Pit, pits, "pit", bad)
            T["weather"] += validate(models.Weather, get("weather", session_key=k), "weather", bad)
            print(f"loaded session {k} ({y})")
    with sqlite3.connect("data/f1.db") as con:  # Load: replace tables, so re-runs never duplicate rows
        for name, rows in T.items():
            pd.DataFrame(rows).drop_duplicates().to_sql(name, con, if_exists="replace", index=False)
        pd.DataFrame(bad, columns=["table", "error", "raw"]).to_sql("rejected", con, if_exists="replace", index=False)
    print({k: len(v) for k, v in T.items()}, "rejected:", len(bad))


if __name__ == "__main__":
    main()
