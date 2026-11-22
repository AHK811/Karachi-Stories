# Known limitations and unresolved discrepancies

This register is part of the frozen dataset. Nothing here was resolved by choosing a convenient
answer, and M2 must not convert any open item into a game-world fact.

## Open — administrative, needs documents not computation

| ID | Item | Measured evidence | Status |
|---|---|---|---|
| L-01 | West / Manghopir government-area basis | OSM West land 188.42 km² against government West 370.00 km², a −49.08% difference with **zero** offshore component. OSM Manghopir Town is 146.35 km² against the published "Mango Pir" 342.00 km² | **OPEN.** A definitional difference is plausible but unproven. Required evidence: the government boundary or notification defining the 342 km² figure. No geometry altered |
| L-02 | Malir inland extent | OSM Malir land 2,643.16 km² against government 2,160.00 km², +22.37%, all inland | **OPEN** |
| L-03 | Malir COD-AB coverage difference | 249.17 km² of COD-AB "Malir Karachi" lies outside the OSM division outline entirely | **OPEN.** Decide at M2 whether OSM or COD-AB governs the outer limit |
| L-04 | South and Keamari land versus government | South land 85.25 vs 122.00; Keamari land 445.78 vs 559.00 | **Non-equivalent comparison.** Government district areas are not stated as land-only, so these are indicative only and are not evidence of a defect |
| L-05 | District naming authority | Government names (Central, East, South, West, Korangi, Malir, Keamari) are official-reference. OSM carries post-2023 names (Nazimabad, Gulshan, Karachi, Orangi). The 2023 Sindh renaming is reported by secondary sources only | **OPEN** for legal confirmation. Alias mapping is stored in L1 properties |
| L-06 | Subdivision tier | 31 government subdivisions retained; OSM maps 21 level-7 towns; COD-AB maps 18 admin3 towns | Three distinct tiers, deliberately **not reconciled**. Never compare counts across tiers |

## Open — classification and data-quality limits

| ID | Limitation | Consequence |
|---|---|---|
| L-07 | L2 and L3 are **OSM-derived** classifications, not independent surveys | Coastline position is only as good as OSM mapping. Publisher warns: "Some errors in the OSM data are repaired." and "If the OSM data can't be repaired automatically, the data here will not be updated." |
| L-08 | OSM `natural=coastline` is understood to follow **mean high water springs** | The land/water line is a tidal convention, not a legally surveyed or timeless boundary |
| L-09 | L3 water includes **marine** polygons | Zero unclassified area means the two supplied classifications cover the measured extent under the chosen definitions. It does **not** mean every part of the coastline is correct, and mapped water must never be reported as measured ocean |
| L-10 | The conservation identity holds **by construction** | `unclassified` is defined as area in neither layer, so the residual of at most 0.000001 km² validates arithmetic and implementation, not geographic correctness |
| L-11 | Source-layer geometry validity is a **2,000-feature sample**, not a census | `land_polygons` has 876,241 features and `water_polygons` 53,330. Clipped layers used for all measurements were fully censused and were clean |
| L-12 | OSM has **zero inner rings** at every administrative level | Enclaves and enclosed water bodies are not modelled in L1 and are silently included in district areas |
| L-13 | COD-AB is administratively stale | 2022-09-02 vintage, has **no Keamari district**, and predates the 2023 renaming. Used as a yardstick only |
| L-14 | No elevation source licensed | `vertical_origin_m` unset; all game Y values are a documented ground-height fallback until a DEM is acquired under its own licence |
| L-15 | World origin E0 and N0 not yet frozen | Chunk indices and every metre-based coordinate are undefined until M2 fixes them and records them in each manifest |
| L-16 | Government boundary authority absent | No Pakistani government body investigated publishes a downloadable polygon: Commissioner Office is a JPG, PBS is PDFs, Board of Revenue is cadastral search, Sindh P&D returned HTTP 503 |
| L-17 | Legal position unreviewed | ODbL share-alike treatment of a distributed game versus a derivative database needs legal review. No compliance claim is made |
| L-18 | OSMData products are **grid tiles with deliberate overlap** | Measured on the frozen layers: 8 overlapping land tile pairs totalling **23.28 km²** double-counted (worst pair 9.89 km²) and 4 water pairs totalling **12.05 km²** (worst 6.10 km²). All mask arithmetic therefore consumes the **union** of each layer, never a sum of features, so district land and water figures are unaffected. An earlier statement of "0 overlapping pairs" was measured after union and could not detect this; it is corrected here |
| L-19 | Data vintage is a snapshot | Both archives state "Date of the data used is **2026-11-21T16:00:00Z**". The dataset is a point-in-time freeze, not a live service, and reproducing it later from the same archives is required before any claim of change |

## What is NOT in dispute

L1 geometry integrity and partition, independently reproduced by Osmium; CRS choice and the
measured ±211 ppm zone-42N distortion; archive provenance and checksums; reproducibility across two
Python environments; the fact that the administrative extent was never modified.
