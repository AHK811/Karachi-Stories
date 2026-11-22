import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from osgeo import gdal, ogr
_ROOT = Path(__file__).resolve().parents[2]

gdal.UseExceptions()

ROOT = _ROOT
GIS = ROOT / "GIS"
SRC_OSM = GIS / "source"
SRC_OSM_DATA = GIS / "source" / "osmdata"
CLIPPED = GIS / "processed" / "osmdata"
WORK = Path("/tmp/osmdata_extract")
CANON = GIS / "canonical"
DATASET_VERSION = "1.0.0"
BOX = (66.20, 24.30, 67.70, 25.80)
WKT_BOX = "POLYGON((%.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f))" % (
    BOX[0], BOX[1], BOX[2], BOX[1], BOX[2], BOX[3], BOX[0], BOX[3], BOX[0], BOX[1])
UA = {"User-Agent": "karachi-street-stories/1.0 (canonical dataset build)"}

OFFICIAL = {"6080948": "Karachi Division", "16347667": "West", "16349281": "Central",
            "16350242": "East", "16350632": "Korangi", "16350836": "South",
            "16351022": "Keamari", "16351916": "Malir"}
CHILD = {"16347667": "Orangi", "16349281": "Nazimabad", "16350242": "Gulshan",
         "16350632": "Korangi", "16350836": "Karachi", "16351022": "Keamari",
         "16351916": "Malir"}


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> rc={proc.returncode}: {proc.stderr[:300]}")
    return proc


def osm_payload(rid):
    if rid == "6080948":
        return SRC_OSM / "karachi-division-6080948.full.osm"
    return SRC_OSM / "osm-children" / f"{rid}-{CHILD[rid]}.full.osm"


def export_relation(rid, tmp):
    run(["osmium", "export", "-f", "geojson", "--geometry-types", "polygon", "-e", "-n",
         "-O", "-o", str(tmp), str(osm_payload(rid))])
    data = json.loads(tmp.read_text(encoding="utf-8"))
    feats = [f for f in data["features"] if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]
    if len(feats) != 1:
        raise RuntimeError(f"relation {rid}: expected 1 polygon feature, got {len(feats)}")
    return feats[0]


def clean_props(d):
    return {k: d[k] for k in sorted(d)}


def build_l1(layers_dir):
    division = export_relation("6080948", Path("/tmp/canon_div.geojson"))
    districts = []
    for rid in ["16347667", "16349281", "16350242", "16350632", "16350836", "16351022", "16351916"]:
        f = export_relation(rid, Path(f"/tmp/canon_{rid}.geojson"))
        p = f["properties"]
        f["properties"] = clean_props({
            "osm_relation": int(rid),
            "admin_level": p.get("admin_level"),
            "official_name": OFFICIAL[rid],
            "osm_community_name": p.get("name:en"),
            "osm_name_native": p.get("name"),
            "name_alias_role": "community-mapped alias of the official reference name",
            "source": "OpenStreetMap",
            "licence": "ODbL 1.0",
        })
        districts.append(f)
    division["properties"] = clean_props({
        "osm_relation": 6080948, "admin_level": division["properties"].get("admin_level"),
        "official_name": "Karachi Division", "osm_community_name": division["properties"].get("name:en"),
        "osm_name_native": division["properties"].get("name"), "source": "OpenStreetMap",
        "licence": "ODbL 1.0",
        "extent_policy": "full administrative extent preserved including maritime area",
    })
    for name, feats in [("l1_admin_karachi_division", [division]),
                        ("l1_admin_districts", districts)]:
        doc = {"type": "FeatureCollection", "name": name, "crs": {"type": "name",
               "properties": {"name": "urn:ogc:def:crs:OGC:1.8:CRS8"}}, "features": feats}
        (layers_dir / f"{name}.geojson").write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    return len(districts)


def reextract_and_clip():
    for z, key in [("land-polygons-split-4326.zip", "land"), ("water-polygons-split-4326.zip", "water")]:
        dest = WORK / key
        if not list(dest.rglob(f"{key}_polygons.shp")):
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(SRC_OSM_DATA / z) as zf:
                zf.extractall(dest)
    CLIPPED.mkdir(parents=True, exist_ok=True)
    for key in ("land", "water"):
        src = next(iter(sorted((WORK / key).rglob(f"{key}_polygons.shp"))))
        out = CLIPPED / f"{key}_karachi" / f"{key}.shp"
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            shutil.rmtree(out.parent)
            out.parent.mkdir(parents=True, exist_ok=True)
        gdal.VectorTranslate(str(out), str(src), format="ESRI Shapefile", clipSrc=WKT_BOX)


def build_l2_l3(layers_dir):
    for key in ("land", "water"):
        gj = CLIPPED / f"{key}_karachi.geojson"
        if gj.exists():
            gj.unlink()
        gdal.VectorTranslate(str(gj), str(CLIPPED / f"{key}_karachi" / f"{key}.shp"), format="GeoJSON")
        data = json.loads(gj.read_text(encoding="utf-8"))
        feats = sorted(data["features"], key=lambda f: json.dumps(f, sort_keys=True))
        for f in feats:
            f["properties"] = clean_props(f.get("properties") or {})
            f["properties"].update({"classification_source": "OSMData preprocessed OSM-derived polygons",
                                    "licence": "ODbL 1.0",
                                    "clip_box_lonlat": list(BOX)})
        doc = {"type": "FeatureCollection", "name": f"l{'2' if key == 'land' else '3'}_{key}_karachi",
               "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.8:CRS8"}},
               "features": feats}
        (layers_dir / f"l{'2' if key == 'land' else '3'}_{key}_mask_karachi.geojson").write_text(
            json.dumps(doc, sort_keys=True), encoding="utf-8")
        print(f"  l{'2' if key == 'land' else '3'}_{key}: {len(feats)} features")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="re-extract and re-clip from archives")
    ap.add_argument("--out", default=str(CANON / f"v{DATASET_VERSION}"))
    args = ap.parse_args()

    out = Path(args.out)
    layers = out / "layers"
    if layers.exists():
        shutil.rmtree(layers)
    layers.mkdir(parents=True)

    t0 = time.perf_counter()
    if args.full:
        print("re-extracting and re-clipping from archives")
        reextract_and_clip()
    n_districts = build_l1(layers)
    print(f"L1: 1 division + {n_districts} districts exported via osmium {subprocess.run(['osmium','--version'],capture_output=True,text=True).stdout.splitlines()[0]}")
    build_l2_l3(layers)

    files = sorted(p for p in out.rglob("*")
                   if p.is_file() and p.name != "checksums.sha256")
    sums = {p.relative_to(out).as_posix(): sha256(p) for p in files}
    (out / "checksums.sha256").write_text(
        "".join(f"{v}  {k}\n" for k, v in sorted(sums.items())), encoding="utf-8")
    print(f"built {len(files)} files in {time.perf_counter() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
