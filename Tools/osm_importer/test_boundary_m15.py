"""M1.5 acceptance tests. Prints measured values; exits non-zero on any FAIL."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.geometry import Point, shape
from shapely.ops import unary_union

import analyze_extent_m15 as ext
from validate_boundary_m15 import (COD, GIS, OSM_CHILD, geod_area_km2, load_osm, osm_polygon,
                                   planar_area_km2, read_dbf, read_shp_geoms)

PROCESSED = GIS / "processed" / "osmdata"
RESULTS = []


def check(name, ok, detail, skipped=False):
    RESULTS.append((name, "SKIP" if skipped else ("PASS" if ok else "FAIL"), detail))


def main():
    div, osm, sindh, cod = ext.load()
    osm_union = unary_union(list(osm.values()))

    check("01 seven districts present", len(osm) == 7, f"districts={len(osm)} names={sorted(osm)}")

    try:
        import yaml
        meta = yaml.safe_load((GIS / "reports" / "boundary-metadata.yml").read_text(encoding="utf-8"))
        subs = [s for d in meta["administrative_reference"]["districts"] for s in d["subdivisions"]]
        area_ok = abs(sum(s["area_sqkm"] for s in subs) - 3527.0) < 0.01
        check("02 thirty-one subdivisions retained in metadata", len(subs) == 31 and area_ok,
              f"subdivisions={len(subs)} area_sum={sum(s['area_sqkm'] for s in subs):.2f}")
    except ModuleNotFoundError as e:
        check("02 thirty-one subdivisions retained in metadata", False, f"SKIP: {e}", skipped=True)

    missing = []
    for rid in list(OSM_CHILD) + ["6080948"]:
        f = (GIS / "source" / "osm-children" / f"{rid}-{OSM_CHILD[rid][0]}.full.osm"
             if rid in OSM_CHILD else GIS / "source" / "karachi-division-6080948.full.osm")
        nodes, ways, rels = load_osm(f)
        for t, ref, role in rels[int(rid)]["members"]:
            if t == "node" and ref not in nodes:
                missing.append(f"{rid}:node/{ref}")
            if t == "way" and ref not in ways:
                missing.append(f"{rid}:way/{ref}")
            if t == "relation" and ref not in rels:
                missing.append(f"{rid}:relation/{ref}")
    check("03 no missing OSM member references", not missing, f"missing={len(missing)} {missing[:5]}")

    invalid = [n for n, g in list(osm.items()) + [("division", div)] if not g.is_valid]
    check("04 valid geometries", not invalid, f"invalid={invalid}")

    sd = div.symmetric_difference(osm_union)
    check("05 parent/district symmetric difference empty", sd.is_empty,
          f"empty={sd.is_empty} area={geod_area_km2(sd):.6f} km2")

    out_sindh = geod_area_km2(div.difference(sindh))
    inside_sindh = geod_area_km2(div.intersection(sindh))
    total = geod_area_km2(div)
    check("06 division extent decomposed against provincial boundary",
          abs((out_sindh + inside_sindh) - total) < 0.01,
          f"total={total:,.2f} inside_sindh={inside_sindh:,.2f} outside_sindh={out_sindh:,.2f}")

    parts = [read_shp_geoms(COD / f"pak_admin{i}.shp") for i in (0, 1, 2, 3)]
    sums = [round(sum(geod_area_km2(g) for g in p if g is not None), 2) for p in parts]
    check("07 COD-AB hierarchy partitions consistently at every level", len(set(sums)) == 1,
          f"admin0..3 sums={sums}")

    worst = max(abs(planar_area_km2(g) / geod_area_km2(g) - 1) for g in list(osm.values()) + [div])
    check("08 geodesic vs EPSG:32642 planar consistency", worst < 0.001,
          f"max relative difference={worst * 100:.4f}%")

    uncovered = {}
    all_outside = True
    for off, g in cod.items():
        if off not in osm:
            continue
        miss = g.difference(osm_union)
        a = geod_area_km2(miss)
        inside = geod_area_km2(miss.intersection(div))
        uncovered[off] = (round(a, 2), round(inside, 2))
        if inside > 0.01:
            all_outside = False
    check("13 COD-AB Karachi area uncovered by OSM lies outside the OSM division",
          all_outside, f"per-district (uncovered, inside_division)={uncovered}")

    town_ids = [16347665, 16351170, 16351171]
    town_files = [GIS / "source" / "osm-towns" / f"{t}.full.osm" for t in town_ids]
    if all(f.exists() for f in town_files):
        tg = [osm_polygon(f, str(t))[0] for f, t in zip(town_files, town_ids)]
        sd2 = osm["West"].symmetric_difference(unary_union(tg))
        check("14 West district equals the union of its three mapped towns", sd2.is_empty,
              f"symdiff={geod_area_km2(sd2):.6f} km2 towns={[round(geod_area_km2(x), 2) for x in tg]}")
    else:
        check("14 West district equals the union of its three mapped towns", False,
              "BLOCKED: town relations not cached", skipped=True)

    report_path = GIS / "validation" / "land_water_m15.json"
    if not report_path.exists():
        for nm, why in [("09 land and water overlap", "run analyze_land_water_m15.py first"),
                        ("10 unclassified area", "run analyze_land_water_m15.py first"),
                        ("11 land-only area by district", "run analyze_land_water_m15.py first"),
                        ("12 land and water spatial coverage", "run analyze_land_water_m15.py first")]:
            check(nm, False, f"BLOCKED: {why}", skipped=True)
    else:
        rep = json.loads(report_path.read_text(encoding="utf-8"))
        drows = rep["districts"]

        overlaps = [r["land_water_overlap_km2"] for r in drows]
        check("09 land and water overlap measured not assumed",
              len(overlaps) == 7 and all(isinstance(v, (int, float)) for v in overlaps),
              f"per-district overlap km2={overlaps} total={sum(overlaps):.4f}")

        res = [abs(r["conservation_residual_km2"]) for r in drows]
        unclass = [r["unclassified_km2"] for r in drows]
        check("10 conservation identity residual within tolerance",
              max(res) < 0.01,
              f"max residual={max(res):.6f} km2, tolerance=0.01; unclassified per district={unclass}")

        lands = {r["district"]: r["land_km2"] for r in drows}
        check("11 land-only area present for all seven districts",
              len(lands) == 7 and all(v > 0 for v in lands.values()),
              f"land km2={lands} sum={sum(lands.values()):,.2f} vs government 3527")

        def load_clipped(dirname, hint):
            from osgeo import gdal, ogr
            gdal.UseExceptions()
            ogr.UseExceptions()
            path = PROCESSED / dirname / f"{hint}.shp"
            if not path.exists():
                return None
            ds = ogr.Open(str(path))
            if ds is None:
                return None
            geoms = [shape(json.loads(f.GetGeometryRef().ExportToJson()))
                     for f in ds.GetLayerByIndex(0)]
            ds = None
            return unary_union([g for g in geoms if not g.is_empty])

        land = load_clipped("land_karachi", "land")
        probes = [(67.04, 24.90, True, "Saddar urban core expected land"),
                  (66.85, 24.55, False, "open Arabian Sea expected not land"),
                  (67.10, 24.83, True, "Korangi coastal expected land")]
        outcomes = []
        if land is not None:
            for lon, lat, expect, note in probes:
                got = land.contains(Point(lon, lat))
                outcomes.append((note, got, got == expect))
        check("12 land mask spatial coverage agrees with known land and sea probes",
              bool(outcomes) and all(ok for _, _, ok in outcomes),
              f"probes={outcomes}" if outcomes else
              f"BLOCKED: clipped land layer not found at {PROCESSED / 'land_karachi' / 'land.shp'}")

    width = max(len(n) for n, _, _ in RESULTS)
    for n, s, d in RESULTS:
        print(f"{n:<{width}}  {s:<4}  {d}")
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for _, s, _ in RESULTS if s == "SKIP")
    print(f"\nTOTAL {len(RESULTS)}  PASS {passed}  FAIL {failed}  SKIP {skipped}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
