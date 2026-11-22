# M1 boundary validation report

**SUPERSEDED by `boundary-validation-m15.md`.** Retained as the record of what was measured with
improvised code. The interim 5,852.38 km² figure below is replaced by 5,839.94 km² geodesic
(5,841.13 km² planar in EPSG:32642), and the interim 0.21% calibration demonstrated only that the
hand-written integral reproduced COD-AB's own published areas — it did not validate the OSM
polygons. See D-010 to D-015.

Status: **partial — blocked on the apt toolchain install (D-009)**. Every result below was
executed and its output inspected. Nothing here is inferred from documentation.

Environment: WSL2 Ubuntu 26.04 LTS, Python 3.14.4, `curl`, and Python standard library only
(`struct`, `xml.etree`, `math`). GDAL, pyproj, shapely and osmium were **not available** for this
run, which is why several required tests are listed as outstanding rather than passed.

## Results against the nine M1 validation requirements

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | Verify the seven child administrative relations | **PASS** | All 7 resolved as `admin_level=6` relations under 6080948; each fetched via its own `full` endpoint; 7/7 parsed |
| 2 | Validate complete division and district geometry | **PARTIAL** | Division: 18 `outer` ways, 0 `inner`, assembled into **1 ring, 0 unclosed**, 501 vertices. Each district assembled to 1 closed ring. Self-intersection and formal validity checks **not run** (needs shapely) |
| 3 | Compare OSM and HDX independently | **PASS (structural)** | Areas, vertex counts, district partitions and vintages compared below. Geometric overlay comparison **not run** (needs shapely) |
| 4 | Polygon validity, holes, multipolygons, gaps, overlaps | **PARTIAL** | COD-AB multiparts observed: Malir 12, South 2, Bin Qasim 12, Kemari 2. OSM division has **no inner roles** → no holes modelled. Dissolve area-sum test passed (see below). Pairwise overlap/gap areas **not measured** |
| 5 | Area in a suitable projected CRS | **NOT DONE** | Requires pyproj/EPSG:32642. Interim geodesic areas computed instead, calibrated to 0.21% |
| 6 | Compare against the 3,527 km² reference | **FAIL for both sources** | OSM **+65.93%**, COD-AB **+9.35%** — see D-007 |
| 7 | Projected versus geodesic distance distortion | **NOT DONE** | Requires pyproj |
| 8 | Coastal and peripheral coverage | **NOT DONE / raised as the key risk** | South Karachi bbox reaches lon 66.5961, far west of the coastline (~66.9–67.0), indicating maritime area inside the polygon. OSM Keamari 2,519.64 km² vs published 559 km². Needs coastline intersection |
| 9 | Document source, vintage, licence, limitations | **PASS** | `boundary-metadata.yml`, `GIS_DATA_SOURCES.md`, `checksums.sha256` |

## Verified numbers

### Administrative reference (Commissioner Office Karachi)

Reconstructed programmatically from the published enumeration:

- 7 districts, **31 subdivisions** (5+4+5+3+4+4+6).
- District areas sum to **3,527.00 km²**; all 31 subdivision areas sum to **3,527.00 km²**.
- Every single district equals the sum of its own subdivisions (7/7 exact).
- **Verdict: internally consistent at both tiers.** The earlier rejection of the 31 figure was an agent error and is corrected.

### Method calibration (required before trusting any area)

Chamberlain–Duquette geodesic integral on the WGS 84 authalic sphere (R = 6,371,007.180991944 m),
exterior = clockwise, holes subtracted, tested against COD-AB's own published `area_sqkm`:

| District | published | computed | error |
|---|---|---|---|
| Central Karachi | 65.14 | 65.28 | +0.21% |
| East Karachi | 202.92 | 203.35 | +0.21% |
| Korangi Karachi | 104.29 | 104.51 | +0.21% |
| Malir Karachi | 2,726.86 | 2,732.50 | +0.21% |
| South Karachi | 507.63 | 508.70 | +0.21% |
| West Karachi | 241.77 | 242.27 | +0.21% |

Mean absolute error **0.210%**, max **0.212%**. Two bugs were found and fixed during this step: an
inverted exterior/interior orientation test (which produced −200% errors) and a ring assembler that
filtered ways against the node dictionary and therefore built zero rings. Both were caught by
running the code, not by reading it.

### Areas against the reference

