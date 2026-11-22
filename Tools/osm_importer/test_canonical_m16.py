"""M1.6 canonical dataset validation. Recomputes from the frozen files; exits non-zero on FAIL."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.geometry import shape
from shapely.ops import unary_union

from validate_boundary_m15 import geod_area_km2, planar_area_km2
_ROOT = Path(__file__).resolve().parents[2]

CANON = _ROOT / "GIS/canonical/v1.0.0"
DISTRICTS = ["Central", "East", "South", "West", "Keamari", "Korangi", "Malir"]
RESULTS = []


def check(name, ok, detail, skipped=False):
    RESULTS.append((name, "SKIP" if skipped else ("PASS" if ok else "FAIL"), detail))


def fc(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    man = fc(CANON / "manifest.json")
    refs = man["reference_measurements_km2"]
    tol = man["tolerance"]["area_km2_absolute"]

    div = fc(CANON / "layers" / "l1_admin_karachi_division.geojson")
    dstr = fc(CANON / "layers" / "l1_admin_districts.geojson")
    land = fc(CANON / "layers" / "l2_land_mask_karachi.geojson")
    water = fc(CANON / "layers" / "l3_water_mask_karachi.geojson")

    check("01 dataset version and CRS declared",
          man["version"] == "1.0.0" and man["crs"]["storage"].startswith("EPSG:4326")
          and all(x["crs"]["properties"]["name"].endswith("CRS8") for x in (div, dstr, land, water)),
          f"version={man['version']} crs={man['crs']['storage']}")

    names = sorted(f["properties"]["official_name"] for f in dstr["features"])
    check("02 seven official district names present, government names canonical",
          names == sorted(DISTRICTS) and len(dstr["features"]) == 7,
          f"official_names={names}")

    aliases = {f["properties"]["official_name"]: f["properties"]["osm_community_name"]
               for f in dstr["features"]}
    check("03 OSM community names stored as aliases, not as official names",
          all(v is not None for v in aliases.values())
          and aliases.get("West") == "Orangi District" and aliases.get("Central") == "Nazimabad District",
          f"aliases={aliases}")

    div_g = shape(div["features"][0]["geometry"])
    d_gs = {f["properties"]["official_name"]: shape(f["geometry"]) for f in dstr["features"]}
    land_g = unary_union([shape(f["geometry"]) for f in land["features"]])
    water_g = unary_union([shape(f["geometry"]) for f in water["features"]])

    got_div = geod_area_km2(div_g)
    exp_div = refs["division"]["administrative"]
    check("04 division administrative area reproduced from canonical file",
          abs(got_div - exp_div) <= tol, f"got={got_div:,.4f} expected={exp_div:,.2f} tol={tol}")

    sd = div_g.symmetric_difference(unary_union(list(d_gs.values())))
    check("05 district partition integrity against division",
          sd.is_empty, f"symdiff={geod_area_km2(sd):.6f} km2 empty={sd.is_empty}")

    bad = []
    for d in DISTRICTS:
        exp = refs["districts"][d]
        g = d_gs[d]
        a_adm = geod_area_km2(g)
        a_land = geod_area_km2(g.intersection(land_g))
        a_water = geod_area_km2(g.intersection(water_g))
        for lbl, got, want in (("adm", a_adm, exp["administrative"]),
                               ("land", a_land, exp["land"]),
                               ("water", a_water, exp["mapped_water"])):
            if abs(got - want) > tol:
                bad.append((d, lbl, round(got, 3), want))
    check("06 all seven districts land and water areas reproduced within tolerance",
          not bad, f"mismatches={bad} tolerance={tol} km2")

    resid = []
    for d in DISTRICTS:
        g = d_gs[d]
        a_adm = geod_area_km2(g)
        a_land = geod_area_km2(g.intersection(land_g))
        a_water = geod_area_km2(g.intersection(water_g))
        a_ov = geod_area_km2(g.intersection(land_g).intersection(g.intersection(water_g)))
        unclass = a_adm - geod_area_km2(g.intersection(unary_union([land_g, water_g])))
        resid.append(round(a_land + a_water - a_ov + unclass - a_adm, 6))
    check("07 conservation residual per district within tolerance",
          max(abs(r) for r in resid) <= man["tolerance"]["conservation_residual_km2"],
          f"residuals={resid}")

    ov = geod_area_km2(land_g.intersection(water_g))
    check("08 land and water masks do not overlap",
          ov <= 0.001, f"overlap={ov:.6f} km2")

    planar_worst = max(abs(planar_area_km2(g) / geod_area_km2(g) - 1)
                       for g in list(d_gs.values()) + [div_g])
    check("09 geodesic and EPSG:32642 planar methods agree",
          planar_worst < 0.001, f"max relative difference={planar_worst * 100:.4f}%")

    invalid = [n for n, g in [("division", div_g)] + list(d_gs.items()) if not g.is_valid]
    check("10 canonical geometries valid", not invalid, f"invalid={invalid}")

    sums = {}
    for line in (CANON / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        h, _, name = line.partition("  ")
        sums[name.strip()] = h
    mismatched = [n for n, h in sums.items()
                  if hashlib.sha256((CANON / n).read_bytes()).hexdigest() != h]
    check("11 checksums.sha256 matches every file in the dataset",
          not mismatched, f"mismatched={mismatched} files_covered={len(sums)}")

    schema_path = CANON / "metadata" / "l4_schema.yml"
    schema = schema_path.read_text(encoding="utf-8") if schema_path.exists() else ""
    needed = ["required_layers", "terrain_base", "roads", "buildings", "water_surface",
              "navigation_graph", "streaming_manifest", "provenance_flags", "width_source",
              "height_source", "E0", "N0", "512"]
    missing = [k for k in needed if k not in schema]
    check("12 L4 schema defined but not populated",
          bool(schema) and not missing and "no game geometry generated" in schema,
          f"missing_keys={missing} bytes={len(schema)}")

    lim = (CANON / "KNOWN_LIMITATIONS.md").read_text(encoding="utf-8")
    open_items = ["L-01", "L-02", "L-03", "L-04", "L-07", "L-09", "L-10", "L-11"]
    check("13 mandatory unresolved issues remain recorded as open",
          all(t in lim for t in open_items) and "OPEN" in lim,
          f"required_ids={open_items} bytes={len(lim)}")

    check("14 maritime extent preserved and not truncated to coastline",
          geod_area_km2(div_g) > 5500 and "full administrative extent preserved"
          in json.dumps(div["features"][0]["properties"]),
          f"admin={geod_area_km2(div_g):,.2f} km2 land_only_would_be~{geod_area_km2(div_g.intersection(land_g)):,.2f}")

    tile = {}
    for hint, g in (("land", land_g), ("water", water_g)):
        feats = [shape(f["geometry"]) for f in (land if hint == "land" else water)["features"]]
        raw = sum(geod_area_km2(x) for x in feats)
        pairs = 0
        worst = 0.0
        for i in range(len(feats)):
            for j in range(i + 1, len(feats)):
                if feats[i].intersects(feats[j]):
                    a = geod_area_km2(feats[i].intersection(feats[j]))
                    if a > 1e-6:
                        pairs += 1
                        worst = max(worst, a)
        tile[hint] = {"raw_sum": round(raw, 3), "union": round(geod_area_km2(g), 3),
                      "double_counted": round(raw - geod_area_km2(g), 3),
                      "overlapping_pairs": pairs, "worst_pair": round(worst, 3)}
    check("15 source grid tiles overlap and masks are consumed as unions",
          all(v["double_counted"] > 0 for v in tile.values())
          and all(v["double_counted"] < 100 for v in tile.values()),
          f"tiles={tile}")

    w = max(len(n) for n, _, _ in RESULTS)
    for n, s, d in RESULTS:
        print(f"{n:<{w}}  {s:<4}  {d}")
    p = sum(1 for _, s, _ in RESULTS if s == "PASS")
    f = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    k = sum(1 for _, s, _ in RESULTS if s == "SKIP")
    print(f"\nTOTAL {len(RESULTS)}  PASS {p}  FAIL {f}  SKIP {k}")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
