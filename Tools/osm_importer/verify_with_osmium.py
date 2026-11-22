import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.geometry import shape

from validate_boundary_m15 import GIS, OSM_CHILD, geod_area_km2, osm_polygon, planar_area_km2

TARGETS = [("6080948", "Karachi Division", GIS / "source" / "karachi-division-6080948.full.osm")] + [
    (rid, f"{alias} ({official})", GIS / "source" / "osm-children" / f"{rid}-{alias}.full.osm")
    for rid, (alias, official) in OSM_CHILD.items()
]
TMP = Path("/tmp/osmium_verify")


def osmium_geometry(path):
    out = TMP / f"{path.stem}.geojson"
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["osmium", "export", "-f", "geojson", "--geometry-types", "polygon", "-e", "-n",
         "-O", "-o", str(out), str(path)],
        capture_output=True, text=True, timeout=900)
    errors = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        return None, errors, proc.returncode
    data = json.loads(out.read_text())
    feats = [f for f in data["features"] if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]
    if len(feats) != 1:
        return None, f"expected 1 polygon feature, got {len(feats)}", proc.returncode
    return shape(feats[0]["geometry"]), errors, proc.returncode


def describe(g):
    geoms = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    return {"parts": len(geoms),
            "outer_rings": len(geoms),
            "inner_rings": sum(len(x.interiors) for x in geoms),
            "vertices": sum(len(x.exterior.coords) + sum(len(h.coords) for h in x.interiors)
                            for x in geoms),
            "geod": geod_area_km2(g),
            "planar": planar_area_km2(g),
            "valid": g.is_valid,
            "bounds": [round(v, 6) for v in g.bounds]}


def main():
    rows = []
    for rid, label, path in TARGETS:
        mine, meta = osm_polygon(path, rid)
        theirs, errors, rc = osmium_geometry(path)
        if theirs is None:
            rows.append({"id": rid, "label": label, "status": "OSMIUM_FAILED",
                         "detail": str(errors)[:220], "rc": rc})
            continue
        a, b = describe(mine), describe(theirs)
        rel = abs(b["geod"] - a["geod"]) / a["geod"]
        sd = geod_area_km2(mine.symmetric_difference(theirs))
        rows.append({"id": rid, "label": label, "status": "OK",
                     "mine": a, "osmium": b,
                     "geodesic_rel_diff": rel,
                     "symmetric_difference_km2": sd,
                     "osmium_geometry_errors": errors or "none",
                     "vertices_match": a["vertices"] == b["vertices"],
                     "parts_match": a["parts"] == b["parts"],
                     "bounds_match": a["bounds"] == b["bounds"]})

    print(f"{'relation':<9}{'label':<24}{'parts':>11}{'vertices':>13}{'geodesic km2':>24}{'symdiff km2':>13}{'rel':>10}")
    for r in rows:
        if r["status"] != "OK":
            print(f"{r['id']:<9}{r['label']:<24} FAILED: {r['detail']}")
            continue
        m, o = r["mine"], r["osmium"]
        print(f"{r['id']:<9}{r['label']:<24}{m['parts']:>4}/{o['parts']:<5}"
              f"{m['vertices']:>5}/{o['vertices']:<6}{m['geod']:>12,.2f}/{o['geod']:<10,.2f}"
              f"{r['symmetric_difference_km2']:>13.6f}{r['geodesic_rel_diff']:>10.2e}")
    print()
    for r in rows:
        if r["status"] != "OK":
            continue
        print(f"  {r['id']:<9} bounds_match={r['bounds_match']} parts_match={r['parts_match']} "
              f"vertices_match={r['vertices_match']} inner(mine/osmium)="
              f"{r['mine']['inner_rings']}/{r['osmium']['inner_rings']} "
              f"osmium_errors={r['osmium_geometry_errors']!r}")

    Path(GIS / "validation" / "osmium_crosscheck.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    ok = [r for r in rows if r["status"] == "OK"]
    worst = max((r["geodesic_rel_diff"] for r in ok), default=1.0)
    worst_sd = max((r["symmetric_difference_km2"] for r in ok), default=1.0)
    print(f"\ncompared {len(ok)}/{len(TARGETS)} relations")
    print(f"max geodesic relative difference : {worst:.3e}")
    print(f"max symmetric difference         : {worst_sd:.6f} km2")
    print(f"all bounds identical             : {all(r['bounds_match'] for r in ok)}")
    print(f"all vertex counts identical      : {all(r['vertices_match'] for r in ok)}")
    print(f"osmium reported geometry errors  : "
          f"{[r['osmium_geometry_errors'] for r in ok if r['osmium_geometry_errors'] != 'none']}")
    return 0 if len(ok) == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
