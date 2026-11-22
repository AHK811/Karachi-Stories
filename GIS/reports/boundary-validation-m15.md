# M1.5 — Boundary forensic validation report

Executed 2026-11-22. Environment: WSL2 Ubuntu 26.04, Python 3.14.4, isolated venv at
`D:\Karachi-Game\.venv-gis` (218 MB, on D:, not on C:) containing **Shapely 2.2.0, PyProj 3.8.0
(PROJ 9.8.1), numpy 2.5.5, matplotlib 3.11.2**. Scripts:
`Tools/osm_importer/validate_boundary_m15.py`, `Tools/osm_importer/render_boundary_m15.py`.
Raw results: `GIS/validation/m15_results.json`.

## Toolchain deviation, stated plainly

The approved step A was `sudo apt install osmium-tool gdal-bin python3-gdal python3-pyproj
python3-shapely`. **It could not be executed: `sudo -n true` returns "interactive authentication
is required"**, so the agent cannot install system packages. To avoid stalling M1.5, shapely and
pyproj were installed from official manylinux cp314 wheels into a venv on D:. This is a deviation
from the approved method and from the project's apt-over-pip preference. It is reversible by
deleting one directory and it touched no system package. **osmium-tool and gdal-bin are still
absent**, which is why Task 4 is incomplete (see below).

## Task 1 — environment verification: PASS (partial)

Verified by import and by a physical sanity test: `Geod.fwd(67.01, 24.86, 90°, 1000 m)` returns
lon 67.0198947 / lat 24.8599997, i.e. exactly ~1 km east at that latitude. osmium: absent.
ogrinfo: absent.

## Task 2 — geometry completeness: PASS

All 8 OSM payloads re-checked with reference counting rather than assumption:

| Relation | units | nodes | ways | outer | inner | missing way refs | missing node refs | missing relation refs | ring components | closure |
|---|---|---|---|---|---|---|---|---|---|---|
| 6080948 | Karachi Division (L5) | 501 | 18 | 18 | 0 | 0 | 0 | 0 | 1 | closed |
| 16347667 | Orangi (L6) | 169 | 13 | 13 | 0 | 0 | 0 | 0 | 1 | closed |
| 16349281 | Nazimabad (L6) | 179 | 12 | 12 | 0 | 0 | 0 | 0 | 1 | closed |
| 16350242 | Gulshan (L6) | 180 | 15 | 15 | 0 | 0 | 0 | 0 | 1 | closed |
| 16350632 | Korangi (L6) | 123 | 9 | 9 | 0 | 0 | 0 | 0 | 1 | closed |
| 16350836 | Karachi (L6) | 115 | 9 | 9 | 0 | 0 | 0 | 0 | 1 | closed |
| 16351022 | Keamari (L6) | 316 | 22 | 22 | 0 | 0 | 0 | 0 | 1 | closed |
| 16351916 | Malir (L6) | 484 | 16 | 16 | 0 | 0 | 0 | 0 | 1 | closed |

**Zero missing references anywhere, and every outer-way set forms exactly one connected,
fully-closed component.** Consequence: the area figures below are properties of OSM's geometry,
not artifacts of an incomplete download — which was the specific risk raised after M1.

**Structural limitation found: OSM models no `inner` roles at any level.** No holes are
represented, so any enclosed water body or enclave inside a Karachi district is silently included
in its area. Nothing was silently discarded; this is recorded as a limitation.

## Task 3 — independent area validation: two methods, no tuning

Method A: `pyproj.Geod(ellps="WGS84").geometry_area_perimeter` on the lon/lat rings (true geodesic).
Method B: reproject to **EPSG:32642** with `Transformer`, then planar `shapely` area.

| Official district | OSM alias | Geodesic km² | Planar 32642 km² | Planar vs geodesic | Government ref | Geodesic vs ref |
|---|---|---|---|---|---|---|
| Central | Nazimabad | 63.97 | 63.98 | +0.015% | 69.00 | **−7.29%** |
| East | Gulshan | 146.18 | 146.19 | +0.010% | 139.00 | **+5.16%** |
| South | Karachi | 116.03 | 116.05 | +0.016% | 122.00 | **−4.90%** |
| West | Orangi | 188.42 | 188.45 | +0.019% | 370.00 | **−49.08%** |
| Keamari | Keamari | 2,514.09 | 2,515.37 | +0.051% | 559.00 | **+349.75%** |
| Korangi | Korangi | 114.44 | 114.45 | +0.007% | 108.00 | **+5.96%** |
| Malir | Malir | 2,696.81 | 2,696.63 | −0.007% | 2,160.00 | **+24.85%** |
| **Division outline** | 6080948 | **5,839.94** | **5,841.13** | **+0.020%** | **3,527.00** | **+65.63%** |

The two independent methods agree with each other to **≤0.051% on every unit**, so the discrepancy
is not a projection artifact and not an algorithm artifact.

**Independent confirmation of the toolchain against COD-AB**, whose own DBF publishes an area field:

| District | COD-AB published attr | PyProj geodesic | Planar 32642 | Agreement |
|---|---|---|---|---|
| Central Karachi | 65.14 | 65.14 | 65.15 | to the centare |
| East Karachi | 202.92 | 202.92 | 202.94 | +0.01% |
| Korangi Karachi | 104.29 | 104.29 | 104.30 | exact |
| Malir Karachi | 2,726.86 | 2,726.86 | 2,726.70 | exact |
| South Karachi | 507.63 | 507.62 | 507.80 | −0.002% |
| West Karachi | 241.77 | 241.77 | 241.81 | exact |

