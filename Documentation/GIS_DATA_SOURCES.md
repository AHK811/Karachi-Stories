# GIS data sources and provenance

Project: Karachi: Street Stories. Scope of this file: administrative boundary sources for
Karachi Division, acquired during M1. Raw geometry stays out of Git (see `.gitignore`);
this file and `GIS/reports/` carry the provenance.

## Approved source roles (M1, project owner decision 2026-11-22)

| Role | Source | Basis |
|---|---|---|
| Administrative reference (names, structure, published areas) | Commissioner Office Karachi | Publishes 7 districts / 31 subdivisions / 3,527 km² |
| Primary provisional boundary geometry | OpenStreetMap relation 6080948 + 7 child district relations | Only candidate carrying all 7 current districts |
| Secondary independent validation | OCHA/HDX COD-AB PAK `pak_admin_boundaries.shp.zip` | CC BY-IGO, complete national COD product |
| **Not approved as written** | OSM export step D | Superseded: see Acquisition route below |

## 1. Commissioner Office Karachi — administrative reference

- Organisation: Office of the Commissioner, Government of Sindh.
- URL: https://commissionerkarachi.gos.pk/index.php/area-maps
- Retrieved: 2026-11-22.
- Content: 3,527 km², 7 districts, 31 subdivisions, per-district and per-subdivision areas, all enumerated. One embedded raster `images/map-1.jpg`.
- Geometry: **none**. Formats: HTML and JPG.
- Licence: **not stated on the page**.
- Limitations: undated; uses pre-2023 district names; no notification numbers given; raster map has no coordinate reference system and is not georeferenced.
- Verification performed: parsed enumeration re-summed programmatically. 31 subdivisions; district areas sum to 3,527.00; all 31 subdivision areas sum to 3,527.00; each district equals the sum of its own subdivisions. Internally consistent at both tiers.

## 2. OpenStreetMap — primary provisional boundary

- Provider: OpenStreetMap contributors. Licence: **ODbL 1.0** (confirmed in server responses).
- Division relation: `6080948`, `admin_level=5`, `boundary=administrative`, `wikidata=Q8660`, `name:en=Karachi Division`. Members: 7 relations, 18 ways, 2 nodes. All 18 ways carry role `outer`; **no `inner` roles**.
- Acquisition route, validated 2026-11-22:
  - `GET https://api.openstreetmap.org/api/0.6/relation/6080948/full` returns only 501 nodes / 18 ways / 8 relations. **It does not expand the child districts' own ways and nodes**, so it cannot produce district geometry on its own.
  - The corrected route is 8 requests: the division plus each of the 7 child districts' `full` endpoints. All 8 retrieved successfully (HTTP 200).
- Files and checksums: `GIS/reports/checksums.sha256`. Sizes: division 122,845 bytes; children 28,360 to 105,190 bytes; total 64 MB for the whole `GIS/` tree including COD-AB.
- Original CRS: EPSG:4326.
- Child districts resolved: 16347667 Orangi, 16349281 Nazimabad, 16350242 Gulshan, 16350632 Korangi, 16350836 Karachi, 16351022 Keamari, 16351916 Malir. All `admin_level=6`.
- Level 7: **21 Town units**. Different tier from the 31 government subdivisions; do not conflate.
- Limitations: community-mapped, not legally authoritative; low vertex density (501 vertices for the division outline); computed area **+65.93%** against the 3,527 km² reference.

## 3. OCHA/HDX COD-AB PAK — secondary validation

- Dataset: Pakistan - Subnational Administrative Boundaries (`cod-ab-pak`), UUID `a64d1ff2-7158-48c7-887d-6af69ce21906`.
- Publisher: OCHA Field Information Services Section (FISS), on HDX.
- Resource: `pak_admin_boundaries.shp.zip`, UUID `d2752403-3c34-4e03-8b4e-3e55500ded10`,
  URL `https://data.humdata.org/dataset/a64d1ff2-7158-48c7-887d-6af69ce21906/resource/d2752403-3c34-4e03-8b4e-3e55500ded10/download/pak_admin_boundaries.shp.zip`
