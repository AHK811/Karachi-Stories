"""M2.0 world-coordinate contract tests. Exits non-zero on FAIL."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from pyproj import CRS, Geod, Transformer
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).parent))
from derive_world_origin_m20 import CHUNK_M, GEOD, bounds_of, load, snyder_tm
_ROOT = Path(__file__).resolve().parents[2]

CFG_PATH = _ROOT / "config/world_coordinates.json"
CANON = _ROOT / "GIS/canonical/v1.0.0"
RESULTS = []


def check(name, ok, detail):
    RESULTS.append((name, "PASS" if ok else "FAIL", detail))


def rings(geom):
    """Every exterior and interior ring of any polygonal geometry type."""
    if geom.geom_type in ("Polygon", "LinearRing"):
        yield from geom.interiors
        yield geom.exterior
    elif geom.geom_type == "GeometryCollection":
        for g in geom.geoms:
            yield from rings(g)
    elif geom.geom_type.startswith("Multi"):
        for g in geom.geoms:
            yield from rings(g)
    else:
        raise AssertionError(f"unexpected geometry type {geom.geom_type}")


def main():
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    E0, N0 = cfg["origin"]["E0"], cfg["origin"]["N0"]
    tr = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(32642), always_xy=True)
    inv = Transformer.from_crs(CRS.from_epsg(32642), CRS.from_epsg(4326), always_xy=True)

    required = ["storage_crs", "working_crs", "units", "scale", "chunk_size_m", "origin",
                "extent", "axis_convention", "transformations", "floating_origin", "measured"]
    check("01 config complete and origin tile-aligned",
          all(k in cfg for k in required) and E0 % CHUNK_M == 0 and N0 % CHUNK_M == 0,
          f"E0={E0} N0={N0} both multiples of {CHUNK_M}; missing keys="
          f"{[k for k in required if k not in cfg]}")

    div = load("l1_admin_karachi_division.geojson")
    b = bounds_of(div, tr)
    check("02 origin is deterministic from the frozen L1 extent",
          E0 == math.floor(b[0] / CHUNK_M) * CHUNK_M and N0 == math.ceil(b[3] / CHUNK_M) * CHUNK_M,
          f"recomputed E0={math.floor(b[0] / CHUNK_M) * CHUNK_M} N0={math.ceil(b[3] / CHUNK_M) * CHUNK_M}")

    e, n = tr.transform(69.0, 0.0)
    check("03 EPSG:32642 definitional anchor", abs(e - 500000.0) < 1e-6 and abs(n) < 1e-6,
          f"E={e:.6f} N={n:.6f}")

    worst = 0.0
    for lon, lat in [(67.01, 24.86), (66.90, 24.80), (67.30, 24.75), (66.60, 24.50),
                     (67.58, 25.67), (66.29, 25.10), (67.05, 25.05), (66.20, 24.30), (67.70, 25.80)]:
        px, py = tr.transform(lon, lat)
        sx, sy = snyder_tm(lon, lat, 69.0, 0.9996)
        worst = max(worst, abs(px - sx), abs(py - sy))
    check("04 pyproj agrees with independent Snyder series", worst < 0.01,
          f"max disagreement={worst * 1000:.2f} mm over 9 control points")

    _, n1 = tr.transform(67.0, 24.0)
    _, n2 = tr.transform(67.0, 25.0)
    e1, _ = tr.transform(66.0, 24.5)
    e2, _ = tr.transform(67.0, 24.5)
    check("05 metric spacing physically plausible",
          110500 < n2 - n1 < 111100 and 100500 < e2 - e1 < 101900,
          f"1 deg lat={n2 - n1:,.1f} m, 1 deg lon at 24.5N={e2 - e1:,.1f} m")

    saddar = (67.0200, 24.8600)
    malir_north = (67.1600, 25.0200)
    gx1, gy1 = tr.transform(*saddar)
    gx2, gy2 = tr.transform(*malir_north)
    z1, z2 = N0 - gy1, N0 - gy2
    check("06 axis convention: north is negative Z, east is positive X",
          gx2 > gx1 and z2 < z1,
          f"game_x {gx1 - E0:,.1f} -> {gx2 - E0:,.1f}; game_z {z1:,.1f} -> {z2:,.1f} "
          f"(northing {gy1:,.1f} -> {gy2:,.1f})")

    minx, miny, maxx, maxy = bounds_of(div, tr)
    worst_rt = 0.0
    pts = 0
    step_m = 2000.0
    n_row = miny
    while n_row <= maxy:
        e_col = minx
        while e_col <= maxx:
            lon0, lat0 = inv.transform(e_col, n_row)
            x, y = tr.transform(lon0, lat0)
            gx, gz = x - E0, N0 - y
            lon1, lat1 = inv.transform(gx + E0, N0 - gz)
            worst_rt = max(worst_rt, GEOD.inv(lon0, lat0, lon1, lat1)[2])
            pts += 1
            e_col += step_m
        n_row += step_m
    check("07 full-chain round trip 4326->32642->game->4326", worst_rt < 1e-6,
          f"max error={worst_rt:.9f} m over {pts} projected grid points at {step_m:.0f} m spacing")

    cols, rows = cfg["extent"]["chunk_cols"], cfg["extent"]["chunk_rows"]
    bad = []
    nvert = 0
    for name in ("l1_admin_karachi_division.geojson", "l1_admin_districts.geojson"):
        for f in json.loads((CANON / "layers" / name).read_text(encoding="utf-8"))["features"]:
            for ring in rings(shape(f["geometry"])):
                for x, y in ring.coords:
                    nvert += 1
                    ex, ny = tr.transform(x, y)
                    cx, cz = math.floor((ex - E0) / CHUNK_M), math.floor((N0 - ny) / CHUNK_M)
                    if not (0 <= cx < cols and 0 <= cz < rows):
                        bad.append((cx, cz))
    check("08 every L1 vertex maps inside the declared chunk grid", not bad and nvert > 1000,
          f"grid={cols}x{rows}, vertices checked={nvert}, out-of-range={len(bad)} {bad[:3]}")

    lx = (minx - E0) % CHUNK_M
    lz = (N0 - maxy) % CHUNK_M
    check("09 chunk-local coordinates lie in [0, chunk_size)",
          0 <= lx < CHUNK_M and 0 <= lz < CHUNK_M, f"local_x={lx:.3f} local_z={lz:.3f}")

    max_abs = max(abs(minx - E0), abs(maxx - E0), abs(N0 - miny), abs(N0 - maxy))
    eps_global = np.nextafter(np.float32(max_abs), np.float32(max_abs * 2)) - np.float32(max_abs)
    eps_local = np.nextafter(np.float32(CHUNK_M), np.float32(CHUNK_M * 2)) - np.float32(CHUNK_M)
    check("10 float32 precision justifies chunk-local coordinates",
          eps_global > 0.001 and eps_local < 0.001,
          f"max global game coord {max_abs:,.0f} m -> float32 step {eps_global * 1000:.2f} mm; "
          f"chunk-local <= {CHUNK_M} m -> step {eps_local * 1000:.3f} mm")

    k = cfg["measured"]["scale_factor_over_division"]
    check("11 EPSG:32642 distortion within documented tolerance",
          0.9998 <= k["min"] and k["max"] <= 1.0006 and k["worst_ppm"] < 600,
          f"k={k['min']}..{k['max']} mean={k['mean']} worst={k['worst_ppm']} ppm over {k['samples']} samples")

    check("12 extent lies wholly inside UTM zone 42N, no zone crossing",
          cfg["extent"]["inside_utm_zone_42_only"],
          f"lon {cfg['extent']['lonlat'][0]}..{cfg['extent']['lonlat'][2]}")

    mismatched = []
    for line in (CANON / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        h, _, name = line.partition("  ")
        if hashlib.sha256((CANON / name.strip()).read_bytes()).hexdigest() != h:
            mismatched.append(name.strip())
    check("13 canonical v1.0.0 unmodified by M2.0", not mismatched,
          f"mismatched={mismatched}")

    check("14 vertical datum recorded as unset rather than invented",
          "UNSET" in cfg["origin"]["vertical_datum"] and cfg["origin"]["vertical_origin_m"] == 0.0,
          f"{cfg['origin']['vertical_datum'][:60]}")

    check("15 engine absence recorded, not assumed",
          cfg["engine"]["godot_executable_found"] is False
          and "unverified" in cfg["engine"]["note"],
          f"godot_found={cfg['engine']['godot_executable_found']}")

    check("16 masks exceeding the administrative extent is flagged, not used as world size",
          cfg["extent"]["masks_exceed_administrative_extent"] is True
          and "artifact" in cfg["origin"]["rule"],
          f"chunk grid {cols}x{rows} from L1 only")

    w = max(len(n) for n, _, _ in RESULTS)
    for n, s, d in RESULTS:
        print(f"{n:<{w}}  {s:<4}  {d}")
    p = sum(1 for _, s, _ in RESULTS if s == "PASS")
    f = len(RESULTS) - p
    print(f"\nTOTAL {len(RESULTS)}  PASS {p}  FAIL {f}")
    print(f"world extent {cfg['extent']['width_m'] / 1000:.1f} x {cfg['extent']['height_m'] / 1000:.1f} km, "
          f"{cols * rows:,} chunks at {CHUNK_M} m")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
