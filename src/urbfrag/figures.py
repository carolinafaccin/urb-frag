"""Figures in the project's visual identity (brand palette, Source Code Pro)."""
import numpy as np
from geopandas import GeoSeries
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import style
from .data import VARIABLES

HEAD, FOOT = 1.5, 0.6
CLASS_COLORS = {"Low": "#F6D5C3", "Medium": style.SEQ[1], "High": style.SEQ[3]}
GATED, SOCIAL = style.CAT[1], style.CAT[0]   # rust, green (validated adjacent pair)
DIMENSIONS = ["Environmental", "Social", "Housing", "Infrastructure"]


def _legend(fig, handles, x, y, title=None, **kw):
    opts = dict(loc="upper left", bbox_to_anchor=(x, y), fontsize=8.5, title_fontsize=9, handlelength=1.4,
                alignment="left", labelspacing=0.8)
    opts.update(kw)
    leg = fig.legend(handles=handles, title=title, **opts)
    leg.get_title().set_fontweight("semibold")
    return leg


def _map_fig(width=10, height=11.5, legend=0.32):
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0.01, FOOT / height, 1 - legend - 0.01, 1 - (HEAD + FOOT) / height])
    return fig, ax, 1 - legend + 0.01, 1 - HEAD / height


def _frame(ax, bounds, pad=300):
    style.map_axes(ax, bounds, pad=pad)


def _overlays(ax, ctx, d, area):
    """Highways, industrial zone, green belt, gated communities and social housing, inside `area`."""
    ctx["industrial"].clip(area).plot(ax=ax, facecolor="none", edgecolor=style.INK, hatch="////", linewidth=0, alpha=0.55, zorder=3)
    ctx["green_belt"].clip(area).plot(ax=ax, facecolor="none", edgecolor=style.SAGE_D, hatch="....", linewidth=0, alpha=0.7, zorder=3)
    hw = ctx["highways"].clip(area.buffer(400))
    hw.plot(ax=ax, color=style.INK, linewidth=3.2, zorder=4)
    hw.plot(ax=ax, color="white", linewidth=1.8, zorder=4.1)
    g = d[d["kind"] == "Gated community"]
    s = d[d["kind"] == "Social housing"]
    gp, sp = g.geometry.representative_point(), s.geometry.representative_point()
    ax.scatter(gp.x, gp.y, s=60, facecolor="white", edgecolor=style.INK, linewidth=1.4, zorder=6)
    ax.scatter(sp.x, sp.y, s=55, marker="^", color=style.INK, edgecolor="white", linewidth=0.6, zorder=6)
    return [Line2D([], [], marker="o", ls="", mfc="white", mec=style.INK, mew=1.4, markersize=8,
                   label=f"Gated communities ({len(g)})"),
            Line2D([], [], marker="^", ls="", color=style.INK, mec="white", markersize=8,
                   label=f"Social housing subdivisions ({len(s)})"),
            Line2D([], [], color=style.INK, lw=3.2, label="Highways"),
            Patch(facecolor="white", edgecolor=style.INK, hatch="////", label="Industrial zone"),
            Patch(facecolor="white", edgecolor=style.SAGE_D, hatch="....", label="Green belt (protected)")]


def map_index(t, ctx, d, out):
    """The sociospatial fragmentation index by census tract, with developments and barriers."""
    fig, ax, lx, ly = _map_fig()
    bounds = t.total_bounds
    for cls, color in CLASS_COLORS.items():
        sub = t[t["class"] == cls]
        sub.plot(ax=ax, color=color, linewidth=0, zorder=1)
    ctx["streets"].clip(t.union_all().buffer(50)).plot(ax=ax, color="white", linewidth=0.35, alpha=0.8, zorder=2)
    t.boundary.plot(ax=ax, color="white", linewidth=0.6, zorder=2.5)
    handles = _overlays(ax, ctx, d, t.union_all())
    _frame(ax, bounds)
    style.scalebar(ax, km=1, loc=(0.04, 0.03))
    counts = t["class"].value_counts()
    _legend(fig, [Patch(facecolor=c, label=f"{k}: {counts.get(k, 0)} tracts") for k, c in CLASS_COLORS.items()],
            lx, ly, "Fragmentation index")
    _legend(fig, handles, lx, ly - 0.17)
    style.header(fig, "Sociospatial fragmentation in Santa Cruz do Sul",
                 "Index of 23 environmental, social, housing and infrastructure variables by census tract.\n"
                 "Gated communities cluster in the north, social housing in the south; the center is the least fragmented.")
    style.footer(fig)
    style.save(fig, out)