- Licence: **CC BY-IGO 3.0** — http://creativecommons.org/licenses/by/3.0/igo/legalcode
- Retrieved 2026-11-22T10:04Z. HTTP `Last-Modified: Fri, 14 Aug 2026 07:22:25 GMT`.
- Size: **25,496,398 bytes**, identical to the API's declared `size` and the HTTP `Content-Length`.
- SHA-256: `04e634d5bd7f1a93d81ae993d6341daa4ed350741fe94eee9e9dce9958a46c86`
- Formats in archive: GeoDatabase, Shapefile, GeoJSON, XLSX (separate resources). No KML. **No CSV of coordinates. No `.poly`.**
- Original CRS: **read from `pak_admin2.prj`**, `GEOGCS["GCS_WGS_1984", SPHEROID["WGS_1984", 6378137.0, 298.257223563]]` = EPSG:4326. Not assumed. Attribute encoding UTF-8 from `.cpg`.
- Vintage: boundaries created 2022-09-02; valid for humanitarian use 2022-09-09; reviewed 2024-09-27; metadata modified 2026-08-14; `version=v01`; single `valid_on=20220909` across all admin2 rows.
- Record counts verified from the binary: admin1 7, admin2 160 geometry records / 160 DBF rows, admin3 577 / 577. Matches the dataset's own stated 7 / 160 / 577.
- Karachi content: **6 districts only** — PK702 Central Karachi (65.14 km², 262 vertices), PK704 East Karachi (202.92, 426), PK712 Korangi Karachi (104.29, 221), PK714 Malir Karachi (2,726.86, 12 parts, 1,224), PK721 South Karachi (507.63, 2 parts, 353), PK729 West Karachi (241.77, 328). Published sum 3,848.61 km².
- **Keamari is absent as a district.** It exists only as `Kemari Town` (PK72101), an admin3 unit inside South Karachi, 410.91 km².
- Post-2023 names (Gulshan, Nazimabad, Orangi) do not appear at admin2.
- admin3 under the 6 Karachi districts: **18 Town units** — a third distinct tier again.

## 4. Sources investigated and rejected or unavailable

| Source | Outcome |
|---|---|
| Sindh Planning & Development Board GIS, https://pnd.gos.pk/gis-map | **HTTP 503** on 2026-11-22. Cannot confirm or rule out a WMS/WFS. Re-attempt later |
| PBS GIS, https://www.pbs.gov.pk/gis/ | **No vector data.** PDFs only: `Administrative Units 2023.pdf`, `Delimitation Plan 2023.pdf`. No licence terms stated. PDF text extraction failed (corrupted stream) — content still unexamined |
| Board of Revenue Sindh, https://sindhzameen.gos.pk/ | Land-record and property search with "Deh Maps". **No downloadable GIS dataset, no API, no OGC service listed.** Cadastral, not administrative boundaries |
| KDA town maps, https://www.kda.gos.pk/contents/?id=94 | Town/district map pages; not investigated as a polygon source; KDA is a planning authority, not the boundary owner |
| Local Government Dept Sindh, `lgdsindh.gov.pk/downloads/UCsKarachi.pdf` | Union Committee name notification; explicitly excludes West and Keamari districts. Useful for the UC tier, not for division geometry |
| SimpleMaps Pakistan, osm-derived repackagers | Rejected: derived products with unstated upstream geometry provenance; unsuitable as an authoritative boundary |
| Google/proprietary imagery | Forbidden by AGENTS.md |

## 5. Corrections to earlier statements in this project's records

- The HDX SHP resource was first reported at 12.7 MB from an HDX page snippet. **The API and
  HTTP headers both say 25,496,398 bytes; the download matches exactly.** The 12.7 MB figure is wrong.
- An earlier M1 report rejected the "31 subdivisions" figure using OSM's 21 level-7 towns and
  the Sindh portal's 42-item list. **That rejection was wrong.** The Commissioner Office publishes
  exactly 31 subdivisions and the enumeration is internally consistent. 31 is accepted.
- `pak_admin2.dbf` was first mis-read as 865 records. That was the header-length field, not the
  record count. **Correct value: 160 records.**

## 6. M1.5 addendum — toolchain and coastline source status

Validation toolchain actually used, current as of the M1.5 third continuation:

