import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
from pyproj import CRS, Geod, Transformer
from shapely import transform as shapely_transform
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import explain_validity
_ROOT = Path(__file__).resolve().parents[2]

GIS = _ROOT / "GIS"
COD = GIS / "interim" / "cod-ab-pak"
CODES = {
    "PK702": "Central",
    "PK704": "East",
    "PK712": "Korangi",
    "PK714": "Malir",
    "PK721": "South",
    "PK729": "West",
}
OSM_CHILD = {
    "16347667": ("Orangi", "West"),
    "16349281": ("Nazimabad", "Central"),
    "16350242": ("Gulshan", "East"),
    "16350632": ("Korangi", "Korangi"),
    "16350836": ("Karachi", "South"),
    "16351022": ("Keamari", "Keamari"),
    "16351916": ("Malir", "Malir"),
}
GOV_AREA = {"Central": 69.0, "East": 139.0, "South": 122.0, "West": 370.0,
            "Keamari": 559.0, "Korangi": 108.0, "Malir": 2160.0}
GEOD = Geod(ellps="WGS84")


def load_osm(path):
    root = ET.parse(path).getroot()
    nodes = {int(n.get("id")): (float(n.get("lon")), float(n.get("lat"))) for n in root.iter("node")}
    ways = {int(w.get("id")): [int(x.get("ref")) for x in w.findall("nd")] for w in root.iter("way")}
    rels = {
        int(r.get("id")): {
            "tags": {t.get("k"): t.get("v") for t in r.findall("tag")},
            "members": [(m.get("type"), int(m.get("ref")), m.get("role") or "") for m in r.findall("member")],
        }
        for r in root.iter("relation")
    }
    return nodes, ways, rels


def chain_rings(wids, ways, nodes):
    adj = defaultdict(list)
    for w in wids:
        nd = ways[w]
        adj[nd[0]].append((w, False))
        adj[nd[-1]].append((w, True))
    used, rings, incomplete = set(), [], []
    for w0 in wids:
        if w0 in used:
            continue
        used.add(w0)
        seq = ways[w0]
        pts = [nodes[x] for x in seq]
        start, end, closed = seq[0], seq[-1], False
        while True:
            if end == start:
                closed = True
                break
            nxt = None
            for cand, rev in adj[end]:
                if cand not in used:
                    nxt = (cand, rev)
                    break
            if nxt is None:
                break
            cand, rev = nxt
            used.add(cand)
            s = ways[cand]
            add = s if not rev else s[::-1]
            pts.extend(nodes[x] for x in add[1:])
            end = add[-1]
        (rings if closed else incomplete).append(pts)
    return rings, incomplete


def osm_polygon(path, rel_id):
    nodes, ways, rels = load_osm(path)
    me = rels[int(rel_id)]["members"]
    ow = [r for t, r, role in me if t == "way" and role == "outer"]
    iw = [r for t, r, role in me if t == "way" and role == "inner"]
    rings_o, bad_o = chain_rings(ow, ways, nodes)
    rings_i, bad_i = chain_rings(iw, ways, nodes)
    polys = []
    prepared = [(r, Polygon(r)) for r in rings_o]
    for r, p in prepared:
        if len(r) < 4:
            continue
        if any(q is not p and p.covers(q) for _, q in prepared):
            continue
        holes = [h for h in rings_i if len(h) > 3 and p.contains(Polygon(h))]
        polys.append(Polygon(r, holes))
    geom = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    return geom, {"outer_rings": len(rings_o), "inner_rings": len(rings_i),
                  "open_outer": len(bad_o), "open_inner": len(bad_i),
                  "parts": len(polys)}