This is the correction the project owner asked for: **the earlier 0.21% calibration proved only
that the improvised integral reproduced COD-AB's own numbers. This table proves the libraries
themselves agree with an independent published source to ~0.01%, using two different methods.**
The OSM polygons are therefore genuinely ~65.6% larger than the administrative reference — that
statement is now measured, not inferred.

## Task 5 — topology and parent/child equivalence: PASS, and it is stronger than area

All 8 geometries: `is_valid = True`. No self-intersection reported, no open rings, no missing
components.

**Symmetric difference test (the test the owner explicitly required):**

```
symmetric_difference( division_outline , union(7 district polygons) )
  -> GEOMETRY EMPTY, area = 0.000 km2
```

So the seven districts are not merely equal in total area to the parent — they are **spatially
identical** to it. Requirement "equal total area is not sufficient evidence" is satisfied by a
genuine geometric equivalence test. Parent/child consistency in OSM is therefore **clean**.

Consequence for the discrepancy: because the dissolve is exact, the +65.6% cannot be blamed on
overlaps, gaps or a bad dissolve. It is in the outline itself.

## Task 6 — coordinate system validation: PASS, EPSG:32642 confirmed fit for 1:1

Local scale factor measured by projecting a true 1 km geodesic baseline in NS and EW directions:

| Point | NS k | EW k |
|---|---|---|
| 66.80 E, 24.80 N | 1.000211 | 1.000208 |
| 66.98 E, 24.86 N | 1.000114 | 1.000112 |
| 67.01 E, 24.86 N | 1.000099 | 1.000097 |
| 67.00 E, 24.75 N | 1.000105 | 1.000103 |
| 67.20 E, 24.90 N | 1.000008 | 1.000006 |
| 67.35 E, 25.10 N | 0.999942 | 0.999940 |
| 67.00 E, 25.25 N | 1.000101 | 1.000099 |

**k range 0.99994 … 1.000211 → worst-case linear distortion +211 / −58 parts per million,
about 21 cm per km.** NS and EW agree within ~2 ppm, confirming conformality. Distortion rises
westward, away from the 69°E central meridian, exactly as transverse Mercator predicts.
Metres and square kilometres are kept separate throughout: linear ppm above, areas in km² above.

**Verdict: the locked EPSG:32642 decision is technically sound for this project.** No change
proposed. The M0 assumption of "30–40 cm/km" was pessimistic; measured worst case is ~21 cm/km.

## Task 4 — land versus water: **NOT COMPLETED**

Required: total, terrestrial, water, outside-coastline, hole-contributed and component-contributed
area per district. **Blocked, and I am not substituting an estimate.**

- Natural Earth 10m land polygons: the documented download URL returns **HTTP 500** on both HEAD
  and ranged GET (verified; response body is an HTML error page, 2,704 bytes). Licence itself is
  fine — the site states Natural Earth is "in the public domain", usable for "personal,
  educational, and commercial purposes", attribution optional.
- `osmium-tool` and `gdal-bin` are not installed (sudo blocked), so `ogr2ogr`/`ogrinfo` cannot be
  used to obtain or convert any other coastline product.
- Hand-closing a land polygon from open coastline lines was rejected: it would produce a plausible
  but unvalidated number, which is precisely what this milestone exists to prevent.

Known from geometry alone, without claiming it is the full answer: OSM has **0 inner rings**, so
hole-contributed area is **0.00 km² for every district**, and component-contributed area is 1 part
per district (no multipolygon parts at all — unlike COD-AB, which has 12 parts for Malir and 2 for
South).

## Task 7 — coastal and peripheral coverage: strong evidence, not yet measured

`GIS/reports/boundary_comparison_m15.png` renders the OSM outline, the 7 districts and COD-AB
overlaid, plus a graticule. What it shows:

- **Keamari's seaward boundary is composed of long straight segments**, including a ~40 km
  diagonal running from about (66.72 E, 24.73 N) to (66.90 E, 24.42 N). Straight lines of that
  length over that latitude are a geometric maritime claim, not a mapped shoreline. This is the
  most likely single cause of the +349.75% and it is now visible, though still unquantified.
- **Malir's excess is inland, not maritime.** Its polygon narrows into a neck reaching 25.677 N,
  far north of the city, toward the Thatta side. So Malir's +24.85% is a different problem from
  Keamari's and must not be explained by the sea.
- **The division bounding box is 66.286–67.583 E, 24.427–25.677 N** — the west and south limits
  sit tens of kilometres offshore relative to Karachi's coastline near 66.9–67.1 E.
- In the urban-core panel, **OSM and COD-AB interior district boundaries coincide closely**
  (Central/East/Korangi/West track each other), so the on-land internal geometry is trustworthy.
- Manora, the harbour, Ibrahim Hyderi and the creek area fall in the zone where Keamari and South
  extend; their treatment cannot be judged until a coastline is available.

## Task 8 — comparison against COD-AB, using only comparable units

