import json
import math
import sys
from pathlib import Path

from pyproj import CRS, Geod, Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union
_ROOT = Path(__file__).resolve().parents[2]

CANON = _ROOT / "GIS/canonical/v1.0.0"
CONFIG = _ROOT / "config/world_coordinates.json"
EVIDENCE = _ROOT / "GIS/validation/world_coordinates_m20.json"
CHUNK_M = 512
GEOD = Geod(ellps="WGS84")
A = 6378137.0
F = 1 / 298.257223563


def snyder_tm(lon, lat, cm, k0):
    """Independent 4th-order ellipsoidal transverse Mercator (Snyder 1987), metres."""
    e2 = 2 * F - F * F
    phi, lam = math.radians(lat), math.radians(lon)
    l0 = math.radians(cm)
    N = A / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    T = math.tan(phi) ** 2
    C = e2 / (1 - e2) * math.cos(phi) ** 2
    Aa = (lam - l0) * math.cos(phi)
    M = A * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * phi))
    x = k0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6
                  + (5 - 18 * T + T * 2 + 72 * C - 58 * e2 / (1 - e2)) * Aa ** 5 / 120)
    y = k0 * (M + N * math.tan(phi) * (Aa ** 2 / 2 + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24
                                       + (61 - 58 * T + T * T) * Aa ** 6 / 720))
    return x + 500000.0, y


def load(name):
    return [shape(f["geometry"]) for f in json.loads((CANON / "layers" / name).read_text(encoding="utf-8"))["features"]]


def bounds_of(geoms, tr):
    g = unary_union(geoms)
    p = transform(tr.transform, g)
    return p.bounds


def scale_field(geoms, cm, k0, step_deg=0.05):
    tr = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(32642), always_xy=True)
    g = unary_union(geoms)
    minx, miny, maxx, maxy = g.bounds
    pts = []
    pairs = []
    lat = miny
    while lat <= maxy:
        lon = minx
        while lon <= maxx:
            if g.contains(Point(lon, lat)):
                k = []
                for bearing in (0.0, 90.0):
                    lon2, lat2, _ = GEOD.fwd(lon, lat, bearing, 1000.0)
                    x1, y1 = tr.transform(lon, lat)
                    x2, y2 = tr.transform(lon2, lat2)
                    v = math.hypot(x2 - x1, y2 - y1) / 1000.0
                    k.append(v)
                    pts.append(v)
                pairs.append(k)
            lon += step_deg
        lat += step_deg
    ns = [q[0] for q in pairs]
    ew = [q[1] for q in pairs]

    def worst(vals):
        return round(max(abs(1 - min(vals)), abs(1 - max(vals))) * 1e6, 1)

    return {"samples": len(pts), "points": len(pairs),
            "min": round(min(pts), 6), "max": round(max(pts), 6),
            "mean": round(sum(pts) / len(pts), 6), "worst_ppm": worst(pts),
            "ns_worst_ppm": worst(ns), "ew_worst_ppm": worst(ew),
            "max_pairwise_diff_ppm": round(max(abs(a - b) for a, b in zip(ns, ew)) * 1e6, 2)}


