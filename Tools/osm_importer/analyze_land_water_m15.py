import csv
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

from osgeo import gdal, ogr
from shapely import wkt as shapely_wkt
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import explain_validity, make_valid

gdal.UseExceptions()

SRC = _ROOT / "GIS/source/osmdata"
WORK = Path("/tmp/osmdata_extract")
PROCESSED = _ROOT / "GIS/processed/osmdata"
VAL = _ROOT / "GIS/validation"
BOX = (66.20, 24.30, 67.70, 25.80)
WKT_BOX = "POLYGON((%.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f))" % (
    BOX[0], BOX[1], BOX[2], BOX[1], BOX[2], BOX[3], BOX[0], BOX[3], BOX[0], BOX[1])
DISTRICTS = ["Central", "East", "South", "West", "Keamari", "Korangi", "Malir"]
GOV = {"Central": 69.0, "East": 139.0, "South": 122.0, "West": 370.0,
       "Keamari": 559.0, "Korangi": 108.0, "Malir": 2160.0}
EXPECTED = {"land-polygons-split-4326.zip": 930863091,
            "water-polygons-split-4326.zip": 908939540}

sys.path.insert(0, str(Path(__file__).parent))
from analyze_extent_m15 import load  # noqa: E402
from validate_boundary_m15 import geod_area_km2, planar_area_km2  # noqa: E402
_ROOT = Path(__file__).resolve().parents[2]

DEFINITIONS = {
    "primary_area_method": "pyproj Geod(ellps=WGS84).geometry_area_perimeter on EPSG:4326 rings",
    "cross_check_method": "planar area of the same geometry reprojected to EPSG:32642",
    "administrative_area": "area of the L1 OSM district polygon, unmodified",
    "land_area": "administrative_area intersected with the OSMData land polygon layer",
    "mapped_water_area": "administrative_area intersected with the OSMData water polygon layer",
    "land_water_overlap": "area inside the district that is in BOTH the land and water layers",
    "unclassified_area": ("administrative_area minus the area covered by the UNION of the land and "
                          "water layers, i.e. inside the boundary but in neither layer"),
    "unclassified_interpretation": ("NOT labelled as ocean. In coastal districts open sea is the "
                                    "likely explanation, but that is an inference, not a measured "
                                    "classification, because no independent bathymetry or sea mask "
                                    "was used."),
    "area_outside_land_polygon": "administrative_area minus the area inside the land layer",
    "conservation_identity": "A_T = A_L + A_W - A_Lw + A_U",
    "identity_derivation": ("holds by construction because A_U is DEFINED as A_T minus the area "
                            "covered by land union water, so the residual measures arithmetic and "
                            "implementation consistency, not geographic correctness"),
    "mutually_exhaustive": "land union water covers the district exactly when A_U is zero",
    "crs_of_layers": "all inputs EPSG:4326; no reprojection of stored geometry, only for measurement",
    "l1_policy": "administrative geometries are read-only here and are never modified or shrunk",
}


def free_gb(mount):
    import os
    st = os.statvfs(mount)
    return st.f_bavail * st.f_frsize / 1e9


def to_shape(geom):
    return shape(json.loads(geom.ExportToJson()))


def extract(zpath, dest):
    dest.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    comp = zpath.stat().st_size
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest)
    el = time.perf_counter() - t0
    files = sorted((f for f in dest.rglob("*") if f.is_file()), key=lambda f: -f.stat().st_size)
    unc = sum(f.stat().st_size for f in files)
    return {"archive": zpath.name, "compressed_bytes": comp, "uncompressed_bytes": unc,
            "seconds": round(el, 2), "ratio": round(unc / comp, 3),
            "mb_per_s": round(unc / max(el, 0.001) / 1e6, 1),
            "internal_files": [{"path": str(f.relative_to(dest)), "bytes": f.stat().st_size}
                               for f in files],
            "c_free_gb_before": None, "c_free_gb_after": None}, files


