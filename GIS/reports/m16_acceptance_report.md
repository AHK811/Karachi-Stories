# M1.6 acceptance report — canonical GIS dataset v1.0.0

Date: 2026-11-22. Prepared for project-owner sign-off. Nothing in M2 was started.

## What is frozen

`D:\Karachi-Game\GIS\canonical\v1.0.0\` — 1.6 MB of geometry plus metadata, committed to Git. The
1.84 GB of source archives remain on `D:` outside Git and are the source of record.

| Layer | File | Features | Status |
|---|---|---|---|
| L1 division | `layers/l1_admin_karachi_division.geojson` | 1 | accepted, preserved unchanged including maritime extent |
| L1 districts | `layers/l1_admin_districts.geojson` | 7 | accepted, government names canonical, OSM names as aliases |
| L2 land mask | `layers/l2_land_mask_karachi.geojson` | 97 | accepted with OSMData provenance |
| L3 water mask | `layers/l3_water_mask_karachi.geojson` | 5 | accepted with marine-data caveats |
| L4 game environment | `metadata/l4_schema.yml` | schema only | defined, **not populated** |

Supporting: `manifest.json`, `checksums.sha256` (8 files), `README.md`, `KNOWN_LIMITATIONS.md`
(19 entries).

## Conditions from the authorisation, each answered

| Requirement | Decision recorded | Evidence |
|---|---|---|
| L1 administrative boundary | Accept, preserve unchanged | test 05 partition symdiff 0.000000 km²; test 14 admin 5,839.94 km² > 5,500; geometry produced by osmium, never edited |
| L2 terrestrial classification | Accept with OSMData provenance | test 06 all seven districts reproduced within 0.05 km²; vintage and warnings in manifest |
| L3 mapped water classification | Accept with marine-data caveats | test 08 land/water union overlap 0.000000 km²; L-09 states mapped water is not measured ocean |
| L4 schema defined, not populated | Met | test 12 asserts required keys and the "no game geometry generated" statement |
| CRS and methodology frozen | Met | `Documentation/CRS_AND_MEASUREMENT.md`; test 01 CRS8 declared; test 09 geodesic vs planar 0.0511% |
| Licensing and attribution frozen | Met | ODbL + CC BY-IGO attribution list, copyright URL and both publisher warnings in manifest |
| Manghopir discrepancy | **Remains OPEN** | L-01, test 15 context, West land −49.08% with zero offshore component |
| Malir coverage discrepancy | **Remains OPEN** | L-02, L-03, including the 249.17 km² COD-AB difference |
| Government-area comparisons | **Marked non-equivalent** | `comparison_note` in manifest; L-04 |

## Test results, actually executed

```
test_canonical_m16.py   exit 0   15 tests: 15 PASS, 0 FAIL, 0 SKIP
test_boundary_m15.py    exit 0   14 tests: 14 PASS, 0 FAIL, 0 SKIP
```

Highlights with measured values:

- 04 division area reproduced from the canonical file: **5,839.9402 km²** vs expected 5,839.94
- 05 partition integrity: symmetric difference **empty, 0.000000 km²**
- 06 all 7 districts land and water reproduced: **0 mismatches** at 0.05 km² tolerance
- 07 conservation residuals: max **1e-06 km²**
- 08 land/water union overlap: **0.000000 km²**
- 09 geodesic vs EPSG:32642: max **0.0511%**
- 11 checksums: **8 files, 0 mismatched**
- 15 grid-tile overlap measured, not assumed: land **23.264 km²** double-counted across 8 pairs,
  water **12.039 km²** across 4 pairs
- 14 maritime extent preserved: admin 5,839.94 km² against land-only 3,674.23 km²

## Reproducibility

A full rebuild from the archives — re-extracting 2.5 GB into ext4 and re-clipping both layers — took
**248.7 s** and produced **all four layers byte-identical** to the frozen files.

One correction belongs in this record. My first comparison reported `NOT REPRODUCIBLE`, which was a
**false negative in my own script**: it treated the hand-authored documents as build outputs and
counted their absence from the rebuild tree as failure. All four generated layers matched. The
comparison recipe in `README.md` was fixed to match reality, because shipping a verification command
that lies would be worse than shipping none.

## Source integrity

- Both OSMData archives re-hashed after all processing: match the manifest.
- All eight OSM payloads and the COD-AB archive re-verified against `checksums.sha256`: OK.
- No administrative geometry was simplified, snapped, repaired or altered. Nothing needed repair.

## Storage, monitored throughout

`C:` free moved 24.780 → 20.242 GB at peak during extraction → **34 GB after cleanup** with the WSL
disk trimmed. `/tmp` verified empty. `D:` 132 GB free. Temporary extraction was deleted only after
validation passed.

## Defects found and fixed during the freeze

1. `checksums.sha256` hashed its own previous copy — a manifest cannot authenticate itself; now
   excluded from its own list.
2. `--full` assumed the archive's internal path; the products nest the shapefile inside a
   directory, now discovered by glob instead of hardcoded.
3. The reproducibility comparison counted authored documents as build outputs (above).
4. An earlier claim of "0 overlapping pairs" was measured after union and could not see deliberate
   grid-tile overlap; withdrawn and replaced by test 15.
5. Twice I reported an exit status taken from a `tail` in a pipeline rather than the process that
   mattered, which made a failed run look successful; every run since captures `$?` directly.

## What M1.6 does not claim

It is not an authoritative cadastral or government boundary dataset. It freezes what the evidence
supports. Six open items require official documents, not more computation, and M2 must not convert
any of them into game-world facts — the L4 schema states this as an acceptance contract.

## Recommendation

Sign off v1.0.0 as the canonical baseline with L-01 through L-03 carried forward as open
administrative questions. Then M2 should begin with **one small geographically representative test
district**, not the whole city, as you specified. Awaiting your explicit approval; nothing further
has been started.