| Component | Version | Install route | Status |
|---|---|---|---|
| osmium-tool | 1.19.0-1build1 (libosmium 2.23.0) | `sudo apt install` by the owner | **installed** |
| gdal-bin / python3-gdal | 3.12.2+dfsg-1build2 (GDAL 3.12.2 "Chicoutimi") | same | **installed** |
| python3-pyproj | 3.7.2 (PROJ 9.7.1) | same | **installed** |
| python3-shapely | 2.1.2 (GEOS 3.14.1) | same | **installed** |
| python3-numpy | 2.3.5 | apt dependency | installed |
| venv `.venv-gis` | shapely 2.2.0, pyproj 3.8.0 (PROJ 9.8.1), numpy 2.5.5, matplotlib 3.11.2, pyyaml | pip wheels on D: | retained, not retired |

Reproducibility between the two was proven numerically rather than by pass counts: 57
full-precision measurements exported from each interpreter diffed to **zero difference on every
value**, and the 14-test suite gives 10 pass / 0 fail / 4 skip under both. Osmium's own
multipolygon assembler reproduces all eight geometries with identical vertex counts, bounds and
areas, symmetric difference 0.000000 km², and reports no geometry errors.

Coastline and land/water mask source — **OSMData, downloaded, verified and measured on 2026-11-22**:

| Product | Bytes | SHA-256 | Download | Throughput |
|---|---|---|---|---|
| `land-polygons-split-4326.zip` | 930,863,091 | `e43bb195ee646f27edcf38c2a50ce14ae39e0ab64e7ef9964b430dad1e605c6d` | 291 s | 3.20 MB/s |
| `water-polygons-split-4326.zip` | 908,939,540 | `e541274f78a83564f19db62f4aad3258a43d15041659b825e7b7d61ac83fdd9b` | 294 s | 3.09 MB/s |

- URLs: `https://osmdata.openstreetmap.de/download/land-polygons-split-4326.zip` and
  `.../water-polygons-split-4326.zip`. Both `Last-Modified: Sun, 22 Nov 2026` at retrieval.