def inspect_layer(shp, sample_limit=2000):
    ds = ogr.Open(str(shp))
    ly = ds.GetLayerByIndex(0)
    srs = ly.GetSpatialRef()
    rec = {"layer": ly.GetName(), "features": ly.GetFeatureCount(),
           "geometry_type": ogr.GeometryTypeToName(ly.GetGeomType()),
           "crs_auth": srs.GetAuthorityName(None) if srs else None,
           "crs_code": srs.GetAuthorityCode(None) if srs else None,
           "is_geographic": bool(srs.IsGeographic()) if srs else None,
           "is_projected": bool(srs.IsProjected()) if srs else None,
           "bounds": [round(v, 6) for v in ly.GetExtent()],
           "validity_scan": "sampled", "scanned": 0, "empty": 0, "invalid": 0,
           "valid": 0, "null_geom": 0}
    ly.ResetReading()
    for f in ly:
        if rec["scanned"] >= sample_limit:
            break
        g = f.GetGeometryRef()
        rec["scanned"] += 1
        if g is None:
            rec["null_geom"] += 1
            continue
        s = to_shape(g)
        if s.is_empty:
            rec["empty"] += 1
        elif s.is_valid:
            rec["valid"] += 1
        else:
            rec["invalid"] += 1
    ds = None
    return rec


def clip_and_load(src_shp, out_dir, hint):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    target = out_dir / f"{hint}.shp"
    src = ogr.Open(str(src_shp))
    lyr = src.GetLayerByIndex(0)
    src_count = lyr.GetFeatureCount()
    src_extent = lyr.GetExtent()
    t0 = time.perf_counter()
    gdal.VectorTranslate(str(target), str(src_shp), format="ESRI Shapefile", clipSrc=WKT_BOX)
    el = time.perf_counter() - t0
    ds = ogr.Open(str(target))
    ly = ds.GetLayerByIndex(0)
    feats = [to_shape(f.GetGeometryRef()) for f in ly]
    meta = {"source_features": src_count, "clipped_features": ly.GetFeatureCount(),
            "seconds": round(el, 2), "bytes": sum(f.stat().st_size for f in out_dir.glob("*")),
            "source_extent": [round(v, 4) for v in lyr.GetExtent()],
            "clipped_extent": [round(v, 6) for v in ly.GetExtent()]}
    ds = None
    src = None
    geom = unary_union([f for f in feats if not f.is_empty])
    return geom, meta


def geometry_quality(geoms, label):
    invalid_before = [g for g in geoms if not g.is_valid]
    empty = [g for g in geoms if g.is_empty]
    repaired = [make_valid(g) for g in invalid_before]
    invalid_after = [g for g in repaired if not g.is_valid]
    wkts = {g.wkt for g in geoms}
    overlap_pairs = 0
    overlap_area = 0.0
    for i in range(len(geoms)):
        for j in range(i + 1, len(geoms)):
            if geoms[i].intersects(geoms[j]):
                inter = geoms[i].intersection(geoms[j])
                if inter.area > 1e-12:
                    overlap_pairs += 1
                    overlap_area += geod_area_km2(inter)
    return {"layer": label, "features": len(geoms), "empty": len(empty),
            "invalid_before_repair": len(invalid_before),
            "invalid_after_repair": len(invalid_after),
            "distinct_geometries": len(wkts),
            "duplicate_features": len(geoms) - len(wkts),
            "overlapping_pairs": overlap_pairs,
            "overlap_area_km2": round(overlap_area, 4)}