Genuinely comparable: COD-AB admin2 units map onto official pre-2023 districts Central/East/
Korangi/Malir/South/West — **six of seven**. Keamari has **no** COD-AB district equivalent; it
exists only as admin3 `Kemari Town` (PK72101, 410.91 km²) inside South Karachi. **Keamari is not
silently treated as zero**: it is excluded from the comparison and reported as absent.

| Official district | OSM geodesic | COD-AB geodesic | OSM − COD-AB |
|---|---|---|---|
| Central | 63.97 | 65.14 | −1.17 |
| East | 146.18 | 202.92 | −56.74 |
| South | 116.03 | 507.62 | −391.59 |
| West | 188.42 | 241.77 | −53.35 |
| Korangi | 114.44 | 104.29 | +10.15 |
| Malir | 2,696.81 | 2,726.86 | −30.05 |
| Keamari | 2,514.09 | **absent as district** | n/a |

The comparison is not symmetric because the units are not the same partition: COD-AB puts the
harbour and offshore water inside **South** Karachi (hence its 507.62 km² against a published
government land area of 122 km²), while OSM puts that water inside **Keamari**. Both datasets
therefore contain substantial ocean; they just assign it to different parents. That is a
partitioning difference, and it means **neither source's district areas can be compared to the
government figures until the sea is separated.**

## Acceptance-criteria position

| Criterion | Status |
|---|---|
| Seven districts present | **Met** |
| District area equals parent area | **Met, and strengthened to geometric identity** |
| Area resembles 3,527 km² | **Failed: +65.63%** |
| Valid topology | **Met** (8/8 valid, closed, no missing refs) |
| Complete geometry | **Met** for what OSM models |
| Documented coastal treatment | **NOT met — Task 4 blocked** |
| Correct district coverage | **Partially met**: Keamari and Malir extents unexplained; West −49% unexplained |
| Traceable provenance | **Met** (hashes, URLs, vintages, licences, scripts, raw JSON) |

**Recommendation: do NOT approve this boundary for M2 yet.** It is structurally clean and its CRS
is validated, but the extent is wrong by a measured 65.6% and the cause is only visually evidenced.

## What unblocks the remainder

1. A coastline/land-mask source that actually downloads. Either retry Natural Earth later, or
   approve the apt install so `gdal-bin` can fetch and convert an alternative public-domain product.
2. `osmium-tool`, to export the relation as a proper multipolygon and to confirm my ring assembly
   against a tested implementation rather than my own code.
3. Then Task 4 per district, the offshore-area figure, and the decision between "clip to coastline"
   and "keep administrative extent including sea".

---

# M1.5 continuation — coastline sourcing and the discrepancy explained

Executed 2026-11-22 after the project owner's architecture decision. Evidence files:
`m15_test_output.txt`, `m15_extent_analysis.txt`, `m15_environment.txt` in this directory.
Code: `Tools/osm_importer/analyze_extent_m15.py`, `Tools/osm_importer/test_boundary_m15.py`.

## Task 1 — system environment: **FAILED, still blocked**

`sudo -n true` still returns "interactive authentication is required". Confirmed absent:
`osmium`, `ogrinfo`, `ogr2ogr`, `gdalinfo`, and system `python3-gdal`, `python3-pyproj`,
`python3-shapely` (all `ModuleNotFoundError`). **The instruction to run the original validation
script under system Python could not be executed.** All results below therefore come from the
`.venv-gis` fallback (shapely 2.2.0, pyproj 3.8.0 / PROJ 9.8.1, numpy 2.5.5, matplotlib 3.11.2,
pyyaml), which the owner directed to retain. When the apt install is run, these same tests must be
re-run under system Python to prove reproducibility before the venv is retired.

## Task 2 — OSMData coastline sources: inspected, **not downloaded**

Measured via HTTP before any download, as required:

| Product | Bytes | MiB | Last-Modified |
|---|---|---|---|
| `land-polygons-split-4326.zip` | 930,863,091 | 887.5 | 2026-11-22T01:49:50Z |
| `water-polygons-split-4326.zip` | 908,939,540 | 866.8 | 2026-11-22T01:52:47Z |
| `land-polygons-split-3857.zip` (alt) | 954,988,788 | 910.7 | available |
| `land-polygons-complete-4326.zip` (alt) | 925,704,470 | 882.8 | available |
| `land-polygons-simple-4326.zip` | **404 — does not exist** | | |
| `simplified-land-polygons-complete-4326.zip` | **404 — does not exist** | | |

- Total for the two chosen WGS84 split products: **1,839,802,631 bytes ≈ 1.71 GiB compressed**,
  before extraction, which expands to several gigabytes each. `D:` has 133 GiB free, so capacity is
  not the obstacle; **processing capability is**.
- Licensing: the site states the products follow **ODbL**. Two warnings are recorded verbatim:
  **"Some errors in the OSM data are repaired."** and **"If the OSM data can't be repaired
  automatically, the data here will not be updated."**
- Therefore the OSMData coastline is **OSM-derived, not an independent measurement of the actual
  shoreline**, and it can be silently stale where repair fails. This limitation is binding on every
  land/water figure it produces.
- No download was performed. Downloading 1.71 GiB of global polygons that cannot be clipped without
  `gdal-bin` would be wasteful; `ogr2ogr -clipsrc` is the correct tool and it is absent.

## Task 6 — Natural Earth: **still unavailable**