- Stored in `GIS\source\osmdata\`, git-ignored. `zipfile.testzip()` clean, 6 entries each.
  `verify_archives.py` recomputes both hashes from disk **after** processing; both matched.
- Layer contents: `land_polygons` **876,241** Polygon features, `water_polygons` **53,330** Polygon
  features, both **EPSG:4326** geographic. A declared 2,000-feature validity sample on each showed
  0 invalid and 0 empty; the clipped layers actually used were fully censused with the same result.
- Extraction measured: land 1,347,551,580 B in 28.5 s (47.2 MB/s, 1.448×); water 1,283,557,503 B in
  26.2 s (49.0 MB/s, 1.412×). Total 2.631 GB actual versus 2.93 GB extrapolated.
- Clipped to `66.20 24.30 67.70 25.80` with GDAL `clipSrc` (never `spatFilter`) into
  `GIS\processed\osmdata\` as shapefiles plus GeoJSON interchange, ~1 MB each. Land kept 97
  features in 2.42 s; water kept 5 features in 103.55 s, because cost follows vertex count.
- Licence **ODbL**, with the service's own warnings retained verbatim: **"Some errors in the OSM
  data are repaired."** and **"If the OSM data can't be repaired automatically, the data here will
  not be updated."**
- Interpretation limits that must travel with any reuse: this is **OSM-derived** geometry, not an
  independent measurement of the shoreline; `water_polygons` includes marine polygons, so areas are
  reported as "mapped water" and **never as measured "ocean"**; OSM `natural=coastline` is
  understood to follow mean high water springs, so no coastline here is a legally surveyed boundary.
- Natural Earth 10m land remains **unavailable** (HTTP 500 on HEAD and three ranged GETs while the
  site root returns 200) and is in any case only a coarse 1:10,000,000 sanity check, never the
  production shoreline.

Derived measurements, all reproducible from the retained archives plus the committed scripts:
`GIS/validation/land_water_m15.json` and `district_measurements_m15.csv`. Division total
5,839.94 km² = land **3,674.23** + mapped water **2,165.71**, overlap 0.00, unclassified 0.00.
Keamari is 445.78 km² of land within 2,514.09 km² of administrative area.

Scripts and outputs, all committed: `Tools/osm_importer/validate_boundary_m15.py`,
`render_boundary_m15.py`, `analyze_extent_m15.py`, `investigate_west_orangi_m15.py`,
`investigate_karachi_gaps_m15.py`, `test_boundary_m15.py`, `dump_measurements.py`,
`benchmark_gdal_clip.py`, `fetch_coastline_archives.sh`, `analyze_land_water_m15.py`,
`render_land_water_m15.py`, `verify_archives.py`;
`GIS/validation/m15_results.json`, `osmium_crosscheck.json`, `gdal_clip_benchmark.json`,
`osmdata_download_manifest.json`, `land_water_m15.json`, `district_measurements_m15.csv`;
`GIS/reports/boundary_comparison_m15.png`, `boundary_land_water_m15.png`.

Coastline or land-mask source for the land versus water split: **not obtained.**

- Natural Earth 10m land polygons, `ne_10m_land.zip`, 3.12 MB, v5.1.1. Licence is suitable — the
  site states Natural Earth is "in the public domain" and usable for "personal, educational, and
  commercial purposes", with attribution optional ("Made with Natural Earth" suggested).
- The documented URL
  `https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip`
  returned **HTTP 500** on both HEAD and a ranged GET, with an HTML error body of 2,704 bytes. No
  file was downloaded and no alternative URL was guessed.
- Consequence: **no land, water or outside-coastline area figures are recorded for any district.**
  The only defensible statement available is that OSM has zero inner rings at every level, so
  hole-contributed area is 0.00 km² for all eight geometries.

Coastline and land/water mask source selected in the M1.5 continuation — **OSMData, inspected but
not yet downloaded**:

| Product | Bytes | Last-Modified | HTTP |
|---|---|---|---|
| `land-polygons-split-4326.zip` | 930,863,091 | 2026-11-22T01:49:50Z | 200 |
| `water-polygons-split-4326.zip` | 908,939,540 | 2026-11-22T01:52:47Z | 200 |
| `land-polygons-split-3857.zip` | 954,988,788 | — | 200 |
| `land-polygons-complete-4326.zip` | 925,704,470 | — | 200 |
| `land-polygons-simple-4326.zip` | — | — | **404** |
| `simplified-land-polygons-complete-4326.zip` | — | — | **404** |

- Pages: https://osmdata.openstreetmap.de/data/land-polygons.html and `/data/water-polygons.html`.
- Produced by assembling OSM coastlines into polygons. Licensing follows **ODbL**, the same
  obligation already carried by the boundary and the future map extract.
- Stated limitations, verbatim: **"Some errors in the OSM data are repaired."** and **"If the OSM
  data can't be repaired automatically, the data here will not be updated."** This is OSM-derived
  geometry, **not an independent measurement of the actual shoreline**, and it can be stale.
- Combined size for the two selected WGS84 split products is **1.71 GiB compressed**, before
  extraction. Download is deliberately deferred until `gdal-bin` is installed, because clipping to
  the Karachi extent is a single `ogr2ogr -clipsrc` and processing global polygons without GDAL is
  not defensible. Destination when approved: `GIS\source\osmdata\`, never in Git.
- Related convention recorded: OSM `natural=coastline` is understood to follow **mean high water
  springs**, so a mapped coastline is not a legally surveyed, timeless property boundary.
- Natural Earth 10m land remains unavailable at the documented URL (HTTP 500 on HEAD and on three
  ranged GETs, while the site root returns 200) and is in any case retained only as a coarse
  1:10,000,000 sanity check, never as the production shoreline.

M1.5 continuation evidence files, all committed: `m15_test_output.txt`, `m15_extent_analysis.txt`,
`m15_environment.txt`, plus `Tools/osm_importer/analyze_extent_m15.py` and
`Tools/osm_importer/test_boundary_m15.py`.
- Note for reproducibility: `Tools/osm_importer/validate_boundary_m15.py` parses cached OSM XML
  with `xml.etree.ElementTree`, which does not harden against entity-expansion attacks. The inputs
  are files this project downloaded itself from `api.openstreetmap.org`, so this is acceptable for
  the offline compiler, but the parser should be hardened before it ever consumes untrusted XML.

## 7. Licensing and distribution obligations

- ODbL: attribute © OpenStreetMap contributors in the game and docs. Review share-alike before
  distributing adapted database extracts. **Legal review required; no guarantee implied.**
- CC BY-IGO: attribute OCHA FISS; keep COD-AB geometry in a separately-attributed layer.
- Do **not** merge ODbL and CC BY-IGO geometry into one undifferentiated file; keep per-feature provenance.
- Pakistani government sources publish no licence terms: cite for facts, do not embed their maps or derive geometry from them.
- Keep these records and source timestamps for every regenerated build.