def index_profile(t, out):
    """Distribution of the index and the four dimensions by class."""
    W, H = 12, 6.4
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, H), gridspec_kw={"width_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.07, right=0.98, top=1 - (HEAD + 0.45) / H, bottom=(FOOT + 0.75) / H, wspace=0.22)
    bins = np.arange(41, 61.5, 1)
    for cls, (lo, hi) in {"Low": (0, 50), "Medium": (50, 55), "High": (55, 100)}.items():
        v = t.loc[t["class"] == cls, "index"]
        a1.hist(v, bins=bins, color=CLASS_COLORS[cls], edgecolor="white", linewidth=1.2, label=cls)
    for x in (50, 55):
        a1.axvline(x, color=style.INK, lw=0.9, ls=(0, (3, 2)))
        a1.text(x, a1.get_ylim()[1] * 0.98, f" {x}", va="top", fontsize=8, color=style.INK)
    a1.set_xlabel("Fragmentation index (simple mean of the 23 scores, 20–100)")
    a1.set_ylabel("Census tracts")
    a1.grid(axis="x", visible=False)
    a1.set_title("Distribution across the 144 urban tracts", loc="left", fontsize=10.5, fontweight="semibold", color=style.INK)
    a1.legend(loc="upper left", fontsize=8.5, handlelength=1.1)
    means = t.groupby("class", observed=False)[[f"dim_{d.lower()}" for d in DIMENSIONS]].mean()
    x = np.arange(len(DIMENSIONS))
    w = 0.26
    for i, cls in enumerate(CLASS_COLORS):
        a2.bar(x + (i - 1) * w, means.loc[cls].values, width=w - 0.03, color=CLASS_COLORS[cls], label=cls)
    a2.set_xticks(x)
    a2.set_xticklabels(DIMENSIONS, fontsize=8.5)
    a2.set_ylim(0, 100)
    a2.set_ylabel("Mean score (20–100)")
    a2.grid(axis="x", visible=False)
    a2.set_title("Mean score by dimension and class", loc="left", fontsize=10.5, fontweight="semibold", color=style.INK)
    a2.legend(loc="upper right", fontsize=8.5, handlelength=1.1, ncol=3)
    style.header(fig, "How the index is built",
                 "Each variable is scored 20–100 by natural breaks (higher = more fragmentation); the index is their simple\n"
                 "mean, split at 50 and 55. Environmental and social variables separate the classes most.")
    style.footer(fig)
    style.save(fig, out)


def map_indicators(t, ctx, out):
    """Six of the index variables, mapped as their natural-break classes."""
    keys = ["v07", "v08", "v12", "v22", "v21", "v14"]
    W, H = 12, 12.5
    fig, axes = plt.subplots(2, 3, figsize=(W, H))
    fig.subplots_adjust(left=0.01, right=0.99, top=1 - (HEAD + 0.75) / H, bottom=(FOOT + 0.2) / H, wspace=0.03, hspace=0.14)
    ramp = dict(zip([20, 40, 60, 80, 100], style.SEQ))
    for ax, k in zip(axes.flat, keys):
        for score, color in ramp.items():
            sub = t[t[k] == score]
            if len(sub):
                sub.plot(ax=ax, color=color, linewidth=0)
        t.boundary.plot(ax=ax, color="white", linewidth=0.4)
        hw = ctx["highways"].clip(t.union_all().buffer(800))
        hw.plot(ax=ax, color=style.INK, linewidth=1.1)
        _frame(ax, t.total_bounds, pad=200)
        ax.set_title(VARIABLES[k][0].replace(" (%)", ""), loc="left",
                     fontsize=9, fontweight="semibold", color=style.INK, wrap=True)
    _legend(fig, [Patch(facecolor=c, label=lab) for c, lab in zip(style.SEQ, ["Very low", "Low", "Medium", "High", "Very high"])],
            0.035, 1 - (HEAD - 0.05) / H, ncol=5, columnspacing=1.4)
    style.header(fig, "A divided city: income, housing and risk",
                 "Six of the 23 variables of the index by census tract (2010), in five natural-break classes. High-income households\n"
                 "and gated communities sit in the north; low income, special social-interest zones and social housing in the south.")
    style.footer(fig)
    style.save(fig, out)


def map_expansion(ua, ctx, d, out):
    """Urbanized area of the municipal seat by period (MapBiomas)."""
    fig, ax, lx, ly = _map_fig()
    geoms = ua.set_index("year").geometry
    periods = [(2022, "2013–2022", style.SEQ[0]), (2013, "1993–2013", style.SEQ[1]),
               (1993, "1985–1993", style.SEQ[3]), (1985, "Urbanized by 1985", style.SEQ[4])]
    bounds = geoms[2022].bounds
    ctx["urban_2016"].plot(ax=ax, color=style.LAND, linewidth=0, zorder=0)
    for y, _, color in periods:   # newest (largest) first, older areas drawn on top
        GeoSeries([geoms[y]], crs=ua.crs).plot(ax=ax, color=color, linewidth=0, zorder=1)
    ctx["urban_2016"].boundary.plot(ax=ax, color=style.MUTED, linewidth=0.7, linestyle=(0, (4, 3)), zorder=2)
    hw = ctx["highways"].cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
    hw.plot(ax=ax, color=style.INK, linewidth=1.1, zorder=3)
    _frame(ax, bounds, pad=600)
    style.scalebar(ax, km=2, loc=(0.04, 0.03))
    km2 = {y: geoms[y].area / 1e6 for y in geoms.index}
    labels = {1985: f"Urbanized by 1985: {km2[1985]:.1f} km²", 1993: f"1985–1993: +{km2[1993] - km2[1985]:.1f} km²",
              2013: f"1993–2013: +{km2[2013] - km2[1993]:.1f} km²", 2022: f"2013–2022: +{km2[2022] - km2[2013]:.1f} km²"}
    _legend(fig, [Patch(facecolor=c, label=labels[y]) for y, _, c in reversed(periods)], lx, ly, "Urbanized area (MapBiomas)")
    _legend(fig, [Line2D([], [], color=style.INK, lw=1.2, label="Highways"),
                  Line2D([], [], color=style.MUTED, lw=0.9, ls=(0, (4, 3)), label="Urban perimeter (2016)")], lx, ly - 0.17)
    style.header(fig, "Four decades of extensive urbanization",
                 f"The urbanized area of the city grew from {km2[1985]:.1f} km² in 1985 to {km2[2022]:.1f} km² in 2022, "
                 "much faster than its population.\nThe thesis reads this growth in three phases: 1970–1993, 1993–2013 and 2013–2022.")
    style.footer(fig)
    style.save(fig, out)


def growth_and_developments(growth, cum, out):
    """Urbanized area by year, and gated communities vs social housing over time (two charts, one axis each)."""
    W, H = 12, 6.2
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, H), gridspec_kw={"width_ratios": [0.8, 1.2]})
    fig.subplots_adjust(left=0.07, right=0.9, top=1 - (HEAD + 0.45) / H, bottom=(FOOT + 0.5) / H, wspace=0.25)
    x = np.arange(len(growth))
    a1.bar(x, growth["km2"], width=0.55, color=style.ORANGE)
    for i, r in growth.reset_index(drop=True).iterrows():
        a1.text(i, r["km2"] + 0.7, f"{r['km2']:.1f}", ha="center", fontsize=8.5, color=style.INK)
    a1.set_xticks(x)
    a1.set_xticklabels(growth["year"].astype(str), fontsize=8.5)
    a1.set_ylabel("km²")
    a1.grid(axis="x", visible=False)
    a1.set_title("Urbanized area (MapBiomas)", loc="left", fontsize=10.5, fontweight="semibold", color=style.INK)
    for kind, color in [("Gated community", GATED), ("Social housing", SOCIAL)]:
        s = cum[cum["kind"] == kind]
        a2.step(s["year"], s["area_km2"], where="post", color=color, lw=2)
        last = s.iloc[-1]
        a2.annotate(f"{kind}\n{int(last['n'])} · {last['area_km2']:.1f} km²", (last["year"], last["area_km2"]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5, color=style.INK,
                    annotation_clip=False)
        a2.plot(last["year"], last["area_km2"], "o", color=color, ms=6, mec="white", mew=1.5)
    for x0, x1 in [(1993, 2013)]:
        a2.axvspan(x0, x1, color=style.GRID, alpha=0.5, lw=0, zorder=0)
    a2.text(2003, a2.get_ylim()[1] * 0.97, "1993–2013", ha="center", va="top", fontsize=8, color=style.MUTED)
    a2.set_xlim(1980, 2022)
    a2.set_ylabel("Cumulative area (km²)")
    a2.grid(axis="x", visible=False)
    a2.set_title("Developments approved by the City", loc="left", fontsize=10.5, fontweight="semibold", color=style.INK)
    style.header(fig, "Growth driven by two housing products",
                 "Gated communities for high-income households and social housing subdivisions spread mostly between 1993 and\n"
                 "2013; gated communities take more land per development.")
    style.footer(fig)
    style.save(fig, out)


def map_location(state, ctx, ua, out):
    """Location: the municipality in Rio Grande do Sul, and the city in the municipality."""
    W, H = 12, 7.6
    fig = plt.figure(figsize=(W, H))
    a1 = fig.add_axes([0.01, FOOT / H, 0.5, 1 - (HEAD + 0.4 + FOOT) / H])
    a2 = fig.add_axes([0.53, FOOT / H, 0.46, 1 - (HEAD + 0.4 + FOOT) / H])
    if state is not None:
        state.plot(ax=a1, color=style.LAND, edgecolor="white", linewidth=0.3)
        state[state["is_scs"]].plot(ax=a1, color=style.ORANGE, linewidth=0)
        style.map_axes(a1, state.total_bounds, pad=5000)
        style.scalebar(a1, km=100, loc=(0.06, 0.05))
    mun = ctx["municipality"]
    mun.plot(ax=a2, color=style.LAND, linewidth=0)
    ua[ua["year"] == 2022].plot(ax=a2, color=style.ORANGE, linewidth=0)
    mun.boundary.plot(ax=a2, color=style.INK, linewidth=0.8)
    ctx["highways"].plot(ax=a2, color=style.INK, linewidth=0.9)
    style.map_axes(a2, mun.total_bounds, pad=1500)
    style.scalebar(a2, km=10, loc=(0.06, 0.05))
    fig.text(0.03, 1 - (HEAD + 0.1) / H, "Rio Grande do Sul", fontsize=10.5, fontweight="semibold", color=style.INK, va="top")
    fig.text(0.55, 1 - (HEAD + 0.1) / H, "Municipality of Santa Cruz do Sul", fontsize=10.5, fontweight="semibold",
             color=style.INK, va="top")
    _legend(fig, [Patch(facecolor=style.ORANGE, label="Urbanized area, 2022"), Line2D([], [], color=style.INK, lw=1.2, label="Highways")],
            0.82, (FOOT + 1.6) / H)
    style.header(fig, "Santa Cruz do Sul, a medium-sized city",
                 "A tobacco-industry hub of about 133,000 people (2022) in the Rio Pardo valley, Rio Grande do Sul, Brazil.")
    style.footer(fig, style.SOURCE.replace("(City of", "and IBGE municipal boundaries (City of"))
    style.save(fig, out)