`ne_10m_land.zip` returned **HTTP 500** on every attempt (HEAD, and three separate ranged GETs,
each producing a 2,704-byte HTML error body) while the site root returns HTTP 200. So the failure is
specific to the download path, not the host. No alternative URL was guessed. Retained per owner
decision as a coarse 1:10,000,000 sanity check only — never as the production shoreline.

## Task 5 — the discrepancy is now explained with measurements, not hypotheses

Testing an alternative idea that needed no new data: how much of the OSM polygon lies outside
Pakistan's own provincial boundary in COD-AB. Result:

```
OSM Karachi Division        5,839.94 km2
  inside COD-AB Sindh       3,718.83 km2   (63.7%)
  OUTSIDE COD-AB Sindh      2,121.11 km2   (36.3%)   bbox 66.2862-67.4498 E, 24.4274-25.6070 N
```

The excess over the 3,527 km² reference is 2,312.94 km². Of that, **2,121.11 km² (91.7%) is area
that not even the COD-AB Sindh province polygon claims** — open Arabian Sea, reached by Keamari's
straight-line seaward boundary. The remaining ~191.83 km² is inside Sindh but beyond the government
figures.

Per district, OSM area split by the provincial boundary:

| District | OSM total | inside Sindh | **outside Sindh** | government | inside vs gov |
|---|---|---|---|---|---|
| Central | 63.97 | 63.97 | 0.00 | 69 | −7.3% |
| East | 146.18 | 146.18 | 0.00 | 139 | +5.2% |
| South | 116.03 | 76.36 | **39.67** | 122 | −37.4% |
| West | 188.42 | 188.42 | **0.00** | 370 | **−49.1%** |
| Keamari | 2,514.09 | 470.50 | **2,043.59** | 559 | −15.8% |
| Korangi | 114.44 | 105.89 | 8.55 | 108 | −2.0% |
| Malir | 2,696.81 | 2,667.51 | 29.30 | 2,160 | **+23.5%** |

This separates the discrepancy into **three distinct causes**, which is why a single "it is the sea"
explanation would have been wrong:

1. **Maritime over-claim (Keamari, South, Korangi):** 2,121.11 km² of open sea inside the OSM
   polygons, 96.3% of it in Keamari. Explained and quantified.
2. **Inland extent difference (Malir):** +536.81 km² against the reference, of which **160.46 km²
   lies inside Sindh but outside COD-AB's entire Karachi union** — that is land COD-AB assigns to
   another district, not sea. Malir's excess is a genuine administrative-definition difference.
3. **West/Orangi is 49.1% too small on land** (188.42 vs 370 km²) with **zero** offshore component.
   This cannot be a maritime artifact and is **not yet explained**. The likely candidates are the
   Manghopir/Maripur peripheral areas and a historical boundary change, but I have not verified
   either and will not correct a boundary on an unverified hypothesis.

OSM division vs COD-AB Karachi union: symmetric difference **2,513.22 km²**, made of
OSM-minus-COD 2,252.27 km² and **COD-minus-OSM 260.94 km²** — the last figure is Karachi area that
COD-AB includes and OSM's seven districts do not, and it must not be lost when choosing a boundary.

## New independent validation of the secondary source

COD-AB's own hierarchy sums to **876,134.13 km² at admin0, admin1, admin2 and admin3 alike** — four
independent levels agreeing to the centare. The secondary source is therefore a gap-free,
overlap-free partition of itself, which strengthens its use as a yardstick. Sindh admin1 measures
141,028.20 km² against its published attribute 141,028.29 km², agreeing to **0.006%**, and has 34
parts (distributary islands and deltas).

Two of my own earlier hypotheses were **disproven by these tests** and are recorded as such:
the `_em` layers are **not** maritime extensions (`_em` is uniformly *smaller* by 1,317.61 km²
nationwide, so it is a different treatment of disputed/excluded areas, not sea), and COD-AB Sindh is
**not** a usable land mask (its bbox reaches 66.5961 E, offshore).

## Task 7 — acceptance tests: 8 PASS, 0 FAIL, 4 SKIP

```
01 seven districts present                                  PASS  districts=7
02 thirty-one subdivisions retained in metadata             PASS  subdivisions=31 area_sum=3527.00
03 no missing OSM member references                         PASS  missing=0
04 valid geometries                                         PASS  invalid=[]
05 parent/district symmetric difference empty               PASS  empty=True area=0.000000 km2
06 division extent decomposed against provincial boundary   PASS  5,839.94 = 3,718.83 + 2,121.11
07 COD-AB hierarchy partitions consistently at every level  PASS  [876134.13] x4
08 geodesic vs EPSG:32642 planar consistency                PASS  max difference 0.0511%
09 land and water overlap                                   SKIP  BLOCKED: no land/water mask
10 unclassified area                                        SKIP  BLOCKED: no land/water mask
11 land-only area by district                               SKIP  BLOCKED: needs OSMData land polygons
12 land and water spatial coverage                          SKIP  BLOCKED: needs OSMData masks
```

## Owner decisions reflected in the plan

The four-layer model is adopted: **L1 administrative boundaries** (OSM 6080948 + 7 districts,
maritime extent **preserved**), **L2 terrestrial land mask** (OSMData land polygons), **L3 water
mask** (OSMData water polygons plus separately identified inland water), **L4 playable world**
(land collides, water is a surface with gameplay limits, the player cannot drive on the sea).
Administrative coverage and terrestrial gameplay coverage are now separate concepts, so no
geographical information is discarded to simplify terrain generation.

