import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.ops import unary_union

from analyze_extent_m15 import load
from validate_boundary_m15 import (COD, geod_area_km2, planar_area_km2, read_dbf, read_shp_geoms)

KEYS = ["Central", "East", "South", "West", "Keamari", "Korangi", "Malir"]


def main():
    div, osm, sindh, cod = load()
    osm_union = unary_union(list(osm.values()))
    cod_union = unary_union(list(cod.values()))
    g2, r2 = read_shp_geoms(COD / "pak_admin2.shp"), read_dbf(COD / "pak_admin2.dbf")

    out = {"interpreter": sys.version.split()[0],
           "library_versions": {}}
    for mod in ("shapely", "pyproj", "numpy"):
        try:
            out["library_versions"][mod] = __import__(mod).__version__
        except Exception:
            out["library_versions"][mod] = None
    import shapely
    out["library_versions"]["geos"] = shapely.geos_version_string if hasattr(shapely, "geos_version_string") else None

    m = {}
    m["division_geod"] = geod_area_km2(div)
    m["division_planar"] = planar_area_km2(div)
    m["division_symdiff_vs_townunion_geod"] = geod_area_km2(div.symmetric_difference(osm_union))
    m["division_in_sindh_geod"] = geod_area_km2(div.intersection(sindh))
    m["division_out_sindh_geod"] = geod_area_km2(div.difference(sindh))
    m["division_symdiff_cod_geod"] = geod_area_km2(div.symmetric_difference(cod_union))
    for k in KEYS:
        m[f"{k}_geod"] = geod_area_km2(osm[k])
        m[f"{k}_planar"] = planar_area_km2(osm[k])
        m[f"{k}_exterior_len"] = len(osm[k].exterior.coords)
        m[f"{k}_bounds"] = [round(v, 9) for v in osm[k].bounds]
        m[f"{k}_vs_sindh_geod"] = geod_area_km2(osm[k].difference(sindh))
        m[f"{k}_vs_codunion_geod"] = geod_area_km2(osm[k].difference(cod_union))
    for k in ["Central", "East", "South", "West", "Korangi", "Malir"]:
        m[f"cod_{k}_geod"] = geod_area_km2(cod[k])
    m["cod_admin2_sum"] = sum(geod_area_km2(g) for g in g2 if g is not None)
    m["cod_admin3_sum"] = sum(geod_area_km2(g) for g in read_shp_geoms(COD / "pak_admin3.shp") if g is not None)
    m["sindh_geod"] = geod_area_km2(sindh)

    out["measurements"] = m
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {sys.argv[1]}  interpreter={out['interpreter']}  "
          f"libs={ {k: v for k, v in out['library_versions'].items() if v} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
