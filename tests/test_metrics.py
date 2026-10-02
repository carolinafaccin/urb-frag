"""Unit tests on synthetic data."""
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from urbfrag import data, metrics


def _tracts():
    rows = []
    for i, score in enumerate([20, 60, 100]):
        rows.append({k: score for k in data.VARIABLES} | {"geometry": box(i, 0, i + 1, 1)})
    return gpd.GeoDataFrame(rows, crs=31982)


def test_index_is_simple_mean_and_classes():
    t = metrics.fragmentation_index(_tracts())
    assert list(t["index"]) == [20, 60, 100]
    assert list(t["class"].astype(str)) == ["Low", "High", "High"]


def test_class_thresholds():
    t = _tracts().iloc[[0]].copy()
    for k in data.VARIABLES:
        t[k] = 50.0
    assert str(metrics.fragmentation_index(t)["class"].iloc[0]) == "Low"   # 50 is still low
    for k in data.VARIABLES:
        t[k] = 55.0
    assert str(metrics.fragmentation_index(t)["class"].iloc[0]) == "Medium"


def test_cumulative_developments():
    d = pd.DataFrame({"kind": ["A", "A", "B"], "year": [2000, 2002, 2001], "area_km2": [1.0, 2.0, 0.5], "nome": list("xyz")})
    c = metrics.cumulative_developments(d).set_index(["kind", "year"])
    assert c.loc[("A", 2001), "area_km2"] == 1.0 and c.loc[("A", 2022), "n"] == 2