def main():
    div = load("l1_admin_karachi_division.geojson")
    dstr = load("l1_admin_districts.geojson")
    land = load("l2_land_mask_karachi.geojson")
    water = load("l3_water_mask_karachi.geojson")

    tr = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(32642), always_xy=True)
    inv = Transformer.from_crs(CRS.from_epsg(32642), CRS.from_epsg(4326), always_xy=True)

    lon_bounds = unary_union(div).bounds
    all_geoms = unary_union(div + land + water)
    print(f"combined lon/lat extent: {all_geoms.bounds}")
    zone_ok = 66.0 <= all_geoms.bounds[0] and all_geoms.bounds[2] <= 72.0
    print(f"entirely inside UTM zone 42N (66E-72E): {zone_ok}")

    b32 = bounds_of(div, tr)
    b_all = bounds_of(list(all_geoms.geoms) if all_geoms.geom_type == "MultiPolygon" else [all_geoms], tr)
    print(f"division projected bounds E {b32[0]:,.2f}..{b32[2]:,.2f}  N {b32[1]:,.2f}..{b32[3]:,.2f}")

    b_div = bounds_of(div, tr)
    E0 = math.floor(b_div[0] / CHUNK_M) * CHUNK_M
    N0 = math.ceil(b_div[3] / CHUNK_M) * CHUNK_M
    print(f"E0={E0} N0={N0} (tile-aligned to {CHUNK_M} m, from the L1 administrative extent only)")
    print(f"  note: L2/L3 extend to the clip box {b_all[0]:,.0f}..{b_all[2]:,.0f} E, which is a")
    print(f"  processing artifact of clipping, not a world boundary; origin ignores it")

    k42 = scale_field(div, 69.0, 0.9996)
    print(f"EPSG:32642 scale field over division: {k42}")

    alt_cm = round((unary_union(div).centroid.x) / 0.05) * 0.05
    tr_alt = Transformer.from_proj(CRS.from_epsg(4326),
                                   CRS.from_proj4(f"+proj=tmerc +lat_0=0 +lon_0={alt_cm} "
                                                  f"+k_0=0.9996 +x_0=500000 +y_0=0 +ellps=WGS84 +units=m"),
                                   always_xy=True)
    b_alt = transform(tr_alt.transform, unary_union(div)).bounds
    print(f"alternative CM={alt_cm}E bounds E {b_alt[0]:,.2f}..{b_alt[2]:,.2f}  N {b_alt[1]:,.2f}..{b_alt[3]:,.2f}")

    print("=== independent cross-check: pyproj vs Snyder series ===")
    worst = 0.0
    samples = []
    for lon, lat in [(67.01, 24.86), (66.90, 24.80), (67.30, 24.75), (66.60, 24.50),
                     (67.58, 25.67), (66.29, 25.10), (67.05, 25.05)]:
        px, py = tr.transform(lon, lat)
        sx, sy = snyder_tm(lon, lat, 69.0, 0.9996)
        d = max(abs(px - sx), abs(py - sy))
        worst = max(worst, d)
        samples.append({"lon": lon, "lat": lat, "pyproj_e": round(px, 4), "snyder_e": round(sx, 4),
                        "pyproj_n": round(py, 4), "snyder_n": round(sy, 4),
                        "abs_diff_m": round(d, 4)})
        print(f"  {lon},{lat}  dE={px - sx:+.4f} m  dN={py - sy:+.4f} m")
    print(f"max independent disagreement: {worst:.4f} m")

    print("=== definitional invariants ===")
    cx, cy = tr.transform(69.0, 0.0)
    print(f"  at CM/equator: E={cx:.4f} (must be 500000) N={cy:.4f} (must be 0)")
    e1, n1 = tr.transform(67.0, 24.0)
    e2_, n2_ = tr.transform(67.0, 25.0)
    print(f"  1 deg latitude at 67E: {n2_ - n1:,.3f} m (expect ~110,800-111,000)")
    e3, _ = tr.transform(66.0, 24.5)
    e4, _ = tr.transform(67.0, 24.5)
    print(f"  1 deg longitude at 24.5N: {e4 - e3:,.3f} m (expect ~101,000)")

    print("=== round-trip error over the extent ===")
    minx, miny, maxx, maxy = unary_union(div).bounds
    worst_rt = 0.0
    worst_at = None
    count = 0
    lat = miny
    while lat <= maxy:
        lon = minx
        while lon <= maxx:
            x, y = tr.transform(lon, lat)
            lon2, lat2 = inv.transform(x, y)
            err = GEOD.inv(lon, lat, lon2, lat2)[2]
            count += 1
            if err > worst_rt:
                worst_rt, worst_at = err, (lon, lat)
            lon += 0.02
        lat += 0.02
    print(f"  {count} grid points, max geodesic round-trip error {worst_rt:.9f} m at {worst_at}")

    print("=== game-space round trip (4326 -> 32642 -> game -> 32642 -> 4326) ===")
    worst_g = 0.0
    lat = miny
    while lat <= maxy:
        lon = minx
        while lon <= maxx:
            x, y = tr.transform(lon, lat)
            gx, gz = x - E0, N0 - y
            xr, yr = gx + E0, N0 - gz
            lon2, lat2 = inv.transform(xr, yr)
            worst_g = max(worst_g, GEOD.inv(lon, lat, lon2, lat2)[2])
            lon += 0.02
        lat += 0.02
    print(f"  max game round-trip error {worst_g:.9f} m")

    print("=== chunk index sanity at boundaries ===")
    for e, n, label in [(E0, N0, "origin"), (E0 + CHUNK_M, N0 - CHUNK_M, "chunk 1,1"),
                        (E0 - 0.001, N0 + 0.001, "just outside SW/NE"),
                        (b32[0], b32[1], "division SW corner"), (b32[2], b32[3], "division NE corner"),
                        (b32[0], N0, "north-west corner"), (b32[2], b32[1], "south-east corner")]:
        cx_i = math.floor((e - E0) / CHUNK_M)
        cz_i = math.floor((N0 - n) / CHUNK_M)
        print(f"  {label:<20} E={e:,.3f} N={n:,.3f} -> chunk ({cx_i}, {cz_i})")

    cfg = {
        "schema_version": 1, "milestone": "M2.0", "derived_utc": "2026-11-22",
        "baseline_dataset": "canonical GIS v1.0.0",
        "storage_crs": "EPSG:4326", "working_crs": "EPSG:32642",
        "working_crs_definition": "WGS 84 / UTM zone 42N, central meridian 69E, k0 0.9996, false E 500000, false N 0",
        "units": "metre", "scale": "1 projected metre = 1 Godot unit",
        "chunk_size_m": CHUNK_M, "benchmark_chunk_size_m": 256,
        "origin": {
            "E0": E0, "N0": N0,
            "rule": "E0 = floor(min_easting/512)*512 and N0 = ceil(max_northing/512)*512 over the L1 administrative extent only, tile-aligned so every chunk index inside the division is non-negative. L2 and L3 reach the clip box because that is how they were cut, which is a processing artifact and deliberately not used to size the world",
            "vertical_origin_m": 0.0,
            "vertical_datum": "UNSET - no licensed elevation source; game Y uses a documented ground-height fallback of 0 m",
            "immutable": True,
            "change_policy": "changing E0/N0 after chunks exist requires a versioned migration"
        },
        "extent": {
            "lonlat": [round(v, 6) for v in all_geoms.bounds],
            "projected_m": [round(v, 3) for v in b_all],
            "division_projected_m": [round(v, 3) for v in b32],
            "masks_exceed_administrative_extent": bool(b_all[0] < b32[0] - 1 or b_all[2] > b32[2] + 1),
            "inside_utm_zone_42_only": zone_ok,
            "width_m": round(b_all[2] - b_all[0], 1), "height_m": round(b_all[3] - b_all[1], 1),
            "chunk_cols": math.floor((b32[2] - E0) / CHUNK_M) + 1,
            "chunk_rows": math.ceil((N0 - b32[1]) / CHUNK_M)
        },
        "axis_convention": {
            "godot_x": "easting_m - E0, increases eastward",
            "godot_z": "N0 - northing_m, increases southward, so north is negative Z",
            "godot_y": "elevation_m - vertical_origin_m, increases upward",
            "handedness": "right-handed Y-up, Godot 4 default"
        },
        "transformations": {
            "gis_to_game": "x=lonlat_to_epsg32642(lon,lat); game_x=x-E0; game_z=N0-y; game_y=elev-vertical_origin_m",
            "game_to_gis": "x=game_x+E0; y=N0-game_z; lon,lat=epsg32642_to_lonlat(x,y); elev=game_y+vertical_origin_m",
            "chunk_index": "chunk_x=floor((easting-E0)/512); chunk_z=floor((N0-northing)/512)",
            "chunk_to_local": "local_x=easting-(E0+chunk_x*512); local_z=N0-northing-(chunk_z*512) then offset by chunk origin"
        },
        "floating_origin": {
            "status": "deferred to M2.5",
            "rule": "global projected coordinates stay 64-bit and are kept separate from local Godot Vector3; rebasing must move physics bodies, navigation, cameras, particles and audio together or not at all"
        },
        "measured": {
            "scale_factor_over_division": k42,
            "independent_implementation_max_disagreement_m": round(worst, 4),
            "max_lonlat_round_trip_error_m": round(worst_rt, 9),
            "max_game_round_trip_error_m": round(worst_g, 9),
            "control_samples": samples
        },
        "alternatives_evaluated": [{
            "name": f"custom TM, central meridian {alt_cm}E, k0 0.9996",
            "reason_for_test": "zone 42N central meridian 69E lies about 170-200 km east of Karachi, so Karachi sits far from the meridian",
            "bounds_e_m": [round(b_alt[0], 2), round(b_alt[2], 2)],
            "verdict": "lower distortion but breaks the locked EPSG:32642 decision and OSM/UTM tooling familiarity; the measured 32642 error is already far below gameplay tolerance, so EPSG:32642 is retained"
        }],
        "engine": {
            "godot_executable_found": False,
            "note": "no Godot binary on PATH or under C:/D:/E: at depth 3; project.godot declares features 4.7 + GL Compatibility but that string is not evidence of an installed engine. The Godot-side implementation of this contract is therefore a specification, unverified until the editor is installed and a headless test is run."
        }
    }
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(cfg, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote {CONFIG}")
    print(f"chunks over extent: {cfg['extent']['chunk_cols']} x {cfg['extent']['chunk_rows']} "
          f"= {cfg['extent']['chunk_cols'] * cfg['extent']['chunk_rows']} chunks at 512 m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