Additional recorded limitation, per the owner: OSM's `natural=coastline` convention is understood to
follow **mean high water springs**, so a mapped coastline is not a timeless, legally surveyed
property boundary. No land/water figure from this source may be presented as a legal boundary.

## Recommendation for M1.6

1. **Run the apt install.** It is the only remaining hard blocker for Tasks 9-12 and for verifying
   my ring assembly against `osmium export`.
2. **Then** download the two OSMData split-4326 archives (1.71 GiB) to `GIS\source\osmdata\`, clip
   with `ogr2ogr -clipsrc` to the Karachi extent plus coastline context, and never hand-close a
   broken ring.
3. Report land, water, unclassified and land-water-overlap per district, and check that
   `land + water + unclassified = administrative area` instead of assuming it.
4. **Investigate West/Orangi's −49.1% separately.** It is the one unexplained figure and it is on
   land, so it is the most likely place for a real administrative-geometry defect.
5. Preserve the 260.94 km² that COD-AB includes and OSM excludes; do not let it vanish at sign-off.

---

# M1.5 second continuation — West/Orangi resolved, and the headline reframed

Executed 2026-11-22 after the owner confirmed the sudo install must be run by them. **The apt
install has still not been executed**: `osmium`, `ogrinfo`, `ogr2ogr`, `gdalinfo` remain absent and
system Python still raises `ModuleNotFoundError: No module named 'osgeo'`. Therefore the tasks that
genuinely require GDAL/osmium — system-Python reproduction, the osmium cross-check, and the
coastline download and clipping — are **not done**, and per the owner's instruction the 1.71 GiB
archives were not downloaded.

The West/Orangi investigation needed neither GDAL nor the coastline, so it was completed.

## A defect found in my own measurement code, fixed and regression-tested

`geod_area_km2` crashed on a `GeometryCollection`, which shapely returns when intersecting
geometries that merely touch along a boundary. That is a real case in this dataset, not a
hypothetical one. Fixed by decomposing any geometry into its constituent polygons before measuring.

Because that function underpins every published number, the whole suite was re-run afterwards:
**division 5,839.94 / 5,841.13 km², symmetric difference 0.000000 km², and all seven district areas
are unchanged**, and the tests still exit 0. The fix added a missing case rather than changing any
result.

## West/Orangi is explained, and it is not a geometry error

OSM's West district (relation 16347667, aliased Orangi) is the exact union of its three mapped
town relations — symmetric difference **0.000000 km²**, so the hierarchy is internally consistent
again:

| Subdivision / town | government km² | OSM town km² | delta |
|---|---|---|---|
| Orangi Town (16347665) | 9.00 | 6.28 | −2.72 |
| Mominabad (16351170) | 19.00 | 35.79 | +16.79 |
| **Mango Pir / Manghopir (16351171)** | **342.00** | **146.35** | **−195.65** |
| **Sum** | **370.00** | **188.42** | **−181.58** |

The per-town deltas sum to −181.58 km², exactly the district-level deficit. **The entire West
anomaly is one subdivision: Manghopir.** OSM's Manghopir Town lies wholly inside the OSM division
and inside COD-AB Sindh, and the division's northern edge (25.6768 N) is far beyond Manghopir's
(25.1046 N), so the missing 195.65 km² is **not** sitting unassigned inside Karachi Division. Only
20.57 km² of Sindh land adjacent to Manghopir falls outside all seven OSM districts.

Conclusion, stated carefully: the most plausible explanation is a **definitional difference in what
the government's "Mango Pir" subdivision statistics cover** — it is not an OSM geometry defect and
not a maritime artifact, since both vector datasets describe roughly 146–242 km² for that area while
the government publishes 342 km². **This is not proven, and the item stays open.** The evidence
still required is the underlying government boundary or notification identifying what territory the
342 km² figure covers. **No district boundary is modified, and none is proposed.** An earlier draft
of this report described that explanation as settled; the owner corrected it as an overclaim, and
D-022 now records the issue as unresolved.

## The headline number should be read differently

| Measure | km² | vs 3,527 reference |
|---|---|---|
| OSM division, whole polygon | 5,839.94 | **+65.58%** |
| **OSM division intersected with COD-AB Sindh** | **3,718.83** | **+5.44%** |
| COD-AB Karachi union | 3,848.61 | +9.12% |

Once OSM's offshore over-claim is removed by intersecting with the provincial boundary, OSM's
land-side extent agrees with the administrative reference to within **5.44%**. The +65.6% headline
was therefore dominated by sea, not by a broken land boundary — which supports the owner's decision
to preserve the administrative extent and derive a separate terrestrial mask, rather than treating
the boundary as defective.

Caveat that must not be lost: 3,718.83 km² is **not** a land area. It still contains harbour, creek
and marsh water inside Sindh, so the true terrestrial figure will be lower and remains unmeasured
until the coastline masks are processed.

## The COD-AB-only area is a coverage difference, not an internal hole

All 260.94 km² of COD-AB Karachi area that no OSM district covers lies **entirely outside the OSM
division outline** — the "inside division" component is 0.00 km² for every district:

| COD-AB district | uncovered km² | of which inside OSM division |
|---|---|---|
| Malir | **249.17** | 0.00 |
| West | 5.95 | 0.00 |
| South | 5.82 | 0.00 |
| Central / East / Korangi | 0.00 | 0.00 |

The per-district sum reconciles exactly to the union-based 260.94 km² figure. So OSM's Karachi
Division **excludes about 249 km² that COD-AB counts as Malir Karachi**, plus ~12 km² elsewhere.
That is a genuine boundary-definition difference to resolve at M1.6, and it is the second-largest
real discrepancy after the sea.

## Acceptance tests now 14: 10 PASS, 0 FAIL, 4 SKIP

Added and passing:
- **13** — COD-AB Karachi area uncovered by OSM lies outside the OSM division (per-district values
  printed, all inside-division components 0.00).
- **14** — West district equals the union of its three mapped towns, symdiff 0.000000 km²,
  towns = [6.28, 35.79, 146.35].

Still skipped with their blockers named: land/water overlap, unclassified area, land-only area by
district, land/water spatial coverage.

Evidence: `m15_test_output.txt`, `m15_west_orangi.txt`, `m15_karachi_gaps.txt`.
Scripts: `investigate_west_orangi_m15.py`, `investigate_karachi_gaps_m15.py`.

---

# M1.5 third continuation — system toolchain installed, reproducibility proven, Osmium agrees

Executed 2026-11-22 after the owner ran the interactive install and supplied the full transcript.
**Steps 1 to 4 of the agreed sequence are complete. Step 5 (land/water) has not started**, because
the OSMData archives remain un-downloaded by instruction.

## Step 1 — system environment: **PASS**

| Component | Installed version |
|---|---|
| osmium-tool | 1.19.0-1build1 (libosmium 2.23.0) |
| gdal-bin / python3-gdal | 3.12.2+dfsg-1build2 — GDAL 3.12.2 "Chicoutimi", released 2026-02-03 |
| python3-pyproj | 3.7.2 (PROJ 9.7.1) |
| python3-shapely | 2.1.2 (GEOS 3.14.1) |
| python3-numpy (dependency) | 2.3.5 |

74 packages installed, 64.5 MB downloaded, 239 MB needed. `python3 -c "from osgeo import gdal;
import pyproj, shapely"` now succeeds.

