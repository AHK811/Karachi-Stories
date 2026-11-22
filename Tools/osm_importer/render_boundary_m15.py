import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon

from analyze_extent_m15 import load as load_all
from validate_boundary_m15 import GIS, geod_area_km2

OUT = GIS / "reports" / "boundary_comparison_m15.png"
COL = {"Central": "#d97706", "East": "#0d9488", "South": "#7c3aed", "West": "#be123c",
       "Keamari": "#1d4ed8", "Korangi": "#4d7c0f", "Malir": "#a16207"}


def rings_of(geom):
    geoms = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    out = []
    for g in geoms:
        out.append(MplPolygon(list(g.exterior.coords), closed=True))
    return geoms, out


def main():
    div, districts, sindh, cod_map = load_all()
    cod = list(cod_map.items())
    outside = div.difference(sindh)
    outside_km2 = geod_area_km2(outside)

    fig, axes = plt.subplots(1, 2, figsize=(17, 9.5))
    for ax, (xlim, ylim, title) in zip(
            axes, [((66.20, 67.70), (24.30, 25.80),
                    "A. Full OSM Karachi Division outline (note offshore extent)"),
                   ((66.80, 67.35), (24.60, 25.25),
                    "B. Urban core: OSM districts vs COD-AB 2022 districts")]):
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect(1.0 / 0.906)
        ax.grid(True, ls=":", lw=0.5, alpha=0.6)
        ax.set_xticks([x for x in (66.25, 66.5, 66.75, 67.0, 67.25, 67.5) if x >= xlim[0] and x <= xlim[1]])
        ax.set_yticks([y for y in (24.4, 24.7, 25.0, 25.3, 25.6) if y >= ylim[0] and y <= ylim[1]])
        ax.set_xlabel("Longitude (EPSG:4326)")
        ax.set_ylabel("Latitude (EPSG:4326)")
        ax.set_title(title, fontsize=10.5)

        if xlim[1] - xlim[0] > 1.0:
            g, patches = rings_of(div)
            ax.add_collection(PatchCollection(patches, facecolor="#0ea5e9", edgecolor="#0ea5e9",
                                              alpha=0.35, label="OSM division fill"))
            for gg in g:
                ax.plot(*zip(*list(gg.exterior.coords) + list(gg.exterior.coords[:1])),
                        color="black", lw=1.6)
            _, patches_out = rings_of(outside)
            ax.add_collection(PatchCollection(patches_out, facecolor="#ef4444", edgecolor="#7f1d1d",
                                              lw=0.4, alpha=0.55, hatch="////",
                                              label=f"outside COD-AB Sindh: {outside_km2:,.0f} km2"))
            for official, gg in districts.items():
                g2, patches2 = rings_of(gg)
                ax.add_collection(PatchCollection(patches2, facecolor=COL[official],
                                                  edgecolor="none", alpha=0.45))
        for official, gg in districts.items():
            g2, patches2 = rings_of(gg)
            ax.add_collection(PatchCollection(patches2, facecolor="none",
                                              edgecolor=COL[official], lw=1.4,
                                              label=f"OSM {official}"))
            c = gg.representative_point()
            if xlim[0] < c.x < xlim[1] and ylim[0] < c.y < ylim[1]:
                ax.annotate(official, (c.x, c.y), fontsize=8, ha="center",
                            color=COL[official], weight="bold")
        for official, gg in cod:
            g3, patches3 = rings_of(gg)
            ax.add_collection(PatchCollection(patches3, facecolor="none", edgecolor="#db2777",
                                              lw=1.1, ls="--", alpha=0.9))
        ax.legend(fontsize=7, loc="upper left", ncol=2, framealpha=0.85)

    fig.suptitle("M1.5 boundary forensic validation: OpenStreetMap relation 6080948 "
                 "(solid, coloured) vs OCHA/HDX COD-AB PAK 2022 (magenta dashed)", fontsize=11)
    fig.text(0.5, 0.02, "Hatched red in panel A is the portion of the OSM administrative polygon "
             "that lies outside the COD-AB Sindh province boundary. It is evidence of offshore "
             "extent, NOT a measured water area: no land/water coastline mask was available "
             "for this run.", ha="center", fontsize=8.5, style="italic")
    fig.tight_layout(rect=(0, 0.035, 1, 0.965))
    fig.savefig(OUT, dpi=125)
    print(f"wrote {OUT}")
    print(f"bytes={OUT.stat().st_size:,}")


if __name__ == "__main__":
    main()
