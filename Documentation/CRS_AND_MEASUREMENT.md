# CRS and area measurement methodology

Frozen with canonical dataset v1.0.0. This is the only method that may be used to report metres or
square kilometres for this project.

## Coordinate systems

| Role | System | Rule |
|---|---|---|
| Storage and interchange | **EPSG:4326** | All canonical GeoJSON is lon/lat WGS 84, declared as GeoJSON CRS8. GeoJSON spec forbids other CRSs, so storage in 4326 is mandatory, not a choice |
| Metric measurement and game world | **EPSG:32642** (WGS 84 / UTM zone 42N) | Every metre and square-kilometre figure derived for gameplay or chunking comes from here |
| Elevation | not licensed yet | `vertical_origin_m` unset; game Y uses a documented ground-height fallback |

Zone 42N has its central meridian at 69°E. The Karachi Division administrative extent spans
66.2°–67.7°E, so it sits **132 km to 284 km west** of the meridian (1° of longitude here measures
101,378.8 m, measured at 24.5°N), and the projection is not distortion-free anywhere in it.
Measured, not assumed:

- Local scale factor over a true 1 km geodesic baseline, sampled across the **whole administrative
  extent** at 0.05° spacing, 418 samples: **k = 0.999868 to 1.000497**, mean 1.000097.
- Worst case **496.7 ppm**, about **50 cm per kilometre**. Revision (M2.0): an earlier entry here and
  in the v1.0.0 manifest reported **+211 ppm** from **7 points in the built-up core only**, which is
  the eastern, lower-distortion part of the division. 211 ppm remains correct for the core; it was
  never a city-wide figure and must not be quoted as one. See D-043.
- Distortion increases westward, away from the central meridian, exactly as transverse Mercator
  predicts.
- Conformality check on the same grid, bearings split instead of pooled: north-south worst
  **496.7 ppm**, east-west worst **493.5 ppm**, and the largest difference between the two bearings at
  any one of the 209 points is **3.26 ppm**. A conformal projection should show equal scale in every
  direction, so this confirms the projection behaves as theory says over the whole city, not just in
  the core. Fields `ns_worst_ppm`, `ew_worst_ppm`, `max_pairwise_diff_ppm` in
  `config/world_coordinates.json`.
- Area effect is second order: planar EPSG:32642 areas agree with geodesic areas to within
  **0.0511%** on every Karachi geometry.

The locked decision stands: EPSG:32642 is fit for 1:1 use. The earlier M0 guess of 30–40 cm/km was
pessimistic for the core and slightly optimistic for the western boundary; 50 cm/km is the measured
city-wide worst case, and it is far below any distance a player or a gameplay system can notice.

## Area method

Primary: `pyproj.Geod(ellps="WGS84").geometry_area_perimeter` on the stored EPSG:4326 rings. This is
a true ellipsoidal geodesic area and is what every published km² figure uses.

Cross-check: reproject the same geometry to EPSG:32642 with `pyproj.Transformer(always_xy=True)` and
take the planar Shapely area. Both are recorded side by side in
`GIS/validation/district_measurements_m15.csv`.

Reconciliation rule: if the two disagree by more than **0.1%**, stop and investigate; the current
worst case is 0.0511%.

## Distance method

Never measure distance in degrees. Convert to EPSG:32642, or use `Geod.inv` for a true geodesic.
Chunk indices use projected eastings and northings only.

## Category definitions used in the land/water table

Definitions are fixed so the identity cannot be read as independent evidence.

| Term | Definition |
|---|---|
| Administrative area | area of the L1 OSM district polygon, unmodified |
| Land | administrative area intersected with the **union** of the L2 land layer |
| Mapped water | administrative area intersected with the **union** of the L3 water layer |
| Overlap | area inside the district present in both layers |
| Unclassified | administrative area minus the area covered by the union of land and water |

Because unclassified is *defined* as "in neither layer", the identity
`A_T = A_L + A_W − A_L∩W + A_U` holds **by construction**. Its residual validates arithmetic and
implementation consistency, not geographic correctness. A residual near zero does **not** mean the
coastline is right.

## Mask consumption rule

OSMData products are grid tiles that deliberately overlap. Measured on the frozen layers: 8
overlapping land pairs totalling 23.28 km² and 4 water pairs totalling 12.05 km². Therefore every
mask operation must use the **union** of a layer. Summing feature areas double-counts and is
forbidden.

## Units discipline

- `deg²` is a raw geometry diagnostic only and is never presented as an area result.
- km² always means geodesic km² from the primary method unless explicitly labelled planar.
- 1 projected metre = 1 Godot unit. No undocumented scale factor may be introduced.

## Game-world transform

`game_x = easting_m − E0`, `game_z = N0 − northing_m`, north toward negative Z. `E0` and `N0` are
**not yet frozen**; they are set in M2 and must appear in every chunk manifest. Once chunks exist,
changing them requires a versioned migration.