## Step 2 — numerical reproducibility: **PASS, bitwise**

The 14-test suite run under **system** Python: exit 0, **10 PASS, 0 FAIL, 4 SKIP** — same as the
venv.

But matching pass counts are weak evidence, so `dump_measurements.py` exported **57 full-precision
measurements** (geodesic and EPSG:32642 planar areas for all eight OSM geometries and six COD-AB
districts, exterior-ring coordinate counts, bounds to 9 decimals, symmetric differences, provincial
intersections, and the admin2/admin3 national sums) from each interpreter and diffed them:

```
identical keys: 57/57
max absolute difference : 0.000000e+00
max relative difference : 0.000000e+00
ALL VALUES BITWISE IDENTICAL
```

achieved across **different library versions** — shapely 2.2.0 vs 2.1.2, pyproj 3.8.0/PROJ 9.8.1 vs
3.7.2/PROJ 9.7.1, numpy 2.5.5 vs 2.3.5 — with GEOS 3.14.1 common to both. So the recorded results
do not depend on the temporary virtual environment, and the PROJ version difference does not move
these geodesic areas at all.

## Step 3 — independent geometry verification with Osmium: **PASS exactly**

`osmium export -f geojson --geometry-types polygon -e -n` was run against each of the eight cached
`.full.osm` payloads and compared to my custom ring assembler:

| Relation | label | parts mine/osmium | vertices mine/osmium | geodesic km² mine/osmium | symmetric difference km² |
|---|---|---|---|---|---|
| 6080948 | Karachi Division | 1/1 | 501/501 | 5,839.94 / 5,839.94 | 0.000000 |
| 16347667 | Orangi (West) | 1/1 | 170/170 | 188.42 / 188.42 | 0.000000 |
| 16349281 | Nazimabad (Central) | 1/1 | 180/180 | 63.97 / 63.97 | 0.000000 |
| 16350242 | Gulshan (East) | 1/1 | 181/181 | 146.18 / 146.18 | 0.000000 |
| 16350632 | Korangi | 1/1 | 124/124 | 114.44 / 114.44 | 0.000000 |
| 16350836 | Karachi (South) | 1/1 | 116/116 | 116.03 / 116.03 | 0.000000 |
| 16351022 | Keamari | 1/1 | 317/317 | 2,514.09 / 2,514.09 | 0.000000 |
| 16351916 | Malir | 1/1 | 485/485 | 2,696.81 / 2,696.81 | 0.000000 |

```
max geodesic relative difference : 0.000e+00
max symmetric difference         : 0.000000 km2
all bounds identical             : True
all vertex counts identical      : True
osmium reported geometry errors  : []
```

Osmium's own multipolygon assembler reported **no geometry errors** for any of the eight, and
`osmium fileinfo` independently confirms 501 nodes / 18 ways / 8 relations and a bounding box of
(66.2862312, 24.4273517, 67.5827753, 25.676796), matching my computed bounds to seven decimals.
**The custom importer is therefore corroborated by an independent implementation, and no source
geometry was repaired.**