def read_shp_geoms(path):
    data = Path(path).read_bytes()
    flen = struct.unpack(">I", data[24:28])[0] * 2
    out = []
    off = 100
    while off + 8 <= flen:
        _, cl = struct.unpack(">II", data[off:off + 8])
        off += 8
        body = data[off:off + cl * 2]
        off += cl * 2
        if struct.unpack("<i", body[0:4])[0] != 5:
            out.append(None)
            continue
        np_, nc = struct.unpack("<2i", body[36:44])
        parts = struct.unpack(f"<{np_}i", body[44:44 + 4 * np_])
        p = struct.unpack(f"<{2 * nc}d", body[44 + 4 * np_:44 + 4 * np_ + 16 * nc])
        pts = list(zip(p[0::2], p[1::2]))
        bounds = list(parts) + [len(pts)]
        shells, holes, ex = [], [], None
        for i, st in enumerate(parts):
            rg = pts[st:bounds[i + 1]]
            if len(rg) < 4:
                continue
            signed = sum(rg[k][0] * rg[k + 1][1] - rg[k + 1][0] * rg[k][1] for k in range(len(rg) - 1))
            if signed < 0:
                if ex is not None:
                    shells.append(Polygon(ex, holes))
                    holes = []
                ex = rg
            elif ex is not None:
                holes.append(rg)
        if ex is not None:
            shells.append(Polygon(ex, holes))
        out.append(shells[0] if len(shells) == 1 else MultiPolygon(shells))
    return out


def read_dbf(path):
    d = Path(path).read_bytes()
    n = struct.unpack("<I", d[4:8])[0]
    hl = struct.unpack("<H", d[8:10])[0]
    rl = struct.unpack("<H", d[10:12])[0]
    fl, i = [], 32
    while d[i] != 0x0D:
        fl.append((d[i:i + 11].split(b"\0")[0].decode(), d[i + 16]))
        i += 32
    rows = []
    for k in range(n):
        rec = d[hl + k * rl + 1:hl + (k + 1) * rl]
        o = {}
        for nm, w in fl:
            o[nm] = rec[:w].decode("utf-8", "replace").strip()
            rec = rec[w:]
        rows.append(o)
    return rows


_TO_32642 = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(32642), always_xy=True)


def _reproject_coords(coords):
    x, y = _TO_32642.transform(coords[:, 0], coords[:, 1])
    return np.column_stack((x, y))


def to_32642(geom):
    return shapely_transform(geom, _reproject_coords)


