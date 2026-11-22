import json
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shapely.ops import unary_union

from validate_boundary_m15 import (COD, GIS, geod_area_km2, osm_polygon, planar_area_km2,
                                   read_dbf, read_shp_geoms)

UA = {"User-Agent": "karachi-street-stories/0.1 (M1.5 West-Orangi boundary investigation)"}
CACHE = GIS / "source" / "osm-towns"
GOV_WEST = {"Orangi Town": 9.0, "Mominabad": 19.0, "Mango Pir": 342.0}
GOV_KEAMARI = {"Baldia": 34.0, "Harbor": 50.0, "Maripur": 450.0, "SITE": 25.0}


def fetch_relation(rid):
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{rid}.full.osm"
    if not dest.exists():
        with urllib.request.urlopen(urllib.request.Request(
                f"https://api.openstreetmap.org/api/0.6/relation/{rid}/full", headers=UA), timeout=120) as r:
            dest.write_bytes(r.read())
        time.sleep(0.8)
    return dest


def child_towns(parent_file, parent_id):
    root = ET.parse(parent_file).getroot()
    for rel in root.iter("relation"):
        if rel.get("id") == str(parent_id):
            return [(int(m.get("ref")), m.get("role")) for m in rel.findall("member")
                    if m.get("type") == "relation"]
    return []


def name_of(path, rid):
    root = ET.parse(path).getroot()
    for rel in root.iter("relation"):
        if rel.get("id") == str(rid):
            tags = {t.get("k"): t.get("v") for t in rel.findall("tag")}
            return tags.get("name:en") or tags.get("name") or "?", tags.get("admin_level", "?")
    return "?", "?"


def main():
    orangi_file = GIS / "source" / "osm-children" / "16347667-Orangi.full.osm"
    towns = child_towns(orangi_file, 16347667)
    print(f"OSM Orangi (official West) references {len(towns)} town relations")

    osm_orangi, _ = osm_polygon(orangi_file, "16347667")
    town_geoms = {}
    for tid, _ in towns:
        nm, lvl = name_of(fetch_relation(tid), tid)
        g, meta = osm_polygon(CACHE / f"{tid}.full.osm", str(tid))
        town_geoms[nm] = g
        print(f"  relation/{tid} L{lvl} {nm:<18} geodesic={geod_area_km2(g):>8.2f} km2  "
              f"planar={planar_area_km2(g):>8.2f}  rings={meta['outer_rings']} parts={meta['parts']} "
              f"valid={g.is_valid}")

    print("\n=== government West subdivisions vs OSM Orangi towns ===")
    print(f"  {'subdivision':<14}{'gov km2':>9}   {'matched OSM town':<20}{'osm km2':>9}{'delta':>9}")
    for sub, area in GOV_WEST.items():
        best = next((nm for nm in town_geoms if sub.split()[0].lower()[:5] in nm.lower()), "?")
        a = geod_area_km2(town_geoms[best]) if best in town_geoms else float("nan")
        print(f"  {sub:<14}{area:>9.1f}   {best:<20}{a:>9.2f}{a - area:>+9.2f}")
    tot_gov = sum(GOV_WEST.values())
    tot_osm = sum(geod_area_km2(g) for g in town_geoms.values())
    print(f"  {'SUM':<14}{tot_gov:>9.1f}   {'OSM town sum':<20}{tot_osm:>9.2f}{tot_osm - tot_gov:>+9.2f}")

    print("\n=== does the union of OSM towns equal the OSM district polygon? ===")
    u = unary_union(list(town_geoms.values()))
    sd = osm_orangi.symmetric_difference(u)
    print(f"  district area={geod_area_km2(osm_orangi):.2f}  town union={geod_area_km2(u):.2f}  "
          f"symdiff={geod_area_km2(sd):.4f} km2  empty={sd.is_empty}")

    print("\n=== where is the missing West area? COD-AB West minus OSM Orangi ===")
    g2 = read_shp_geoms(COD / "pak_admin2.shp")
    r2 = read_dbf(COD / "pak_admin2.dbf")
    cod_west = next(g for g, row in zip(g2, r2) if row["adm2_pcode"] == "PK729" and g is not None)
    missing = cod_west.difference(osm_orangi)
    extra = osm_orangi.difference(cod_west)
    print(f"  COD-AB West area            : {geod_area_km2(cod_west):.2f} km2")
    print(f"  OSM Orangi area             : {geod_area_km2(osm_orangi):.2f} km2")
    print(f"  in COD-AB West, NOT in OSM  : {geod_area_km2(missing):.2f} km2  bbox={[round(v,4) for v in missing.bounds] if not missing.is_empty else 'empty'}")
    print(f"  in OSM Orangi, NOT COD-AB   : {geod_area_km2(extra):.2f} km2  bbox={[round(v,4) for v in extra.bounds] if not extra.is_empty else 'empty'}")

    print("\n=== which OSM district owns the area COD-AB calls West? ===")
    from analyze_extent_m15 import load
    div, osm, sindh, cod = load()
    parts = list(missing.geoms) if missing.geom_type == "MultiPolygon" else [missing]
    for p in sorted(parts, key=lambda g: -g.area)[:8]:
        rep = p.representative_point()
        owners = [nm for nm, g in osm.items() if g.contains(rep)]
        print(f"  part {geod_area_km2(p):>7.2f} km2 at ({rep.x:.4f},{rep.y:.4f}) "
              f"inside OSM district(s): {owners or 'NONE - outside all 7'}")
    print(f"  division contains all of COD-AB West? {div.contains(cod_west)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