Useful provenance from the same payload: OSM object timestamps range **2009-12-07T16:52:29Z to
2026-10-12T23:44:18Z**, so the boundary geometry's last edit predates this assessment by about six
weeks.

Two tool-usage errors were found and fixed on the way, and are worth recording so they are not
repeated: `osmium export` has no `osm_id` attribute (the valid list differs), and without
`--geometry-types polygon` it emits the boundary as a **LineString** plus stray points, which would
have looked like a failure of my geometry rather than of my flags.

## Step 4 — GDAL clipping benchmark: **measured, replaces the earlier extrapolation**

`benchmark_gdal_clip.py` ran real `gdal.VectorTranslate` operations against the COD-AB shapefiles
with clip box `66.20 24.30 67.70 25.80` (verified: ring area exactly 2.25 deg², centroid
66.95 E 25.05 N):

| Run | Seconds | Features kept | Area deg² | Output KB |
|---|---|---|---|---|
| admin2 `-clipSrc` WKT → ext4 | 0.178 | 11/160 | 1.3533 | 97 |
| admin2 `-spatFilter` bbox only → ext4 | 0.140 | 11/160 | **8.3838** | 235 |
| admin2 `-clipSrc` WKT → `D:` 9p | 0.220 | 11/160 | 1.3533 | 97 |
| admin3 `-clipSrc` WKT → ext4 | 0.452 | 33/577 | 1.3533 | 199 |

Two findings that matter for the real run:

1. **`-spat` vs `-clipSrc` is not visible in feature counts** — both returned the same 11 features —
   but `-spat` retained **8.3838 deg² against 1.3533 deg²**, i.e. it kept the entire uncut polygons
   including landmass far outside Karachi. D-028's decision to clip rather than filter is now
   measured, not merely argued. Areas are reported in **deg² here deliberately**; they are not
   square kilometres and must not be read as such.
2. **The 9p penalty is workload-dependent.** For this CPU-bound clip, `D:` was only **1.24× slower**
   (0.220 s vs 0.178 s), whereas the earlier bulk file extraction measured **2.8× slower**. So the
   "extract in ext4" advice is justified by I/O-heavy steps, not by geometry work, and the two
   figures should not be conflated.

Three GDAL/Osmium API mistakes were caught by running the code rather than assuming it:
`-quiet` is `--quiet`, `clipsrc` is `clipSrc`, `spatialFilter` is `spatFilter`, and
`osmium derive-tags` does not exist in 1.19.

## Disk and capacity, re-measured

`C:` free fell from 25 GB to **23 GB (91% used)** across this work, and the WSL directory holds 13 GB.
`D:` remains at 133 GB free. The WSL filesystem reports 945 GB virtual. The ~2.93 GB projected
OSMData extraction is still comfortably inside `C:` headroom, but the trend is downward, so the
plan re-checks `C:` immediately before downloading and deletes the extraction afterwards.

## Where this leaves M1.5

Steps 1-4 are complete and passed. **Step 5, the land/water decomposition, has not begun** and
tests 09-12 remain skipped. The administrative geometry is now independently verified; what is
still missing is the terrestrial mask, the Manghopir government notification, and the ~249 km²
Malir coverage difference.

---

# M1.5 step 5 — land and water decomposition: MEASURED

Executed 2026-11-22. Artifacts: `osmdata_download_manifest.json`, `land_water_m15.json`,
`district_measurements_m15.csv`, `boundary_land_water_m15.png`, and scripts
`fetch_coastline_archives.sh`, `analyze_land_water_m15.py`, `render_land_water_m15.py`,
`verify_archives.py`.

## A — downloads verified twice

| Archive | Bytes | Expected | SHA-256 | Duration | Throughput |
|---|---|---|---|---|---|
| `land-polygons-split-4326.zip` | 930,863,091 | match | `e43bb195…05c6d` | 291 s | 3.20 MB/s |
| `water-polygons-split-4326.zip` | 908,939,540 | match | `e541274f…3fdd9b` | 294 s | 3.09 MB/s |

Checksums were recomputed from disk **after all extraction and clipping** by
`verify_archives.py`, not only at download time: both still match, `RESULT: ALL ARCHIVES VERIFIED`.
`zipfile.testzip()` reported no corrupt members; 6 entries each.

## B/C — source inspection and measured extraction

| Layer | Features | Geometry | CRS | Sampled validity |
|---|---|---|---|---|
| `land_polygons` | **876,241** | Polygon | EPSG:4326 geographic | 2,000 scanned, 0 invalid, 0 empty |
| `water_polygons` | **53,330** | Polygon | EPSG:4326 geographic | 2,000 scanned, 0 invalid, 0 empty |

Validity on the source layers is a **declared 2,000-feature sample**, not a full census — a
complete scan of 876k polygons was not proportionate here. The clipped layers used for every
measurement **were** fully censused (below).

Extraction into ext4, measured: land 1,347,551,580 B in 28.5 s (47.2 MB/s, ratio 1.448×); water
1,283,557,503 B in 26.2 s (49.0 MB/s, ratio 1.412×). Total **2.631 GB actual** against my earlier
2.93 GB extrapolation, which over-predicted by about 10%.

## D — clipping with `clipSrc`, never `spatFilter`

| Layer | Kept | Source features | Seconds | Output |
|---|---|---|---|---|
| land | 97 | 876,241 | 2.42 | 499,250 B |
| water | 5 | 53,330 | **103.55** | 491,666 B |