def parts_of(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    if isinstance(geom, Polygon):
        return [geom]
    out = []
    for g in getattr(geom, "geoms", []):
        out.extend(parts_of(g))
    return out


def geod_area_km2(geom):
    def one(g):
        a = GEOD.geometry_area_perimeter(g.exterior.coords)[0]
        for h in g.interiors:
            a += GEOD.geometry_area_perimeter(h.coords)[0]
        return abs(a) / 1e6
    return sum(one(g) for g in parts_of(geom))


def planar_area_km2(geom):
    g = to_32642(geom)
    return g.area / 1e6


def report_parts(diff):
    ranked = sorted(parts_of(diff), key=lambda g: -planar_area_km2(g))[:6]
    return [{"km2": round(planar_area_km2(g), 3),
             "centroid_lonlat": [round(g.centroid.x, 5), round(g.centroid.y, 5)],
             "offshore_like": g.bounds[0] < 66.95 or g.bounds[1] < 24.75} for g in ranked]


def main():
    out = {}
    div, divmeta = osm_polygon(GIS / "source" / "karachi-division-6080948.full.osm", "6080948")
    out["division"] = {"meta": divmeta, "valid": div.is_valid,
                      "reason": None if div.is_valid else explain_validity(div),
                      "geodesic_km2": round(geod_area_km2(div), 2),
                      "planar_32642_km2": round(planar_area_km2(div), 2)}

    districts = {}
    for rid, (alias, official) in OSM_CHILD.items():
        g, meta = osm_polygon(GIS / "source" / "osm-children" / f"{rid}-{alias}.full.osm", rid)
        districts[official] = (alias, g, meta)

    union = unary_union([g for _, g, _ in districts.values()])
    sd = div.symmetric_difference(union)
    sd_area = planar_area_km2(sd)
    out["symdiff_division_vs_districtunion_km2"] = round(sd_area, 3)
    out["symdiff_empty"] = bool(sd.is_empty)
    out["symdiff_parts"] = report_parts(sd)

    rows = []
    for official, (alias, g, meta) in sorted(districts.items()):
        rows.append({
            "official": official, "osm_alias": alias,
            "outer_rings": meta["outer_rings"], "inner_rings": meta["inner_rings"],
            "open_rings": meta["open_outer"] + meta["open_inner"], "parts": meta["parts"],
            "valid": g.is_valid,
            "geodesic_km2": round(geod_area_km2(g), 2),
            "planar_km2": round(planar_area_km2(g), 2),
            "gov_km2": GOV_AREA[official],
            "geo_vs_gov_pct": round((geod_area_km2(g) - GOV_AREA[official]) / GOV_AREA[official] * 100, 2),
            "planar_vs_geodesic_pct": round((planar_area_km2(g) / geod_area_km2(g) - 1) * 100, 3),
        })
    rows.sort(key=lambda r: ["Central", "East", "South", "West", "Keamari", "Korangi", "Malir"].index(r["official"]))
    out["districts"] = rows

    cod = read_shp_geoms(COD / "pak_admin2.shp")
    rowsc = read_dbf(COD / "pak_admin2.dbf")
    out["cod_ab"] = []
    for g, r in zip(cod, rowsc):
        if r["adm2_pcode"] in CODES and g is not None:
            out["cod_ab"].append({
                "pcode": r["adm2_pcode"], "name": r["adm2_name"], "official": CODES[r["adm2_pcode"]],
                "published_attr_km2": round(float(r["area_sqkm"]), 2),
                "geodesic_km2": round(geod_area_km2(g), 2),
                "planar_km2": round(planar_area_km2(g), 2),
                "valid": g.is_valid, "parts": len(g.geoms) if isinstance(g, MultiPolygon) else 1,
            })

    t = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(32642), always_xy=True)
    scale = []
    for lon, lat in [(66.98, 24.86), (67.01, 24.86), (67.20, 24.90), (67.35, 25.10),
                     (66.80, 24.80), (67.00, 24.75), (67.00, 25.25)]:
        d = 1000.0
        for bearing, lab in [(0.0, "NS"), (90.0, "EW")]:
            lon2, lat2, _ = GEOD.fwd(lon, lat, bearing, d)
            x1, y1 = t.transform(lon, lat)
            x2, y2 = t.transform(lon2, lat2)
            scale.append({"lon": lon, "lat": lat, "dir": lab,
                          "k": round(math.hypot(x2 - x1, y2 - y1) / d, 6)})
    out["scale_factors"] = scale
    out["k_min"] = min(s["k"] for s in scale)
    out["k_max"] = max(s["k"] for s in scale)
    out["bbox_division"] = [round(v, 5) for v in div.bounds]
    (GIS / "validation").mkdir(parents=True, exist_ok=True)
    (GIS / "validation" / "m15_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    d = out["division"]
    print(f"DIVISION  geodesic={d['geodesic_km2']}  planar32642={d['planar_32642_km2']}  "
          f"valid={d['valid']}  reason={d['reason']}  meta={d['meta']}")
    print(f"BBOX      lon {out['bbox_division'][0]}..{out['bbox_division'][2]}  "
          f"lat {out['bbox_division'][1]}..{out['bbox_division'][3]}")
    print(f"SYMDIFF   parent vs union(districts) = {out['symdiff_division_vs_districtunion_km2']} km2  "
          f"empty={out['symdiff_empty']}  parts={out['symdiff_parts']}")
    print("\nOFFICIAL | OSM_ALIAS | VALID | RINGS(O/I) | PARTS | GEODESIC | PLANAR | GOV | GEO_VS_GOV% | PLANAR_VS_GEO%")
    for r in rows:
        print(f"{r['official']:<8}| {r['osm_alias']:<9}| {str(r['valid']):<5}| "
              f"{r['outer_rings']}/{r['inner_rings']:<3}| {r['parts']:<5}| {r['geodesic_km2']:>9}| "
              f"{r['planar_km2']:>9}| {r['gov_km2']:>7}| {r['geo_vs_gov_pct']:>11}| {r['planar_vs_geodesic_pct']:>9}")
    print("\nCOD-AB | PUBLISHED_ATTR | GEODESIC | PLANAR | VALID | PARTS")
    for c in out["cod_ab"]:
        print(f"{c['official']:<6}| {c['published_attr_km2']:>14}| {c['geodesic_km2']:>9}| "
              f"{c['planar_km2']:>9}| {str(c['valid']):<5}| {c['parts']}")
    print("\nUTM 42N SCALE FACTORS (1 km geodesic baseline)")
    for s in out["scale_factors"]:
        print(f"  {s['lon']}E {s['lat']}N {s['dir']} k={s['k']}")
    print(f"  k_min={out['k_min']} k_max={out['k_max']}")


if __name__ == "__main__":
    sys.exit(main())
