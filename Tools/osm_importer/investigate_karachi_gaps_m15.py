import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.ops import unary_union

from analyze_extent_m15 import load
from validate_boundary_m15 import COD, geod_area_km2, read_dbf, read_shp_geoms

GOV = {"Central": 69.0, "East": 139.0, "South": 122.0, "West": 370.0,
       "Keamari": 559.0, "Korangi": 108.0, "Malir": 2160.0}


def main():
    div, osm, sindh, cod = load()
    osm_union = unary_union(list(osm.values()))
    cod_union = unary_union(list(cod.values()))

    print("=== A. area COD-AB claims for Karachi that the OSM seven districts do not cover ===")
    total_missing = 0.0
    for off in ["Central", "East", "South", "West", "Korangi", "Malir"]:
        g = cod[off]
        miss = g.difference(osm_union)
        a = geod_area_km2(miss)
        total_missing += a
        inside_div = geod_area_km2(miss.intersection(div))
        print(f"  {off:<8} COD-AB={geod_area_km2(g):>9.2f}  not covered by OSM={a:>8.2f} km2 "
              f"({a / geod_area_km2(g) * 100:>5.1f}%)  of which inside OSM division={inside_div:>8.2f}")
    print(f"  sum of COD-AB Karachi area not covered by OSM districts: {total_missing:,.2f} km2")
    print(f"  union-based symmetric-difference figure was 260.94 km2; per-district sum is "
          f"{total_missing:,.2f} km2")

    print("\n=== B. OSM Manghopir Town against the government 342 km2 figure ===")
    mang = Path(__file__).parent.parent.parent / "GIS" / "source" / "osm-towns" / "16351171.full.osm"
    from validate_boundary_m15 import osm_polygon
    mg, _ = osm_polygon(mang, "16351171")
    deficit = 342.0 - geod_area_km2(mg)
    print(f"  OSM Manghopir Town        : {geod_area_km2(mg):>9.2f} km2")
    print(f"  government 'Mango Pir'    : {342.0:>9.2f} km2")
    print(f"  deficit                   : {-deficit:>9.2f} km2")
    print(f"  Manghopir bbox            : {[round(v, 4) for v in mg.bounds]}")
    print(f"  inside OSM division?      : {div.contains(mg)}")
    print(f"  inside COD-AB Sindh?      : {sindh.contains(mg)}")
    north = mg.bounds[3]
    print(f"  division north edge       : {div.bounds[3]:.4f}   Manghopir north edge: {north:.4f}")
    strip = sindh.difference(osm_union)
    near = strip.intersection(mg.buffer(0.08))
    print(f"  Sindh land adjacent to Manghopir not in any OSM Karachi district: "
          f"{geod_area_km2(near):.2f} km2")

    print("\n=== C. is the government 3,527 km2 reachable from either dataset on land? ===")
    for label, geom in [("OSM division", div), ("COD-AB Karachi union", cod_union),
                        ("OSM division inside Sindh", div.intersection(sindh))]:
        print(f"  {label:<26} {geod_area_km2(geom):>10.2f} km2   vs 3,527 -> "
              f"{(geod_area_km2(geom) / 3527 - 1) * 100:+7.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
