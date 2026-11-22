import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

from validate_boundary_m15 import (CODES, COD, GIS, OSM_CHILD, geod_area_km2, osm_polygon,
                                   read_dbf, read_shp_geoms)

GOV = {"Central": 69.0, "East": 139.0, "South": 122.0, "West": 370.0,
       "Keamari": 559.0, "Korangi": 108.0, "Malir": 2160.0}
ORDER = ["Central", "East", "South", "West", "Keamari", "Korangi", "Malir"]


def load():
    div, _ = osm_polygon(GIS / "source" / "karachi-division-6080948.full.osm", "6080948")
    osm = {}
    for rid, (alias, official) in OSM_CHILD.items():
        g, _ = osm_polygon(GIS / "source" / "osm-children" / f"{rid}-{alias}.full.osm", rid)
        osm[official] = g
    g1, r1 = read_shp_geoms(COD / "pak_admin1.shp"), read_dbf(COD / "pak_admin1.dbf")
    sindh = next(g for g, row in zip(g1, r1) if row["adm1_name"].strip() == "Sindh" and g is not None)
    g2, r2 = read_shp_geoms(COD / "pak_admin2.shp"), read_dbf(COD / "pak_admin2.dbf")
    cod = {CODES[row["adm2_pcode"]]: g for g, row in zip(g2, r2)
           if row["adm2_pcode"] in CODES and g is not None}
    return div, osm, sindh, cod


def main():
    div, osm, sindh, cod = load()
    cod_union = unary_union(list(cod.values()))
    osm_union = unary_union(list(osm.values()))

    print("=== A. OSM Karachi Division against COD-AB Sindh province extent ===")
    inside = geod_area_km2(div.intersection(sindh))
    outside = geod_area_km2(div.difference(sindh))
    outgeom = div.difference(sindh)
    print(f"  OSM division total   : {geod_area_km2(div):10,.2f} km2")
    print(f"  inside COD-AB Sindh  : {inside:10,.2f} km2")
    print(f"  OUTSIDE COD-AB Sindh : {outside:10,.2f} km2")
    print(f"  outside bbox         : {[round(v, 4) for v in outgeom.bounds] if not outgeom.is_empty else 'empty'}")

    print("\n=== B. per district: OSM area split by COD-AB Sindh and by COD-AB Karachi union ===")
    print(f"  {'district':<9}{'OSM':>10}{'inSindh':>10}{'outSindh':>10}{'inCOD-KHI':>11}{'outCOD-KHI':>12}{'gov':>8}")
    rows = []
    for off in ORDER:
        g = osm[off]
        a = geod_area_km2(g)
        ins = geod_area_km2(g.intersection(sindh))
        outs = geod_area_km2(g.difference(sindh))
        inc = geod_area_km2(g.intersection(cod_union))
        outc = geod_area_km2(g.difference(cod_union))
        rows.append((off, a, ins, outs, inc, outc))
        print(f"  {off:<9}{a:>10,.2f}{ins:>10,.2f}{outs:>10,.2f}{inc:>11,.2f}{outc:>12,.2f}{GOV[off]:>8,.0f}")

    print("\n=== C. is COD-AB Sindh itself land-only? ===")
    print(f"  Sindh admin1 area : {geod_area_km2(sindh):,.2f} km2 (published attr 141,028.29)")
    print(f"  Sindh admin1 bbox : {[round(v, 4) for v in sindh.bounds]}")
    print(f"  parts             : {len(sindh.geoms) if isinstance(sindh, MultiPolygon) else 1}")
    print(f"  Sindh bbox west edge lon {sindh.bounds[0]:.4f} vs Karachi coastline near 66.9-67.1E")

    print("\n=== D. OSM division vs COD-AB Karachi union ===")
    print(f"  symmetric difference : {geod_area_km2(div.symmetric_difference(cod_union)):,.2f} km2")
    print(f"  OSM minus COD-KHI    : {geod_area_km2(div.difference(cod_union)):,.2f} km2")
    print(f"  COD-KHI minus OSM    : {geod_area_km2(cod_union.difference(div)):,.2f} km2")

    print("\n=== E. COD-AB internal partition consistency ===")
    for nm, f in [("admin0", "pak_admin0.shp"), ("admin1", "pak_admin1.shp"),
                  ("admin2", "pak_admin2.shp"), ("admin3", "pak_admin3.shp")]:
        tot = sum(geod_area_km2(g) for g in read_shp_geoms(COD / f) if g is not None)
        print(f"  sum({nm}) = {tot:12,.2f} km2")

    print("\n=== F. does Sindh contain the sea OSM Keamari claims? ===")
    k = osm["Keamari"]
    kin = geod_area_km2(k.intersection(sindh))
    kout = geod_area_km2(k.difference(sindh))
    print(f"  OSM Keamari inside Sindh : {kin:10,.2f} km2  ({(kin / GOV['Keamari'] - 1) * 100:+.1f}% of gov 559)")
    print(f"  OSM Keamari outside Sindh: {kout:10,.2f} km2")
    print(f"  => area Sindh itself claims as Karachi sea but OSM Keamari does not: "
          f"{geod_area_km2(sindh.difference(osm_union).intersection(cod_union)):,.2f} km2")

    return 0


if __name__ == "__main__":
    sys.exit(main())
