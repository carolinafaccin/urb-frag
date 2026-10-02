"""Fragmentation index, urban growth, housing developments and the check against the thesis."""
import pandas as pd

from .data import VARIABLES

CLASSES = {"Low": (0, 50), "Medium": (50, 55), "High": (55, 100)}   # thesis thresholds (index 0-100)

# Values published in Faccin (2025), thesis, PROPUR/UFRGS
PUBLISHED = {
    "index_min": 41.7,
    "urban_km2_1993": 17.74, "urban_km2_2013": 31.78, "urban_km2_2022": 35.00,
    "gated_communities": 22,
    "gated_share_1970_1993_pct": 4.55, "gated_share_2013_2022_pct": 13.64,
    "gated_km2_2007": 0.90, "gated_km2_2013": 2.70,
}


def fragmentation_index(t):
    """Simple mean of the 23 scored variables, then three classes (thesis, section 4.1.2)."""
    t = t.copy()
    t["index"] = t[list(VARIABLES)].mean(axis=1)
    t["class"] = pd.cut(t["index"], [0, 50, 55, 100], labels=list(CLASSES), right=True)
    for dim in ("Environmental", "Social", "Housing", "Infrastructure"):
        t[f"dim_{dim.lower()}"] = t[[k for k, v in VARIABLES.items() if v[1] == dim]].mean(axis=1)
    return t


def index_summary(t):
    s = t.groupby("class", observed=False).agg(tracts=("index", "size"), area_km2=("geometry", lambda g: g.area.sum() / 1e6))
    s["tracts_pct"] = 100 * s["tracts"] / s["tracts"].sum()
    return s.reset_index()


def dimensions_by_class(t):
    cols = [c for c in t.columns if c.startswith("dim_")]
    return t.groupby("class", observed=False)[cols].mean().round(1).reset_index()


def urban_growth(ua):
    g = pd.DataFrame({"year": ua["year"], "km2": ua.area / 1e6})
    g["growth_pct"] = g["km2"].pct_change() * 100
    years = g["year"].diff()
    g["annual_pct"] = ((g["km2"] / g["km2"].shift()) ** (1 / years) - 1) * 100
    return g


def developments_by_phase(d):
    t = d.groupby(["kind", "phase"], observed=False).agg(n=("nome", "size"), area_km2=("area_km2", "sum")).reset_index()
    t["share_pct"] = 100 * t["n"] / t.groupby("kind")["n"].transform("sum")
    return t


def cumulative_developments(d):
    """Number and cumulative area of developments by year of approval."""
    years = range(int(d["year"].min()), 2023)
    rows = []
    for kind, g in d.groupby("kind"):
        for y in years:
            s = g[g["year"] <= y]
            rows.append({"kind": kind, "year": y, "n": len(s), "area_km2": s["area_km2"].sum()})
    return pd.DataFrame(rows)


def validate(t, growth, d):
    gated = d[d["kind"] == "Gated community"]
    ph = gated["phase"].value_counts(normalize=True) * 100
    g = growth.set_index("year")["km2"]
    computed = {
        "index_min": t["index"].min() if t is not None else float("nan"),
        "urban_km2_1993": g[1993], "urban_km2_2013": g[2013], "urban_km2_2022": g[2022],
        "gated_communities": len(gated),
        "gated_share_1970_1993_pct": ph.get("1970–1993", 0), "gated_share_2013_2022_pct": ph.get("2013–2022", 0),
        "gated_km2_2007": gated.loc[gated["year"] <= 2007, "area_km2"].sum(),
        "gated_km2_2013": gated.loc[gated["year"] <= 2013, "area_km2"].sum(),
    }
    rows = []
    for k, v in PUBLISHED.items():
        c = round(float(computed[k]), 2)
        tol = 0 if k == "gated_communities" else max(0.05, 0.02 * abs(v))
        rows.append({"check": k, "published": v, "computed": c, "tolerance": tol, "ok": abs(c - v) <= tol})
    return pd.DataFrame(rows)