The 43× time difference despite 16× fewer features is explained by geometry complexity: the water
layer contains a handful of very large ocean polygons, so cost tracks vertex count, not feature
count. Recorded so future runtimes are not estimated from feature numbers.

Full-census geometry quality on the clipped layers: land 93 polygons after union — **0 empty,
0 invalid before repair, 0 invalid after, 0 duplicates, 0 overlapping pairs**; water 1 polygon with
the same clean result. Nothing needed repair, and no source geometry was modified.

## E — the district table you required

All areas measured with pyproj geodesic on EPSG:4326 rings; EPSG:32642 planar retained as a
cross-check. Definitions are recorded verbatim in `land_water_m15.json`.

| District | Administrative | Land | Mapped water | Overlap | Unclassified | Government | Land vs gov |
|---|---|---|---|---|---|---|---|
| Central | 63.97 | 63.97 | 0.00 | 0.0000 | 0.00 | 69 | −7.29% |
| East | 146.18 | 146.18 | 0.00 | 0.0000 | 0.00 | 139 | +5.16% |
| South | 116.03 | 85.25 | 30.77 | 0.0000 | 0.00 | 122 | −30.12% |
| West | 188.42 | 188.42 | 0.00 | 0.0000 | 0.00 | 370 | **−49.08%** |
| Keamari | 2,514.09 | **445.78** | **2,068.31** | 0.0000 | 0.00 | 559 | −20.25% |
| Korangi | 114.44 | 101.47 | 12.97 | 0.0000 | 0.00 | 108 | −6.04% |
| Malir | 2,696.81 | 2,643.16 | 53.66 | 0.0000 | 0.00 | 2,160 | **+22.37%** |
| **Division** | **5,839.94** | **3,674.23** | **2,165.71** | **0.0000** | **0.00** | **3,527** | **+4.17%** |

**The headline result: the terrestrial area inside the preserved administrative boundary is
3,674.23 km², only +4.17% above the 3,527 km² government reference.** The +65.58% of the full
polygon is now accounted for as 2,165.71 km² of mapped water, overwhelmingly the Keamari sea wedge.

## F — validation

- **Conservation residual: max 0.000001 km² across all seven districts**, and `unclassified = 0.00`
  everywhere. Land ∪ water tiles the administrative polygon completely.
  Important honesty note: this identity **holds by construction**, because `unclassified` is
  *defined* as the area inside the district but in neither layer. The residual therefore validates
  arithmetic and implementation consistency, **not** geographic correctness. Stated so it cannot be
  mistaken for independent proof.
- **Land/water overlap measured at 0.0000 km² for every district** — measured, not assumed.
- **District partition**: parent-vs-district symmetric difference 0 km²; **no pairwise district
  overlaps** detected.
- **Keamari maritime wedge quantified**: 2,514.09 km² administrative, of which only **445.78 km²
  is land**; 2,068.31 km² is mapped water.
- **Spatial coverage probes**: Saddar (67.04, 24.90) inside land ✓; open Arabian Sea (66.85, 24.55)
  correctly *not* land ✓; Korangi coast (67.10, 24.83) inside land ✓.
- **Acceptance suite: 14 tests, 14 PASS, 0 FAIL, 0 SKIP, exit 0.** Tests 09-12 are now real
  measurements rather than blocked placeholders.

## Unclassified is not a category here, and water is not assumed to be sea

The OSMData `water_polygons` layer evidently includes **marine** polygons, not only inland water —
which is why unclassified comes out exactly zero. I therefore do not report "ocean" as a measured
class. The 2,165.71 km² is "mapped water per OSMData", and the visual evidence in
`boundary_land_water_m15.png` shows it following a realistic coastline with harbour creeks and
islands, but the classification remains OSM-derived, not an independent survey.

## Residual discrepancies, unchanged and still open

Land-only areas still disagree with the government figures district by district, and clipping did
not fix that:

- **West −49.08% on land** — entirely inland, the Manghopir definitional issue, still unresolved
  pending the government notification.
- **Malir +22.37% on land** — inland over-extension, plus the 249.17 km² COD-AB coverage difference.
- **South −30.12% and Keamari −20.25% on land** — partly explained by harbour water being counted
  in the government figures, but not reconciled; the government district areas are not stated as
  land-only, so this comparison is not apples-to-apples and is recorded as indicative only.

## Storage, monitored as required

`C:` free: 24.780 → 24.012 (after land extraction) → **20.242 GB (peak usage)** → **23.004 GB after
cleanup**. `/tmp` verified empty and `/tmp/osmdata_extract` confirmed deleted only after validation
passed. `D:` 140.802 GB free. Retained: archives 1.84 GB, clipped layers ~1 MB, GeoJSON 1.7 MB.

## Position for M1.6

The geographical foundation is now measured end to end: administrative extent preserved and
unmodified, land and water classified with zero unclassified area and zero overlap, partition
topology exact, CRS validated, provenance and checksums recorded, and every geometry independently
reproduced by Osmium. **Remaining open items are administrative, not geometric**: Manghopir's
342 km² basis, Malir's inland extent, and the 249.17 km² COD-AB coverage difference. M1.6 sign-off
is yours to decide; I have not started M2 and no boundary was altered.

