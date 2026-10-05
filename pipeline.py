"""URB-FRAG pipeline: thesis dataset (Zenodo) + index variables -> tables, validation and figures.

    python pipeline.py                       # everything
    python pipeline.py --only tables         # tables and validation against the thesis
    python pipeline.py --only figures docs   # redraw figures and copy the README ones

Folders come from config/config.local.json (dataset_dir, sources_dir, outputs_dir).
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from urbfrag import config, data, figures, metrics, style  # noqa: E402

README_FIGURES = ["map_index", "index_profile", "map_indicators", "map_expansion", "growth_and_developments", "map_location"]


def run_tables(t, growth, d, outputs_dir):
    out = outputs_dir / "tables"
    growth.round(2).to_csv(out / "urban_growth.csv", index=False)
    metrics.developments_by_phase(d).round(3).to_csv(out / "developments_by_phase.csv", index=False)
    d.drop(columns="geometry").round(4).to_csv(out / "developments.csv", index=False)
    if t is not None:
        cols = ["tract", "neighborhood", "index", "class"] + list(data.VARIABLES) + [c for c in t.columns if c.startswith("dim_")]
        t[cols].round(2).to_csv(out / "fragmentation_index_by_tract.csv", index=False)
        metrics.index_summary(t).round(2).to_csv(out / "fragmentation_index_summary.csv", index=False)
        metrics.dimensions_by_class(t).to_csv(out / "dimensions_by_class.csv", index=False)
    val = metrics.validate(t, growth, d)
    val.to_csv(out / "validation.csv", index=False)
    for _, r in val.iterrows():
        print(f"  {'ok ' if r['ok'] else 'FAIL'} {r['check']}: published {r['published']}, computed {r['computed']}")
    return val["ok"].all()


def run_figures(t, ua, growth, d, dataset_dir, sources_dir, outputs_dir):
    style.setup()
    f = outputs_dir / "figures"
    ctx = data.context(dataset_dir)
    if t is not None:
        figures.map_index(t, ctx, d, f / "map_index.png")
        figures.index_profile(t, f / "index_profile.png")
        figures.map_indicators(t, ctx, f / "map_indicators.png")
    figures.map_expansion(ua, ctx, d, f / "map_expansion.png")
    figures.growth_and_developments(growth, metrics.cumulative_developments(d), f / "growth_and_developments.png")
    figures.map_location(data.load_state(sources_dir), ctx, ua, f / "map_location.png")
    print(f"figures written to {f}")


def run_docs(outputs_dir):
    dest = Path(__file__).parent / "docs" / "img"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in README_FIGURES:
        src = outputs_dir / "figures" / f"{name}.png"
        if src.exists():
            shutil.copy(src, dest / f"{name}.png")
            n += 1
    print(f"copied {n} figures to {dest}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="+", choices=["tables", "figures", "docs"])
    args = p.parse_args()
    steps = args.only or ["tables", "figures", "docs"]

    dataset_dir, sources_dir, outputs_dir = config.load()
    data.fetch_dataset(dataset_dir)
    t = data.load_index(sources_dir)
    t = metrics.fragmentation_index(t) if t is not None else None
    if t is None:
        print("index variables not found in sources_dir: the index figures are skipped")
    ua = data.urban_area(dataset_dir)
    growth = metrics.urban_growth(ua)
    d = data.developments(dataset_dir)
    ok = True
    if "tables" in steps:
        ok = run_tables(t, growth, d, outputs_dir)
    if "figures" in steps:
        run_figures(t, ua, growth, d, dataset_dir, sources_dir, outputs_dir)
    if "docs" in steps:
        run_docs(outputs_dir)
    if not ok:
        sys.exit("validation failed: computed values differ from the published ones (see tables/validation.csv)")


if __name__ == "__main__":
    main()
