import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import shape
from shapely.ops import unary_union
_ROOT = Path(__file__).resolve().parents[2]

PROCESSED = _ROOT / "GIS/processed/osmdata"
REPORT = _ROOT / "GIS/validation/land_water_m15.json"
OUT = _ROOT / "GIS/reports/boundary_land_water_m15.png"
COL = {"Central": "#d97706", "East": "#0d9488", "South": "#7c3aed", "West": "#be123c",
       "Keamari": "#1d4ed8", "Korangi": "#4d7c0f", "Malir": "#a16207"}


def load(hint):
    data = json.loads((PROCESSED / f"{hint}_karachi.geojson").read_text(encoding="utf-8"))
    return unary_union([shape(f["geometry"]) for f in data["features"]])


def patches(g):
    geoms = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    return geoms, [MplPolygon(list(x.exterior.coords), closed=True) for x in geoms]


def main():
    land = load("land")
    water = load("water")
    rep = json.loads(REPORT.read_text(encoding="utf-8"))
    from analyze_extent_m15 import load as load_admin
    div, osm, sindh, cod = load_admin()

    fig, axes = plt.subplots(1, 2, figsize=(17.5, 9.5))
    for ax, (xlim, ylim, title) in zip(axes, [
            ((66.20, 67.70), (24.30, 25.80), "A. Karachi Division over the OSMData land/water mask"),
            ((66.75, 67.25), (24.60, 25.15), "B. Harbour, creek and urban core detail")]):
        _, wp = patches(water)
        ax.add_collection(PatchCollection(wp, facecolor="#0369a1", edgecolor="none",
                                          label="mapped water (OSMData water polygons)"))
        _, lp = patches(land)
        ax.add_collection(PatchCollection(lp, facecolor="#d6d3d1", edgecolor="#78716c", lw=0.3,
                                          label="land (OSMData land polygons)"))
        _, dp = patches(div)
        ax.add_collection(PatchCollection(dp, facecolor="none", edgecolor="black", lw=2.0,
                                          label="L1 administrative extent"))
        for name, g in osm.items():
            _, pp = patches(g)
            ax.add_collection(PatchCollection(pp, facecolor=COL[name], edgecolor=COL[name],
                                              lw=1.0, alpha=0.42))
            c = g.representative_point()
            if xlim[0] < c.x < xlim[1] and ylim[0] < c.y < ylim[1]:
                ax.annotate(name, (c.x, c.y), fontsize=8, ha="center", weight="bold",
                            color="white", bbox=dict(fc="#1c1917", pad=1.2, alpha=0.65))
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect(1.101)
        ax.grid(True, ls=":", lw=0.5, alpha=0.5)
        ax.set_xlabel("Longitude (EPSG:4326)")
        ax.set_ylabel("Latitude (EPSG:4326)")
        ax.set_title(title, fontsize=10.5)
        ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)

    d = rep["division"]
    fig.suptitle("M1.5 land/water classification inside the preserved administrative extent: "
                 f"admin {d['admin_km2']:,.2f} km2 = land {d['land_km2']:,.2f} + water "
                 f"{d['mapped_water_km2']:,.2f}, overlap 0.00, unclassified 0.00 km2", fontsize=11)
    fig.text(0.5, 0.02, "L1 administrative boundary is shown unmodified and still contains the "
             "maritime wedge; the land mask is what determines drivable terrain. Keamari: "
             "445.78 km2 land of 2,514.09 km2 administrative.", ha="center", fontsize=8.5,
             style="italic")
    fig.tight_layout(rect=(0, 0.035, 1, 0.955))
    fig.savefig(OUT, dpi=125)
    print(f"wrote {OUT} bytes={OUT.stat().st_size:,}")


if __name__ == "__main__":
    main()