def main():
    VAL.mkdir(parents=True, exist_ok=True)
    report = {"definitions": DEFINITIONS, "clip_box_lonlat": list(BOX),
              "c_free_gb_start": round(free_gb("/mnt/c"), 3),
              "d_free_gb_start": round(free_gb("/mnt/d"), 3)}

    for z, want in EXPECTED.items():
        p = SRC / z
        if not p.exists() or p.stat().st_size != want:
            print(f"ABORT: {z} missing or wrong size ({p.stat().st_size if p.exists() else 'absent'} != {want})")
            return 2
    print("archive sizes verified against expected byte counts")

    extracts, shps = [], {}
    for z, key in [("land-polygons-split-4326.zip", "land"), ("water-polygons-split-4326.zip", "water")]:
        dest = WORK / key
        pre = sorted((f for f in dest.rglob("*.shp")), key=lambda f: -f.stat().st_size) \
            if dest.exists() and "--reextract" not in sys.argv else []
        if pre:
            info = {"archive": z, "reused_existing_extraction": True,
                    "uncompressed_bytes": sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()),
                    "internal_files": [{"path": str(f.relative_to(dest)), "bytes": f.stat().st_size}
                                       for f in sorted((x for x in dest.rglob("*") if x.is_file()),
                                                       key=lambda x: -x.stat().st_size)]}
            print(f"reusing existing extraction for {z}: {info['uncompressed_bytes']:,} B")
        else:
            info, files = extract(SRC / z, dest)
        info["c_free_gb_after"] = round(free_gb("/mnt/c"), 3)
        extracts.append(info)
        if not info.get("reused_existing_extraction"):
            print(f"extracted {z}: {info['uncompressed_bytes']:,} B in {info['seconds']} s "
                  f"({info['mb_per_s']} MB/s, ratio {info['ratio']}x) C: free {info['c_free_gb_after']} GB")
        cand = [f for f in Path(dest).rglob("*.shp")]
        shps[key] = max(cand, key=lambda f: f.stat().st_size)
        print(f"  main shapefile: {shps[key].name} ({shps[key].stat().st_size:,} B)")

    report["extraction"] = extracts
    report["source_inspection"] = {}
    for key, shp in shps.items():
        rec = inspect_layer(shp)
        report["source_inspection"][key] = rec
        print(f"source {key}: layer={rec['layer']} features={rec['features']} geom={rec['geometry_type']} "
              f"CRS={rec['crs_auth']}:{rec['crs_code']} geographic={rec['is_geographic']} "
              f"valid={rec['valid']} invalid={rec['invalid']} empty={rec['empty']} bounds={rec['bounds']}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    land, land_meta = clip_and_load(shps["land"], PROCESSED / "land_karachi", "land")
    water, water_meta = clip_and_load(shps["water"], PROCESSED / "water_karachi", "water")
    report["clipping"] = {"land": land_meta, "water": water_meta}
    print(f"clipped land: {land_meta['clipped_features']}/{land_meta['source_features']} feats "
          f"in {land_meta['seconds']} s -> {land_meta['bytes']:,} B")
    print(f"clipped water: {water_meta['clipped_features']}/{water_meta['source_features']} feats "
          f"in {water_meta['seconds']} s -> {water_meta['bytes']:,} B")

    land_parts = list(land.geoms) if land.geom_type == "MultiPolygon" else [land]
    water_parts = list(water.geoms) if water.geom_type == "MultiPolygon" else [water]
    report["geometry_quality"] = {"clipped_land": geometry_quality(land_parts, "land"),
                                  "clipped_water": geometry_quality(water_parts, "water")}
    for lbl in ("clipped_land", "clipped_water"):
        q = report["geometry_quality"][lbl]
        print(f"{lbl}: features={q['features']} empty={q['empty']} invalid_before={q['invalid_before_repair']} "
              f"invalid_after={q['invalid_after_repair']} duplicates={q['duplicate_features']} "
              f"overlap_pairs={q['overlapping_pairs']} overlap_km2={q['overlap_area_km2']}")

    lw_union = unary_union([land, water])
    div, osm, sindh, cod = load()
    rows = []
    for d in DISTRICTS:
        g = osm[d]
        total = geod_area_km2(g)
        gl = g.intersection(land)
        gw = g.intersection(water)
        a_land = geod_area_km2(gl)
        a_water = geod_area_km2(gw)
        a_ov = geod_area_km2(gl.intersection(gw))
        covered = geod_area_km2(g.intersection(lw_union))
        unclass = total - covered
        outside = geod_area_km2(g.difference(land))
        rows.append({"district": d, "admin_area_km2": round(total, 2),
                     "land_km2": round(a_land, 2), "mapped_water_km2": round(a_water, 2),
                     "land_water_overlap_km2": round(a_ov, 4),
                     "unclassified_km2": round(unclass, 2),
                     "area_outside_land_km2": round(outside, 2),
                     "conservation_residual_km2": round(a_land + a_water - a_ov + unclass - total, 6),
                     "government_km2": GOV[d],
                     "land_vs_government_pct": round((a_land / GOV[d] - 1) * 100, 2),
                     "admin_planar_32642_km2": round(planar_area_km2(g), 2),
                     "land_planar_32642_km2": round(planar_area_km2(gl), 2)})
        r = rows[-1]
        print(f"  {d:<8} admin={r['admin_area_km2']:>9.2f} land={r['land_km2']:>8.2f} "
              f"water={r['mapped_water_km2']:>6.2f} overlap={r['land_water_overlap_km2']:>7.4f} "
              f"unclass={r['unclassified_km2']:>9.2f} resid={r['conservation_residual_km2']:>8.5f} "
              f"gov={GOV[d]:>7.1f} land_vs_gov={r['land_vs_government_pct']:>7.2f}%")

    report["districts"] = rows
    tot = geod_area_km2(div)
    tl = geod_area_km2(div.intersection(land))
    tw = geod_area_km2(div.intersection(water))
    to_ = geod_area_km2(div.intersection(land).intersection(div.intersection(water)))
    tu = tot - geod_area_km2(div.intersection(lw_union))
    report["division"] = {"admin_km2": round(tot, 2), "land_km2": round(tl, 2),
                          "mapped_water_km2": round(tw, 2), "overlap_km2": round(to_, 4),
                          "unclassified_km2": round(tu, 2),
                          "conservation_residual_km2": round(tl + tw - to_ + tu - tot, 6)}
    print(f"DIVISION admin={tot:,.2f} land={tl:,.2f} water={tw:.2f} overlap={to_:.4f} unclass={tu:,.2f}")

    sd = div.symmetric_difference(unary_union(list(osm.values())))
    report["partition"] = {"parent_vs_district_symdiff_km2": round(geod_area_km2(sd), 6),
                           "district_pair_overlaps": []}
    for i in range(len(DISTRICTS)):
        for j in range(i + 1, len(DISTRICTS)):
            a, b = osm[DISTRICTS[i]], osm[DISTRICTS[j]]
            if a.intersects(b):
                ov = geod_area_km2(a.intersection(b))
                if ov > 0.001:
                    report["partition"]["district_pair_overlaps"].append(
                        [DISTRICTS[i], DISTRICTS[j], round(ov, 4)])
    print(f"partition symdiff={report['partition']['parent_vs_district_symdiff_km2']} km2 "
          f"pair overlaps={report['partition']['district_pair_overlaps']}")

    keam = osm["Keamari"]
    report["keamari_wedge"] = {"admin_km2": round(geod_area_km2(keam), 2),
                               "land_km2": round(geod_area_km2(keam.intersection(land)), 2),
                               "unclassified_km2": round(geod_area_km2(keam.difference(lw_union)), 2),
                               "outside_land_km2": round(geod_area_km2(keam.difference(land)), 2)}
    print(f"KEAMARI wedge: admin={report['keamari_wedge']['admin_km2']:,.2f} "
          f"land={report['keamari_wedge']['land_km2']:,.2f} "
          f"outside_land={report['keamari_wedge']['outside_land_km2']:,.2f}")

    report["storage_end"] = {"c_free_gb": round(free_gb("/mnt/c"), 3),
                             "d_free_gb": round(free_gb("/mnt/d"), 3)}

    (VAL / "land_water_m15.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    with open(VAL / "district_measurements_m15.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {VAL/'land_water_m15.json'} and district_measurements_m15.csv")
    print(f"C: free {report['c_free_gb_start']} -> {report['storage_end']['c_free_gb']} GB")

    if "--keep-extract" in sys.argv:
        print("extraction retained (--keep-extract)")
    else:
        print("NOT deleting extraction yet; validation review is required first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
