import json
import shutil
import sys
import time
from pathlib import Path

from osgeo import gdal, ogr, osr
_ROOT = Path(__file__).resolve().parents[2]

gdal.UseExceptions()

SRC_DIR = _ROOT / "GIS/interim/cod-ab-pak"
OUT = _ROOT / "GIS/validation/gdal_clip_benchmark.json"
BOX = (66.20, 24.30, 67.70, 25.80)
WKT = "POLYGON((%.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f))" % (
    BOX[0], BOX[1], BOX[2], BOX[1], BOX[2], BOX[3], BOX[0], BOX[3], BOX[0], BOX[1])


def layer_stats(path):
    ds = ogr.Open(str(path))
    ly = ds.GetLayerByIndex(0)
    n = ly.GetFeatureCount()
    deg2 = sum(f.GetGeometryRef().Area() for f in ly)
    geom = ly.GetGeomType()
    ds = None
    return n, deg2, ogr.GeometryTypeToName(geom)


def run(src, dst, label, clip=True):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    target = dst / (dst.name + ".shp")
    opts = {"format": "ESRI Shapefile"}
    if clip:
        opts["clipSrc"] = WKT
    else:
        opts["spatFilter"] = BOX
    t0 = time.perf_counter()
    gdal.VectorTranslate(str(target), str(src), **opts)
    dt = time.perf_counter() - t0
    n, deg2, gname = layer_stats(target)
    src_n, src_deg2, _ = layer_stats(src)
    return {"label": label, "seconds": round(dt, 3), "features": n,
            "source_features": src_n, "area_deg2": round(deg2, 4),
            "source_area_deg2": round(src_deg2, 4), "geometry_type": gname,
            "output_bytes": sum(f.stat().st_size for f in target.parent.glob("*") if f.is_file())}


def main():
    src = SRC_DIR / "pak_admin2.shp"
    src3 = SRC_DIR / "pak_admin3.shp"
    results = {"gdal_version": gdal.VersionInfo("--version"),
               "osmium_version": None,
               "clip_box_lonlat": list(BOX),
               "clip_wkt": WKT, "runs": []}
    results["runs"].append(run(src, Path("/tmp/cb_clip_ext4"), "admin2 -clipsrc WKT to ext4"))
    results["runs"].append(run(src, Path("/tmp/cb_spat_ext4"), "admin2 -spat bbox only to ext4", clip=False))
    results["runs"].append(run(src, _ROOT / "GIS/interim/_cb_clip_d",
                               "admin2 -clipsrc WKT to D: (9p)"))
    results["runs"].append(run(src3, Path("/tmp/cb3_clip_ext4"), "admin3 -clipsrc WKT to ext4"))

    for p in ["/tmp/cb_clip_ext4", "/tmp/cb_spat_ext4", "/tmp/cb3_clip_ext4",
              str(_ROOT / "GIS/interim/_cb_clip_d")]:
        shutil.rmtree(p, ignore_errors=True)

    print(f"GDAL: {results['gdal_version']}")
    print(f"clip box (lon/lat): {BOX}")
    print(f"{'run':<38}{'sec':>7}{'features':>10}{'area deg2':>12}{'out KB':>9}")
    for r in results["runs"]:
        print(f"{r['label']:<38}{r['seconds']:>7.3f}{r['features']:>7}/{r['source_features']:<3}"
              f"{r['area_deg2']:>12.4f}{r['output_bytes'] / 1024:>9.0f}")

    clip = next(r for r in results["runs"] if r["label"].endswith("ext4") and "clipsrc" in r["label"])
    spat = next(r for r in results["runs"] if "spat" in r["label"])
    print(f"\n  clipped area   {clip['area_deg2']:.4f} deg2 vs spat-filtered {spat['area_deg2']:.4f} deg2"
          f" -> cutting removes {spat['area_deg2'] - clip['area_deg2']:.4f} deg2")
    print(f"  feature counts identical: {clip['features'] == spat['features']}"
          f" ({clip['features']} vs {spat['features']})")
    d9p = next(r for r in results["runs"] if "9p" in r["label"])
    print(f"  ext4 {clip['seconds']:.3f} s vs 9p {d9p['seconds']:.3f} s "
          f"-> 9p factor {d9p['seconds'] / clip['seconds']:.2f}x slower")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
