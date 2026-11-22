# Canonical GIS dataset v1.0.0 — build and verification

Frozen 2026-11-22 at M1.6. This directory is a **derived, reproducible** artifact. The archives it
is built from are the source of record and are not stored in Git.

## Prerequisites

WSL2 Ubuntu 26.04 with the system GIS stack, verified by `dpkg-query`:

```
osmium-tool 1.19.0-1build1    gdal-bin 3.12.2+dfsg-1build2
python3-gdal 3.12.2           python3-pyproj 3.7.2    python3-shapely 2.1.2
```

## Inputs and their required checksums

| Input | Path | SHA-256 |
|---|---|---|
| OSM division payload | `GIS/source/karachi-division-6080948.full.osm` | `70d7df9a3501c363c12f0e3f30316194f1ace2b1c0692dbc0826f5f27a744a8e` |
| OSM district payloads | `GIS/source/osm-children/*.full.osm` | see `GIS/reports/checksums.sha256` |
| OSMData land | `GIS/source/osmdata/land-polygons-split-4326.zip` | `e43bb195ee646f27edcf38c2a50ce14ae39e0ab64e7ef9964b430dad1e605c6d` |
| OSMData water | `GIS/source/osmdata/water-polygons-split-4326.zip` | `e541274f78a83564f19db62f4aad3258a43d15041659b825e7b7d61ac83fdd9b` |

Verify before rebuilding:

```bash
python3 Tools/osm_importer/verify_archives.py
( cd GIS/source && sha256sum -c ../reports/checksums.sha256 )
```

## Rebuild

Fast path, reusing the validated clipped layers:

```bash
cd Tools/osm_importer && python3 build_canonical_m16.py
```

Full path from the archives, which re-extracts 2.631 GB into WSL ext4 and re-clips, and is the
reproducibility proof:

```bash
cd Tools/osm_importer
python3 build_canonical_m16.py --full --out /tmp/rebuild_check
python3 -c "
import hashlib, pathlib
a = pathlib.Path('/mnt/d/Karachi-Game/GIS/canonical/v1.0.0/layers')
b = pathlib.Path('/tmp/rebuild_check/layers')
for f in sorted(a.glob('*.geojson')):
    g = b / f.name
    ha = hashlib.sha256(f.read_bytes()).hexdigest()
    hb = hashlib.sha256(g.read_bytes()).hexdigest() if g.exists() else 'ABSENT'
    print(f'{f.name:<40} identical={ha == hb}')
"
rm -rf /tmp/rebuild_check /tmp/osmdata_extract
```

Expected: every layer `identical=True`. Measured on 2026-11-22: all four layers identical, full
rebuild from the archives taking 248.7 s.

Only `layers/` is a build output. `manifest.json`, `README.md`, `KNOWN_LIMITATIONS.md` and
`metadata/l4_schema.yml` are hand-authored inputs and are correctly absent from a rebuild tree, so
they must not be included in this comparison. `checksums.sha256` covers all eight files and is
deliberately excluded from its own hash list, because a manifest cannot authenticate itself.

## Determinism rules that make the above possible

- L1 geometry is produced by `osmium export`, not by the project's own ring assembler.
- L2 and L3 are written by GDAL `VectorTranslate`, then feature-sorted by canonical JSON so
  ordering cannot drift.
- Feature properties are serialised with sorted keys.
- Clipping uses `clipSrc` against the fixed box `66.20 24.30 67.70 25.80`; `spatFilter` would keep
  whole uncut polygons and is forbidden here.
- No source geometry is simplified, snapped, repaired or otherwise altered. Nothing needed repair.

## Verification

```bash
cd Tools/osm_importer && python3 test_boundary_m15.py && python3 test_canonical_m16.py
```

Both must exit 0. `test_canonical_m16.py` recomputes every area **from the canonical files** and
compares against `manifest.json`, so the frozen artifact is checked rather than trusted.

## What this dataset is not

Not a cadastral or government boundary dataset. See `KNOWN_LIMITATIONS.md`; items L-01 through
L-06 are administrative questions that require official documents, and L-07 through L-17 bound how
far the classification can be claimed.
