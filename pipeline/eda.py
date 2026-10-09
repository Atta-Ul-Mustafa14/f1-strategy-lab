import datetime as dt, json, sqlite3
from pathlib import Path
import pandas as pd


def main():
    con = sqlite3.connect("data/f1.db")
    T = {t: pd.read_sql(f"select * from {t}", con) for t in ("sessions", "drivers", "laps", "stints", "pit", "weather", "rejected")}
    laps, stints, pit, wx = T["laps"], T["stints"], T["pit"], T["weather"]
    print("Missing values in laps:\n", laps.isna().sum(), "\n", laps.lap_duration.describe())
    # clean laps: drop out-laps, then slow laps (in-laps, safety car); add a small fuel correction (0.03 s per lap, an assumption)
    laps = laps[laps.lap_duration.notna() & (laps.is_pit_out_lap == 0)].copy()
    laps["adj"] = laps.lap_duration + 0.03 * laps.lap_number
    key = ["session_key", "driver_number"]
    laps = laps[laps.adj < laps.groupby(key).adj.transform("median") * 1.07].copy()
    laps["delta"] = laps.adj - laps.groupby(key).adj.transform("median")      # vs the driver's own race median
    laps["fdelta"] = laps.adj - laps.groupby("session_key").adj.transform("median")  # vs the whole field
    m = laps.merge(stints, on=key)
    m = m[(m.lap_number >= m.lap_start) & (m.lap_number <= m.lap_end)].copy()
    m["age"] = m.tyre_age_at_start.fillna(0) + m.lap_number - m.lap_start + 1
    deg = {}
    for c, d in m[m.age <= 35].groupby("compound"):
        t = d.groupby("age").delta.agg(["mean", "size"])
        t = t[t["size"] >= 15]
        if len(t) > 3:
            deg[c] = [[int(a), round(float(v), 3)] for a, v in t["mean"].items()]
    p = pit[pit.pit_duration < 40].merge(T["drivers"].drop_duplicates(key), on=key)
    t = p.groupby("team_name").pit_duration.agg(["median", "size"])
    t = t[t["size"] >= 5].sort_values("median")
    pits = [{"team": k, "median": round(float(r["median"]), 2), "n": int(r["size"])} for k, r in t.iterrows()]
    ns = (stints.groupby(key).size() - 1).clip(upper=3).rename("stops").reset_index()
    t = laps.groupby(key).fdelta.mean().reset_index().merge(ns).groupby("stops").fdelta.agg(["mean", "size"])
    stops = [{"stops": int(k), "pace": round(float(r["mean"]), 3), "n": int(r["size"])} for k, r in t.iterrows()]
    m["t"] = pd.to_datetime(m.date_start, utc=True, format="ISO8601").dt.as_unit("ns")
    wx["wt"] = pd.to_datetime(wx.date, utc=True, format="ISO8601").dt.as_unit("ns")
    w = pd.merge_asof(m.dropna(subset=["t"]).sort_values("t"), wx.sort_values("wt"), left_on="t", right_on="wt",
                      by="session_key", direction="nearest")
    w["band"] = (w.track_temperature // 5 * 5).astype(int)
    t = w.groupby("band").delta.agg(["mean", "size"])
    temp = [{"band": int(k), "pace": round(float(r["mean"]), 3)} for k, r in t[t["size"] >= 100].iterrows()]
    rain = {}
    for flag, name in ((0, "Dry"), (1, "Rain")):
        d = w[w.rainfall == flag]
        if len(d) >= 50:
            rain[name] = (d.compound.value_counts(normalize=True) * 100).round(1).to_dict()
    n = {k: len(T[k]) for k in ("sessions", "laps", "stints", "pit", "weather")}
    rej = len(T["rejected"])
    health = {**n, "rejected": rej, "rejection_rate": round(100 * rej / max(1, rej + sum(n.values()) - n["sessions"]), 2)}
    out = {"demo": False, "generated": dt.date.today().isoformat(), "years": sorted(map(int, T["sessions"].year.unique())),
           "health": health, "degradation": deg, "pit_by_team": pits, "pace_by_stops": stops, "pace_by_temp": temp, "compound_by_rain": rain}
    Path("public").mkdir(exist_ok=True)
    Path("public/data.json").write_text(json.dumps(out))
    print("wrote public/data.json", health)


if __name__ == "__main__":
    main()
