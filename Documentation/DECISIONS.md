# Decisions

Format: date, decision, options considered, rationale, consequences.

## D-001 (2026-11-21) Working repository moves to D:\Karachi-Game

Options: stay on the Google Drive volume `I:\`; split repo on `I:` with data on `D:`; move to `D:`.
Rationale: WSL cannot mount `I:` at all (`wsl` emits "Failed to translate 'I:\My Drive\GTA Karachi'"),
`I:` has ~23.8 GiB free and Google DriveFS conflicts with Godot's rewritten `.godot` cache. `D:`
gives ~133 GiB and appears as `/mnt/d`.
Consequences: copied byte-for-byte, original left intact as backup, Git initialized. Every future
path uses `D:\Karachi-Game` or `/mnt/d/Karachi-Game`.

## D-002 (2026-11-21) AGENTS.md governs: true 1:1 geography

Options: AGENTS.md 1:1 realism; PROJECT_PLAN.md fictionalized with compressed distances; hybrid.
Rationale: project owner chose AGENTS.md explicitly when the conflict was surfaced.
Consequences: 1 metre = 1 Godot unit; real road and footprint geometry; no invented layouts.
`docs/PROJECT_PLAN.md` still contains the older fictionalized wording and is now the outdated document.

## D-003 (2026-11-22) M1 boundary source roles

Options for primary geometry: OpenStreetMap; HDX COD-AB PAK; a Pakistani government polygon;
a hand-drawn envelope.
Rationale: no government body investigated publishes downloadable polygons (Commissioner = JPG,
PBS = PDFs, Board of Revenue = cadastral search, Sindh P&D = HTTP 503). OSM is the only candidate
with all 7 current districts as machine-readable `admin_level=6` relations under
`admin_level=5` relation 6080948, and it shares the OSM data family with our roads and buildings.
COD-AB is permissively licensed and nationally complete, so it becomes the independent yardstick.
Consequences: provisional primary = OSM; secondary = COD-AB; admin reference = Commissioner Office.
**Provisional, not final** — D-007 remains open. A rectangle is not used as a boundary.

## D-004 (2026-11-22) Government district names are the official reference

Options: adopt OSM post-2023 names; retain Commissioner/PBS pre-2023 names; wait for a notification.
Rationale: project owner instruction. The 2023 renaming is reported by secondary sources
(Wikipedia citing a Sindh decision, and a 2024 news item); the legally authoritative notification
text has not been obtained.
Consequences: canonical names are Central, East, South, West, Korangi, Malir, Keamari. OSM names
(Orangi, Nazimabad, Gulshan, Karachi) are stored as community-mapped aliases with an explicit
alias-to-official mapping in `GIS/reports/boundary-metadata.yml`. Renaming later is a data
migration, not a rediscovery.

## D-005 (2026-11-22) Three subdivision tiers exist and must never be conflated

Evidence: Commissioner Office = **31 subdivisions**; OSM `admin_level=7` = **21 Town units**;
COD-AB `admin3` = **18 Town units**.
Rationale: these are different administrative concepts from different eras, not competing counts
of one thing. An earlier M1 report compared them as if they were and thereby wrongly rejected the
31 figure.
Consequences: any pipeline field for the sub-district tier must record which tier it holds.
Do not derive a subdivision count by counting another source's towns.

## D-006 (2026-11-22) Interim area method is acceptable only because it is calibrated

Options: wait for pyproj/GDAL; or compute areas in pure Python now.
Rationale: a Chamberlain-Duquette geodesic integral on the WGS 84 authalic sphere was tested
against COD-AB's own published `area_sqkm` for all 6 Karachi districts and reproduced them with
0.210% mean absolute error (max 0.212%), so the implementation is measurably correct at this scale.
Consequences: interim figures in the validation report carry a 0.21% method uncertainty and are
labelled interim. **They must be superseded** by an EPSG:32642 computation through pyproj before
any boundary is used for chunking, because the locked coordinate rule is metre-based projection.

## D-007 (2026-11-22) OPEN — OSM division outline is not yet fit for clipping

Evidence: computed OSM division area 5,852.38 km² against the 3,527 km² reference, **+65.93%**.
**Superseded by D-011: the properly measured value is 5,839.94 km² geodesic, +65.63%. The
conclusion that the outline is far too large stands; the number and its provenance changed.**
The 7 OSM district areas sum to exactly the division outline (no area leak), so the error is in the
outline itself, not in the dissolve. Dominated by Keamari District at 2,519.64 km² versus the
published 559 km², with Malir at 2,702.37 versus 2,160. COD-AB overshoots by only +9.35%.
Hypothesis, unconfirmed: OSM district boundaries extend into the Arabian Sea and inland beyond the
administrative limit, so the polygon encloses maritime and non-Karachi area.
Options: adopt COD-AB despite missing Keamari; use OSM but intersect it with the coastline;
use OSM land-only by clipping to the natural coast; hand-correct; or escalate to obtain an
authoritative polygon.
Consequence: **no full Karachi extraction may proceed on this polygon until resolved.** The
3,527 km² reference is not a usable pass criterion until the marine-versus-land split is measured.

## D-008 (2026-11-22) Corrected OSM acquisition route is mandatory

Evidence: `relation/6080948/full` returned 501 nodes / 18 ways / 8 relations and did not expand the
child districts' member ways, so district geometry was absent from the single-call route.
Consequences: acquisition is 8 requests (division + each of 7 districts). Any future refresh must
repeat all 8 and re-verify element counts, not just the division.

## D-009 (2026-11-22) apt toolchain install cannot be automated by the agent

Evidence: `sudo -n true` in WSL returns "interactive authentication is required".
Consequences: step A of M1 execution authorization requires the project owner to run the install
interactively. Validation tests needing GDAL, pyproj, shapely and osmium stay blocked until then.

## D-010 (2026-11-22) shapely and pyproj installed into a venv as a documented deviation

Options: stall M1.5 until the owner runs the apt install; or install the two libraries from
official manylinux cp314 wheels into `D:\Karachi-Game\.venv-gis`.
Rationale: Tasks 3, 5 and 6 need only shapely and pyproj, and both have cp314 manylinux x86_64
wheels. GDAL and fiona have none, and osmium-tool and gdal-bin genuinely require apt, so they
remain absent. The venv is 218 MB on D:, not on C:, and is removed by deleting one directory.
Consequences: M1.5 results were produced with real libraries rather than improvised code. This is a
deviation from the approved apt method and from the project's apt-over-pip preference, flagged for
owner awareness. When the apt install happens the venv should be retired so one toolchain exists.

## D-011 (2026-11-22) OSM geometry is complete; the area discrepancy is real

Evidence: all 8 payloads have zero missing way, node and relation references; every outer-way set
forms exactly one connected closed ring; `is_valid` is True for all 8. Two independent area methods
(pyproj geodesic, and planar area after reprojection to EPSG:32642) agree within 0.051% on every
unit, and the same libraries reproduce COD-AB's own published `area_sqkm` values to about 0.01%.
Consequences: the suspicion that 5,852 km² was an artifact of an incomplete download is
**disproven**. The measured division area is **5,839.94 km² geodesic / 5,841.13 km² planar**,
**+65.63%** over the 3,527 km² reference. This replaces the interim 5,852.38 figure everywhere.

## D-012 (2026-11-22) Parent and child geometries are spatially identical, not just equal-area

Evidence: `symmetric_difference(division, union(7 districts))` returns an **empty geometry,
0.000 km²**.
Rationale: the project owner required this specific test because equal total area does not prove
spatial equivalence.
Consequences: the OSM hierarchy is internally consistent. The extent error lives in the outline, so
it cannot be fixed by re-dissolving districts and no overlap or gap repair is needed.

## D-013 (2026-11-22) EPSG:32642 is confirmed fit for the 1:1 scale decision

Evidence: local scale factor measured over a true 1 km geodesic baseline at seven points across
Karachi gives **k = 0.99994 to 1.000211**, worst case about +211 ppm, roughly 21 cm per kilometre,
with NS and EW agreeing within ~2 ppm and distortion rising westward away from the 69°E central
meridian exactly as transverse Mercator predicts.
Consequences: the locked CRS decision stands and no change is proposed. The M0 estimate of
30-40 cm/km was pessimistic and is superseded by this measurement.

## D-014 (2026-11-22) OPEN — the maritime explanation is evidenced but not measured

Evidence: Keamari measures 2,514.09 km² against a published 559 km² and its seaward edge is drawn
as long straight segments including a ~40 km diagonal, visible in
`GIS/reports/boundary_comparison_m15.png`; the division bbox reaches 66.286 E and 24.427 N, tens of
kilometres offshore. But Malir's +24.85% excess is **inland**, its polygon narrowing north to
25.677 N, and West is **−49%**, so the discrepancy is not one phenomenon.
Also relevant: OSM has **zero inner rings at every level**, so no holes are modelled, while COD-AB
has 12 parts for Malir and 2 for South. COD-AB places the harbour and offshore water inside South
Karachi (507.62 km² against a published 122 km²) whereas OSM places comparable water in Keamari, so
the two datasets assign the sea to different parents.
Consequences: **Task 4 land and water decomposition is incomplete and no land or water figure is
published.** Natural Earth's documented download URL returns HTTP 500 on HEAD and on ranged GET,
and without gdal-bin or osmium-tool no alternative coastline product could be obtained or
converted. Hand-closing a land polygon from open coastline lines was rejected as producing an
unvalidated number. **M2 extraction must not proceed on this polygon.**

## D-015 (2026-11-22) Boundary not approved at M1.5

Decision: not signed off. Met: 7 districts, valid topology, complete geometry, geometric
parent-child identity, traceable provenance, CRS validated. Not met: documented coastal treatment,
correct district coverage, and area agreement with the reference.
Next gate: M1.6 requires the land and water measurement plus a decision on whether the game world
clips to the administrative extent including sea, or to the coastline.

## D-016 (2026-11-22) Four-layer geographical architecture, administrative extent preserved

Project owner decision, adopted as the model for all later milestones:

| Layer | Content | Source | Rule |
|---|---|---|---|
| L1 Administrative | division + 7 districts | OSM relation 6080948 | **full extent preserved, maritime included, never truncated at the coast** |
| L2 Terrestrial land mask | actual land | OSMData land polygons | drives terrain and road placement |
| L3 Water mask | sea, harbour, creeks, inland water | OSMData water polygons + separate inland water | drives water surfaces |
| L4 Playable world | Godot terrain, roads, buildings, vehicles, simulation | L1-L3 plus authored art | land collides, water is a surface, **the player cannot drive on the sea** |

Rationale: administrative coverage and terrestrial gameplay coverage are different concepts.
Clipping the source map to the coastline in order to simplify terrain generation would discard
geographical information.
Consequences: chunk indexing and world bounds are computed on L1 including sea; L2 decides what
becomes drivable ground; boats and maritime gameplay are possible later features, not now.

## D-017 (2026-11-22) The area discrepancy is explained and quantified

Evidence: of the OSM division's 5,839.94 km², **3,718.83 km² lies inside COD-AB's Sindh province
polygon and 2,121.11 km² lies outside it**, bounding box 66.2862-67.4498 E, 24.4274-25.6070 N. The
excess over the 3,527 km² reference is 2,312.94 km², so **91.7% of the excess is area that not even
the provincial polygon claims** - open Arabian Sea.
Per district the excess splits into three unrelated causes: Keamari 2,043.59 km² offshore, South
39.67 and Korangi 8.55 km² offshore; Malir 160.46 km² of **inland** area that COD-AB assigns to
another district; and West 188.42 km² against a published 370 km² with **zero** offshore component.
Consequences: "the sea" alone was never the answer and D-014's caution was correct. **West/Orangi
remains unexplained** and is the priority investigation, because it is a land discrepancy and the
most likely place for a genuine administrative-geometry defect. No boundary correction is made on an
unverified hypothesis.

## D-018 (2026-11-22) Coastline source is OSMData land and water polygons; Natural Earth is coarse-only

Measured before download: `land-polygons-split-4326.zip` 930,863,091 bytes and
`water-polygons-split-4326.zip` 908,939,540 bytes, both last modified 2026-11-22, total **1.71 GiB
compressed**. `land-polygons-simple-4326.zip` and `simplified-land-polygons-complete-4326.zip`
return 404. Licensing follows ODbL. The site warns, verbatim: **"Some errors in the OSM data are
repaired."** and **"If the OSM data can't be repaired automatically, the data here will not be
updated."**
Rationale: OSM-derived coastline is the same data family as our roads and buildings and is far more
detailed than a 1:10,000,000 generalised product. Natural Earth is retained only as a broad sanity
check.
Consequences: **no land or water area is published for any district yet.** The download is deferred
until `gdal-bin` exists, because `ogr2ogr -clipsrc` is the correct way to extract the Karachi subset
and processing 1.71 GiB of global polygons without it is not defensible. Every land/water figure
must carry the limitation that this is OSM-derived, possibly stale where repair failed, and not an
independent measurement of the real shoreline.

## D-019 (2026-11-22) Mapped coastline is not a legal boundary

OSM's `natural=coastline` convention is understood to follow **mean high water springs**, so a
mapped coastline is not a timeless, legally surveyed property boundary. Recorded at the owner's
instruction.
Consequences: no land/water measurement from this source may be described as a legal boundary; the
coastline in the game is a physical and gameplay approximation.

## D-020 (2026-11-22) Two agent hypotheses disproven by their own tests

The `_em` layers in the COD-AB archive were guessed to carry maritime area. They do not: `_em` is
uniformly **smaller** nationwide by 1,317.61 km² at every level, so it is a different treatment of
excluded or disputed areas. COD-AB Sindh was then guessed to be usable as a land mask. It is not:
its bounding box reaches 66.5961 E, offshore.
Consequences: both are recorded as disproven rather than quietly dropped. Positive finding from the
same work: **COD-AB sums to 876,134.13 km² identically at admin0, admin1, admin2 and admin3**, so
the secondary source is a gap-free and overlap-free partition of itself, and Sindh measures
141,028.20 km² against its own published 141,028.29 km², agreeing to 0.006%.

## D-021 (2026-11-22) M1.5 acceptance tests: 8 pass, 0 fail, 4 blocked

`Tools/osm_importer/test_boundary_m15.py` exits 0. Passing: seven districts; 31 subdivisions with
areas summing to 3,527.00; zero missing member references; all geometries valid; parent-child
symmetric difference empty; extent decomposition consistent; COD-AB partition consistency; geodesic
versus EPSG:32642 agreement to 0.0511%. Skipped with the reason printed, not faked: land-water
overlap, unclassified area, land-only area by district, and land-water spatial coverage.
Consequences: the venv remains the active toolchain and is **not retired**, because system Python
still cannot import gdal, pyproj or shapely and `sudo` still requires interactive authentication.
After the apt install, these same tests must run under system Python to prove reproducibility.
Also recorded: 260.94 km² of Karachi area is inside COD-AB's union but outside OSM's seven
districts, and must not be lost at sign-off.

## D-022 (2026-11-22) OPEN — West/Manghopir is an unresolved administrative reconciliation issue

Evidence: OSM West (relation 16347667) is the exact union of its three mapped towns, symmetric
difference **0.000000 km²**. Town areas 6.28, 35.79 and 146.35 km² against government subdivisions
Orangi Town 9.00, Mominabad 19.00 and Mango Pir 342.00 km² give deltas −2.72, +16.79 and
**−195.65**, summing to exactly the −181.58 km² district deficit.
Findings: the whole anomaly is one subdivision, Manghopir. OSM's Manghopir Town is fully inside
both the division and COD-AB Sindh, and the division's north edge (25.6768 N) lies far beyond it
(25.1046 N), so the missing land is not unassigned space inside Karachi Division.

**Status: unresolved. No district boundary modified, and none proposed.**
A definitional difference in what the government Mango Pir subdivision statistics cover is a
**plausible explanation, not a proven one** - an earlier version of this record stated it as though
settled, and that was an overclaim. Neither vector dataset supports 342 km² for that area (OSM
Manghopir 146.35 km²; COD-AB's entire West district is only 241.77 km²). The evidence still missing
is the **underlying government boundary or notification identifying what territory the 342 km²
figure covers**. Until that is obtained, the 195.65 km² difference remains an open administrative
reconciliation issue and must not be presented as explained.

## D-023 (2026-11-22) The +65.6% headline is dominated by sea; land-side extent agrees to 5.44%

Evidence: OSM division intersected with COD-AB Sindh = **3,718.83 km²**, which is **+5.44%** against
the 3,527 km² reference, versus +65.58% for the whole polygon. COD-AB's own Karachi union is
+9.12%.
Consequences: the administrative boundary is not broadly defective on land, which supports D-016's
decision to preserve the full administrative extent and derive a separate terrestrial mask instead
of treating the polygon as broken. **3,718.83 km² is explicitly not a land area** - it still contains
harbour, creek and marsh water inside Sindh - so the true terrestrial figure is lower and stays
unmeasured until the coastline masks are processed.
**Role of this figure: an independent geographical comparison only.** It is a provincial-boundary
intersection and must not be used as, or reported as, the final game terrain area.

## D-024 (2026-11-22) OSM Karachi Division excludes about 249 km² that COD-AB counts as Karachi

Evidence: all 260.94 km² of COD-AB Karachi area uncovered by any OSM district lies **outside the OSM
division outline**, with an inside-division component of 0.00 km² for every district. It decomposes
as Malir 249.17, West 5.95, South 5.82, and 0.00 for Central, East and Korangi. Per-district sum
reconciles exactly to the union-based 260.94 km².
Consequences: this is the second-largest genuine discrepancy after the sea and is a
boundary-definition difference to resolve at M1.6, not an internal topology hole.

## D-025 (2026-11-22) Measurement defect found and fixed in geod_area_km2

Evidence: `geod_area_km2` raised `AttributeError: 'GeometryCollection' object has no attribute
'exterior'` when intersecting geometries that touch along a boundary, which occurs in this dataset.
Fixed by decomposing any geometry into constituent polygons before measuring.
Consequences: because that function backs every published number, the full suite was re-run as a
regression check afterwards and **every previously reported value is unchanged** (5,839.94 /
5,841.13 km², symmetric difference 0.000000 km², all seven district areas, tests exit 0). The fix
added a missing case rather than altering a result. Acceptance tests are now 14: 10 pass, 0 fail,
4 skipped with named blockers, including two new ones for the uncovered-area location and the West
town union.

## D-026 (2026-11-22) Coastline download deliberately still withheld

The owner instructed that the 1.71 GiB OSMData archives must not be downloaded until GDAL is proven
and the existing validation is reproducible without the venv. Neither precondition can be met
because the apt install still requires an interactive sudo password that neither the agent nor the
owner's message can supply. **The archives were not downloaded and system-Python reproduction is
not done.** The venv remains the active toolchain.

## D-027 (2026-11-22) Correction: what the sudo test does and does not prove

An earlier statement here read as though `sudo -n true` failing proved the installation impossible.
That was wrong emphasis. **`-n` (`--non-interactive`) specifically suppresses the password prompt**,
so its failure proves only that non-interactive sudo is unavailable to the agent. It says nothing
about whether installation is possible; the owner can answer an interactive prompt in a real Ubuntu
terminal and the agent cannot.
Precise current state, re-verified with `dpkg-query -W` rather than inferred: `osmium-tool`,
`gdal-bin`, `python3-gdal`, `python3-pyproj` and `python3-shapely` all report *not installed*;
`osmium`, `ogrinfo`, `ogr2ogr` and `gdalinfo` are absent from PATH; system Python raises
`ModuleNotFoundError: No module named 'osgeo'`.
Consequences: per the Task 1 stop condition, the system-Python reproduction and the Osmium
cross-check are **not performed** and are reported as blocked, not as passed. The regression suite
stays in the repository permanently as the owner directed. Source integrity was re-verified
independently: both recorded SHA-256 values still match the files on disk, and Git is clean at
`7aee4d1`.

Attempted interactively on 2026-11-22 and observed, not assumed: `sudo apt-get update` started a
password read from `/dev/tty` and **blocked indefinitely** - a 25-second `timeout` wrapper did not
terminate it, and the process survived until killed by PID. It neither succeeded nor returned a
clean refusal, which is the concrete reason the agent cannot complete this step: there is no
channel through which to type a password. `id -nG` confirms the account `ak_brother_811` **is** a
member of the `sudo` group, so the owner's interactive route will work. After the killed attempt,
`dpkg --audit` reported nothing and the dpkg lock was free, so **no package database damage and no
half-install state were left behind**.

## D-028 (2026-11-22) Measured extraction benchmarks and the coastline processing plan

Measured, not estimated, using the COD-AB archive already on disk (25,496,398 B compressed, 60
entries, 40,550,468 B uncompressed, **ratio 1.59x**):

| Target filesystem | Extracted | Time | Throughput |
|---|---|---|---|
| `D:` via 9p drvfs (`/mnt/d`) | 40,550,468 B | 1.65 s | **24.5 MB/s** |
| WSL ext4 (distro disk) | 40,550,468 B | 0.60 s | **67.8 MB/s** |

ext4 is **2.8x faster** than the 9p Windows mount for this workload.

Plan derived from those numbers, **not yet executed**:

1. Download both archives to `GIS\source\osmdata\` on `D:` as the retained source of record:
   **1,839,802,631 B compressed (1.71 GiB)**, both `Last-Modified: 2026-11-22`, re-confirmed by
   HTTP before this plan was written. Download time is **not** estimated, because measuring it
   would require the download itself.
2. **Extract into the WSL ext4 filesystem, not `/mnt/d`**, then clip there, and copy only the small
   clipped Karachi result back to `D:`. At the measured 67.8 MB/s, ~2.93 GB of extraction is on the
   order of 45 s; at the 9p rate 24.5 MB/s it is on the order of 120 s. Both figures are
   **extrapolations from one archive** and the 2.93 GB itself is an extrapolation at the measured
   1.59x ratio, so treat them as planning magnitudes, not commitments.
3. Disk: `D:` has 133 GiB free and the WSL disk reports 945 GiB virtual, but **its backing store is
   on `C:`, measured at 24 GB free and 91% used** - down from 25 GB earlier the same day - so a
   ~3 GB extraction is safe while anything approaching tens of gigabytes inside Linux is not.
   Extraction must be deleted after clipping, and `C:` headroom must be re-checked immediately
   before the download because it is trending downward.
4. Clipping will use `ogr2ogr -clipsrc` against a documented Karachi bounding box rather than
   `-spat`, because `-spat` would pull in the entire Asia landmass polygon uncut. Clipping
   **changes geometry**, so the clip box must be recorded in the manifest and every area computed
   after clipping, never before.
5. `land-polygons` and `water-polygons` are both ODbL, and the service warns that automatic repair
   is not guaranteed and that data stops updating where repair fails. Broken rings must not be
   closed by hand.
6. Acceptance for the land/water step: for each district verify that
   `land + water + unclassified = administrative area` within a stated tolerance, instead of
   assuming the identity holds.

## D-029 (2026-11-22) System GIS installed; D-009 and D-027 blockers cleared

The owner ran the interactive install and supplied the transcript: 74 packages, 64.5 MB downloaded,
239 MB needed. Verified by `dpkg-query` and imports: osmium-tool 1.19.0-1build1 (libosmium 2.23.0),
gdal-bin and python3-gdal 3.12.2+dfsg-1build2 (GDAL 3.12.2 "Chicoutimi"), python3-pyproj 3.7.2
(PROJ 9.7.1), python3-shapely 2.1.2 (GEOS 3.14.1), python3-numpy 2.3.5.
Consequences: D-009 and the blocked portion of D-027 are closed. Steps 1 to 4 of the agreed
sequence are complete; step 5 remains gated on the OSMData download decision.

## D-030 (2026-11-22) Results are reproducible without the virtual environment, bitwise

Method: `dump_measurements.py` exported 57 full-precision values - geodesic and EPSG:32642 planar
areas for all eight OSM geometries and six COD-AB districts, exterior-ring coordinate counts, bounds
to nine decimals, symmetric differences, provincial intersections and national sums - from system
Python and from `.venv-gis`, then diffed them.
Result: **57/57 keys identical, max absolute and relative difference 0.000000e+00**, across different
library versions (shapely 2.2.0 vs 2.1.2, pyproj 3.8.0/PROJ 9.8.1 vs 3.7.2/PROJ 9.7.1, numpy 2.5.5
vs 2.3.5) with GEOS 3.14.1 common. The 14-test suite also gives 10 pass, 0 fail, 4 skip under both.
Consequences: no recorded value depends on the temporary venv, and the PROJ version difference does
not move these geodesic areas. The venv may be retired when the owner chooses, though it is retained
for now as instructed. Matching pass counts alone were deliberately not accepted as proof.

## D-031 (2026-11-22) Osmium independently reproduces all eight geometries

Method: `osmium export -f geojson --geometry-types polygon -e -n` against each cached `.full.osm`,
compared to the custom ring assembler in `validate_boundary_m15.py`.
Result: for all eight relations, parts, **vertex counts**, bounds and geodesic areas match exactly;
**max symmetric difference 0.000000 km2**; max relative area difference 0.000e+00; osmium reported
**no geometry errors** for any relation. `osmium fileinfo` independently confirms 501 nodes / 18 ways
/ 8 relations and bbox (66.2862312, 24.4273517, 67.5827753, 25.676796).
Consequences: the custom importer is corroborated by an independent implementation, which closes the
main residual risk in every area figure published so far. No source geometry was repaired.
New provenance from the same payload: OSM object timestamps span 2009-12-07T16:52:29Z to
2026-10-12T23:44:18Z, so the boundary's last edit is about six weeks before this assessment.
Recorded tool-usage traps: `osmium export` has no `osm_id` attribute, and omitting
`--geometry-types polygon` emits the boundary as a LineString plus stray points, which can be
mistaken for a geometry defect rather than a flag error.

## D-032 (2026-11-22) Clipping must use -clipSrc, measured; the 9p penalty is workload-dependent

Measured with `benchmark_gdal_clip.py` using real `gdal.VectorTranslate`, clip box
66.20 24.30 67.70 25.80 (verified ring area exactly 2.25 deg2, centroid 66.95 E 25.05 N):

| Run | s | features | area deg2 | out KB |
|---|---|---|---|---|
| admin2 -clipSrc to ext4 | 0.178 | 11/160 | 1.3533 | 97 |
| admin2 -spatFilter to ext4 | 0.140 | 11/160 | 8.3838 | 235 |
| admin2 -clipSrc to D: 9p | 0.220 | 11/160 | 1.3533 | 97 |
| admin3 -clipSrc to ext4 | 0.452 | 33/577 | 1.3533 | 199 |

Consequences: **`-spatFilter` and `-clipSrc` return identical feature counts but very different
geometry** - 8.3838 against 1.3533 deg2 - so a feature-count check cannot detect an uncut import.
Any pipeline step must verify geometry, not row counts. The earlier extrapolated extraction
throughputs stand for I/O-bound work, but this CPU-bound clip showed only a **1.24x** 9p penalty
against **2.8x** for bulk extraction, so the two must not be quoted interchangeably. Areas here are
deliberately in deg2 and are not square kilometres.
Tool-usage errors caught by execution and recorded so they are not repeated: `-quiet` is
`--quiet`, `clipsrc` is `clipSrc`, `spatialFilter` is `spatFilter`, and `osmium derive-tags` does
not exist in osmium 1.19.

## D-033 (2026-11-22) C: capacity is trending down during this work

Measured across the session: `C:` free went 25 GB to 24 GB to **23 GB at 91% used**, with the WSL
directory at 13 GB. `D:` stayed at 133 GB free.
Consequences: the projected ~2.93 GB OSMData extraction remains safe on current headroom, but the
download step must re-measure `C:` immediately beforehand rather than reusing any figure from this
document, and the extraction must be deleted after clipping.

## D-034 (2026-11-22) Land and water are measured; the terrestrial area is +4.17% not +65.6%

Measured with pyproj geodesic areas, EPSG:32642 planar retained as a cross-check, against OSMData
`land_polygons` (876,241 features) and `water_polygons` (53,330 features), both EPSG:4326, clipped
with `clipSrc` to the documented box:

| District | Administrative | Land | Mapped water | Overlap | Unclassified |
|---|---|---|---|---|---|
| Central | 63.97 | 63.97 | 0.00 | 0 | 0 |
| East | 146.18 | 146.18 | 0.00 | 0 | 0 |
| South | 116.03 | 85.25 | 30.77 | 0 | 0 |
| West | 188.42 | 188.42 | 0.00 | 0 | 0 |
| Keamari | 2,514.09 | **445.78** | **2,068.31** | 0 | 0 |
| Korangi | 114.44 | 101.47 | 12.97 | 0 | 0 |
| Malir | 2,696.81 | 2,643.16 | 53.66 | 0 | 0 |
| Division | 5,839.94 | **3,674.23** | **2,165.71** | 0 | 0 |

**The terrestrial area inside the preserved administrative boundary is 3,674.23 km², +4.17% against
the 3,527 km² reference.** The +65.58% of the full polygon is now accounted for as mapped water,
overwhelmingly the Keamari sea wedge.
Consequences: L1 stays exactly as it is. L2 land mask is what decides drivable terrain. Keamari's
maritime wedge is quantified at 2,068.31 km² of water against 445.78 km² of land.

## D-035 (2026-11-22) Zero unclassified area is a definitional result, not proof

`unclassified` is **defined** as the district area covered by neither the land nor the water layer,
so `A_T = A_L + A_W - A_Lw + A_U` holds by construction. The measured residual is at most
**0.000001 km²** per district and unclassified is 0.00 everywhere, which validates arithmetic and
implementation consistency - **not** geographic correctness. Recorded explicitly so it cannot be
cited as independent evidence.
Related: OSMData `water_polygons` clearly includes marine polygons, not only inland water, which is
why nothing falls outside both layers. Consequently **no area is reported as "ocean"**. The 2,165.71
km² is "mapped water per OSMData", OSM-derived and not an independent survey.
Land/water overlap was measured, not assumed: **0.0000 km² in every district**. Clipped-layer
geometry was fully censused: 93 land polygons and 1 water polygon, 0 empty, 0 invalid before or
after repair, 0 duplicates, 0 overlapping pairs. Nothing required repair and no source geometry was
modified.

## D-036 (2026-11-22) Runtime tracks geometry complexity, not feature count

Clipping land took 2.42 s for 97 kept features from 876,241; clipping water took **103.55 s** for 5
kept features from 53,330. The water layer holds a few very large ocean polygons, so cost follows
vertex count.
Consequences: pipeline runtime estimates must be built from geometry size, not row counts. Also
measured: extraction 47.2 and 49.0 MB/s in ext4 with actual ratios 1.448x and 1.412x, totalling
2.631 GB against the 2.93 GB extrapolation, which over-predicted by about 10%.
`C:` free during the run: 24.780 -> 24.012 -> **20.242 GB at peak** -> 23.004 GB after cleanup.
`/tmp/osmdata_extract` was deleted only after validation passed, and `/tmp` was then verified empty.
Archives were re-verified by recomputed SHA-256 **after** all processing: both match.

## D-037 (2026-11-22) Acceptance suite now 14 of 14, no skips

Tests 09-12 became real measurements instead of blocked placeholders, and three of my own bugs were
caught while enabling them: GDAL `Geometry` has no `__geo_interface__` (use `ExportToJson()`),
`VectorTranslate` has no `layerOptions` keyword, and the clipped-layer path in the test was wrong
(`land_karachi/land.shp`, not `land/land.shp`). Separately, an earlier "exit code 0" I reported was
the status of a `tr` pipe rather than the analysis process, which had in fact crashed; every
subsequent run captures the real `$?`.
Consequences: the suite is the standing regression gate for M1.6 and M2. Rendering uses GeoJSON
interchange because matplotlib exists only in the venv while GDAL exists only in system Python, so
the two environments are now deliberately decoupled at that boundary.

## D-038 (2026-11-22) Remaining M1.6 items are administrative, not geometric

Open: Manghopir's 342 km² basis, still needing the government notification, with West at −49.08%
on land; Malir's inland over-extension at +22.37% plus the 249.17 km² COD-AB coverage difference;
and South −30.12% / Keamari −20.25% on land, which are only indicative because the government
district figures are not stated as land-only and so are not directly comparable to a land mask.
Closed: extent classification, topology, CRS, provenance, reproducibility and independent geometry
verification.

## D-039 (2026-11-22) Grid tiles deliberately overlap; an earlier overlap claim was wrong

The archive READMEs state the products are "split into a grid with slight overlap", and measuring
the frozen layers confirmed it: **8 overlapping land pairs totalling 23.28 km²** (worst pair
9.89 km²) and **4 water pairs totalling 12.05 km²** (worst 6.10 km²). Raw sums exceed union areas by
exactly those amounts.
Correction: the earlier "0 overlapping pairs" was computed on `unary_union` output, so it could not
detect tile overlap. That claim is withdrawn.
Consequences: district land and water figures remain valid because every mask operation already
used the union, but the project rule is now explicit and asserted by test 15 - **consume masks as
unions, never sum features**. Recorded as L-18.

## D-040 (2026-11-22) Canonical dataset v1.0.0 frozen at M1.6

Structure: `GIS/canonical/v1.0.0/` with `layers/` (L1 division + 7 districts, L2 land, L3 water, all
EPSG:4326 GeoJSON), `manifest.json`, `metadata/l4_schema.yml`, `checksums.sha256`, `README.md` and
`KNOWN_LIMITATIONS.md`. Total 1.6 MB of geometry, committed to Git; the 1.84 GB archives stay
ignored.
Rationale: a freeze that cannot be regenerated is not a freeze, so the small derived layers are
versioned and the build is scripted and deterministic - osmium produces L1, GDAL produces L2 and L3,
features are sorted by canonical JSON and properties serialised with sorted keys.
Consequences: L4 is schema only with `E0`, `N0` and `vertical_origin_m` explicitly UNSET, so M2
cannot accidentally inherit an undefined origin. Government names are canonical and OSM names are
stored as aliases in L1 properties. Provenance records the data vintage
2026-11-21T16:00:00Z, ODbL copyright, the two publisher warnings verbatim, and the COD-AB and
Commissioner references. Nineteen limitations are registered, six of them open administrative
questions that need documents rather than more computation.

## D-041 (2026-11-22) Two process defects found while freezing the dataset

A self-referential checksum manifest: `checksums.sha256` hashed the previous build's copy of
itself, so verification failed. Fixed by excluding the manifest from its own list, because a
manifest cannot authenticate itself.
A wrong assumption about archive internals: the full rebuild looked for
`land_polygons.shp` at the extraction root, while the archives nest it inside a directory named
after the product. Fixed by discovering the path with a glob instead of hardcoding it.
Also recurring on my side: reporting an exit status taken from a `tail` in a pipeline instead of
the process that mattered, which made a failed build look successful. Every subsequent run
captures `$?` directly from the tool.

## D-042 (2026-11-22) M2.0 freezes the world origin from the administrative extent only

`E0 = 225280 m`, `N0 = 2841088 m`, both exact multiples of the 512 m chunk, derived as
`floor(min_easting/512)*512` and `ceil(max_northing/512)*512` over L1 Karachi Division only, so every
chunk index inside the division is non-negative and a tile can never be named `-1,3`. The vertical
origin is recorded as `0.0 m` with `vertical_datum` explicitly **UNSET**, because no licensed elevation
source exists and a flat number without a datum must not read like a survey.
Options considered: origin from the L2/L3 masks (rejected - the masks reach the clip box, which would
silently widen the world by 22.64 km east-west and 30.98 km north-south beyond the boundary), a
rounded kilometre origin (rejected - breaks tile alignment and makes index arithmetic lossy), and the
centroid as origin (rejected - produces negative indices in the west and south).
Consequences: `config/world_coordinates.json` is the machine-readable contract and
`Documentation/WORLD_COORDINATES.md` the human one, locked by 16 assertions. Changing `E0`/`N0` after
chunks exist is a versioned migration, not an edit. The chunk grid over the division is
257 x 269 = 69,133 tiles - an address space, not a workload.

## D-043 (2026-11-22) City-wide distortion is 496.7 ppm, not the 211 ppm previously published

The 211 ppm figure in `CRS_AND_MEASUREMENT.md` and in the frozen v1.0.0 manifest was measured at
**7 points in the built-up core**, which sits east, closer to the 69E central meridian, where
transverse Mercator distortion is smallest. Sampling the whole administrative extent at 0.05 degrees
(418 baselines over 209 points) gives **k = 0.999868 to 1.000497, worst 496.7 ppm**, about 50 cm per
kilometre, with the worst case at the western Keamari/Hub boundary as theory predicts.
This is a scope correction, not a regression: 211 ppm stays true for the core and was never a
city-wide number. Both documents now state which region each figure describes.
Consequences: EPSG:32642 remains locked - 50 cm/km is undetectable in gameplay, geodesic and planar
areas still agree to 0.0511%, and a custom central meridian at 67.05E was evaluated and rejected for
breaking the locked CRS and every UTM-native tool around OSM. Measuring the two bearings separately,
they agree to 3.26 ppm across all 209 points, confirming conformality city-wide rather than only in
the core.

## D-044 (2026-11-22) Two defects that only a real run could find, plus the repository rename

The M2.0 round-trip test hung rather than failed: it stepped projected **metres** by `0.02`, so the
loop over a 131 x 137 km extent needed millions of iterations and never reached the later assertions.
Fixed by stepping 2,000 m, which is 4,554 points and runs in about a second. A hang that hides twelve
subsequent checks is a worse failure than a wrong number, and it survived review because an earlier
"16 passed" run predated that loop.
Test 08 then crashed with `'MultiPolygon' object has no attribute 'exterior'` - it had assumed a
feature geometry is always a single polygon. Fixed with a ring walker that descends MultiPolygon and
GeometryCollection and yields interior rings as well, and that **raises on any other geometry type**
instead of silently checking nothing. It now reports the 2,074 vertices it actually examined, so a
vacuous pass is impossible.
Root folder: `D:\Karachi-Game` no longer exists because it was **renamed to `D:\Karachi Street
Stories`**, not deleted - Git history, canonical dataset, archives and venv are intact. The real
defect was mine: ten tool scripts hardcoded `/mnt/d/Karachi-Game/...`. All ten now derive the root
from their own location (nine Python via `_ROOT = Path(__file__).resolve().parents[2]`, the download
script via `ROOT="$(cd "$(dirname "$0")/../.." && pwd)"`), so the repository survives any future
rename. The three full suites (16 + 15 + 14) pass from the new path.
Consequences and open items: `AGENTS.md` still documents `D:\Karachi-Game` as the suggested root, and
line 47 of the frozen `GIS/canonical/v1.0.0/README.md` still contains the old absolute path in its
rebuild-verification snippet. Neither was edited - the first is the owner's master prompt, the second
sits inside the checksum-protected freeze - so both are recorded here as known stale text. The recipe
still works; substitute the current root.

## D-045 (2026-11-22) The GitHub remote already has an unrelated history; nothing was pushed

`https://github.com/AHK811/Karachi-Stories.git` was inspected read-only
(`git ls-remote`, then `git fetch` of `main`). It contains **2 commits**
(`79602c4` "docs: add professional game project README", `2d10061` "Delete README.md") and
`git merge-base` reports **no common ancestry** with local `main`, which has the M0-M2.0 history.
A dry-run push was rejected `[rejected] main -> main (non-fast-forward)`.
Options, none taken without approval: force push (erases the two remote commits - refused, it is a
destructive operation on shared state), rebase ~20 local commits onto the remote (works, but
rewrites local history for a README add/delete that carries no content), merge unrelated histories
(`--allow-unrelated-histories`, keeps both), or push to a side branch and decide in the GitHub UI.
Recommendation: push `main` to a new branch, then fast-forward `main` in the UI or delete the remote's
two empty commits first, since a public repo whose tip deletes its own README has nothing to lose.
Authentication was predicted to be a blocker, and that prediction was WRONG: I checked
`git config --global credential.helper` inside WSL, found nothing, and concluded no push could
complete. The push then worked first try, because the helper lives in the **Windows** system config
(`C:/Program Files/Git/etc/gitconfig` -> `manager`). Checking one lane and declaring the other
impossible is the same mistake as green-in-WSL-not-equals-green-on-Windows, only in reverse.
Authorship: existing commits are authored `AHK811-edu <k263018@khi.nu.edu.pk>`. Changing the email to
`ak.brothers.811@gmail.com` needs a config edit (the owner's, not mine) and, for history already
created, a rewrite - and note that pushing makes author emails public on GitHub.

Resolution (same day, owner-approved): pushed `main` to the **new branch**
`refs/heads/world-coordinates-m20` at `a1bed55`, by URL, without creating an `origin` remote and
without editing git config. Verified afterwards: remote `main` is still `2d10061`, untouched, and
`merge-base` still reports no common ancestry, so the owner can fast-forward, open a pull request, or
delete the two empty remote commits in the UI. Authorship was deliberately left as-is with the school
email, which is now publicly visible because the repository is public - the owner chose that after it
was flagged. `git credential.helper=manager` (system-wide Git for Windows) supplied the
credential; no token was read, stored or printed by this task.

Final outcome (owner then requested main, the Gmail address, and the message "Initial commit"):
`46ccd69 Initial commit` joins the two histories with `-s ours --allow-unrelated-histories`, parents
`[8d5916f, 2d10061]`, tree byte-identical to local main (`a1515b6`), authored and committed as
`ak.brothers.811@gmail.com` via per-command `-c user.email=` so **git config was still not modified**.
Because `2d10061` is a parent, pushing to `main` is a genuine fast-forward
(`2d10061..46ccd69`) - **no force push, no published commit rewritten or deleted**. Remote `main` and
local `main` are now both `46ccd69`; `world-coordinates-m20` remains at `8d5916f` as an ancestor and
can be deleted in the UI. The 14 milestone commits stay intact under the merge. Note the honest
asymmetry the owner accepted: only the import commit carries the Gmail address; the M0-M2.0 commits
keep `k263018@khi.nu.edu.pk`, which is public on GitHub.