| Source | Karachi area (computed) | vs 3,527 km² |
|---|---|---|
| OSM division outline (6080948) | **5,852.38 km²** | **+2,325.38 (+65.93%)** |
| OSM sum of 7 districts | **5,852.38 km²** | matches its own outline exactly |
| COD-AB sum of 6 districts (published attrs) | 3,848.61 km² | +321.61 (+9.12%) |
| COD-AB sum of 6 districts (computed) | 3,856.61 km² | +329.61 (+9.35%) |
| Commissioner Office reference | 3,527 km² | — |

Positive finding: the OSM 7-district dissolve reproduces the division outline to the centare, so the
district set is a consistent partition of that outline. The outline itself is the problem.

Per-district comparison, OSM computed vs Commissioner published:

| Official district | OSM relation / alias | OSM km² | Published km² | Difference |
|---|---|---|---|---|
| West | Orangi (16347667) | 188.81 | 370.00 | −181.19 |
| Central | Nazimabad (16349281) | 64.11 | 69.00 | −4.89 |
| East | Gulshan (16350242) | 146.49 | 139.00 | +7.49 |
| Korangi | Korangi (16350632) | 114.68 | 108.00 | +6.68 |
| South | Karachi (16350836) | 116.27 | 122.00 | −5.73 |
| **Keamari** | Keamari (16351022) | **2,519.64** | 559.00 | **+1,960.64** |
| **Malir** | Malir (16351916) | **2,702.37** | 2,160.00 | **+542.37** |

Keamari alone accounts for 84% of the total overshoot. The four small inner districts agree with the
published areas to within about 5%, which is reassuring for their on-land limits and points squarely
at maritime and peripheral extension, not general sloppiness.

### Vertex density (matters for 1:1 boundary fidelity)

| Source | Karachi vertices |
|---|---|
| OSM division outline | 501 |
| OSM 7 districts combined | 1,566 |
| COD-AB 6 districts | 2,814 (1.8× OSM) |
| COD-AB 18 admin3 towns | 3,838 |

Both candidates are generalised. For a boundary whose only job is clipping data, this is likely
acceptable; it must not be presented as a high-fidelity coastline.

### Administrative currency

| Question | OSM | COD-AB v01 |
|---|---|---|
| Seven districts present? | **Yes** | **No — 6** |
| Keamari present as a district? | **Yes** (16351022) | **No** — only `Kemari Town` PK72101 inside South Karachi |
| Post-2023 names present? | Yes (Orangi/Nazimabad/Gulshan/Karachi) | No (0 occurrences of Gulshan/Nazimabad/Orangi at admin2) |
| Vintage | live as of retrieval | boundaries created 2022-09-02, single valid_on 20220909 |

### COD-AB internal consistency

- admin1 7 records, admin2 160 geometry records / 160 DBF rows, admin3 577 / 577 — matches the
  dataset's own stated 7 / 160 / 577 exactly.
- admin3 area sum for the Karachi districts = 3,848.61 km², identical to the admin2 sum → districts
  and towns partition the same space with no leak.
- CRS read from `.prj` as EPSG:4326; encoding UTF-8 from `.cpg`; downloaded bytes equal the declared
  Content-Length; SHA-256 re-verified against the recorded value (`cod-ab-pak/...zip: OK`).

## Outstanding tests and what unblocks them

| Test | Needs |
|---|---|
| `st_is_valid` / self-intersection / `is_simple` on all 8 polygons | shapely |
| Pairwise district overlap area and gap area | shapely |
| Buffer-0 dissolve comparison versus the division outline | shapely |
| Area in EPSG:32642 projected square metres | pyproj |
| Projected vs geodesic distance distortion at Karachi's longitude | pyproj |
| Marine vs land decomposition, coastline intersection, island handling | osmium + coastline geometry |
| Multipolygon hole preservation through `osmium export` | osmium-tool |
| Rendered OSM-versus-COD-AB comparison map | GDAL or matplotlib |
| `osmium extract --polygon` reference validation | M2, after the polygon is approved |

## Conclusion for project-owner sign-off

Requirement 6 fails for both candidate sources and requirement 8 is the reason it fails. **Do not
authorize M2 extraction on the OSM division outline yet.** The recommended next step is the marine
decomposition, because the evidence says the overshoot is concentrated in one maritime district and
one large inland district rather than being spread evenly.

Data volume so far: `GIS/source` 25 MB, `GIS/interim` 39 MB, `GIS/reports` 16 KB, on a drive with
~133 GiB free. No Pakistan PBF downloaded, no extraction run, no Godot file touched.
