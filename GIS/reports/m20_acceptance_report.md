# M2.0 — World Coordinate Foundation acceptance report

Executed 2026-11-22. Repository root at execution time: `D:\Karachi Street Stories`
(WSL: `/mnt/d/Karachi Street Stories`). This is **not** `D:\Karachi-Game`; that folder was renamed
by the project owner and the difference is recorded in DECISIONS.md D-044.

Every number below came from a command that was run and whose output was read. Where something was
not verified, it says so in the same sentence.

## Artifact name mapping

The brief asked for specific filenames. Four already exist under different names from earlier
milestones, so nothing was duplicated:

| Brief asked for | Delivered as | Why |
|---|---|---|
| `Documentation/WORLD_COORDINATE_SYSTEM.md` | `Documentation/WORLD_COORDINATES.md` | same content, shorter name |
| `Configuration/world_coordinates.json` | `config/world_coordinates.json` | `config/` is the existing lowercase convention |
| `Tools/world_coordinates/test_world_coordinates.py` | `Tools/osm_importer/test_world_coordinates_m20.py` | one tool tree, `_m20` suffix like every other milestone script |
| `GIS/reports/m20_acceptance_report.md` | this file | as requested |

## Phase A — environment audit (nothing changed)

Godot **is not installed on this machine**. Detection attempted, all negative:

```
not on PATH: godot, godot4, godot.exe, Godot_v4.7-stable_win64.exe
absent: C:\Program Files\Godot
absent: C:\Program Files (x86)\Godot
absent: C:\Users\AK BROTHER\AppData\Local\Programs\Godot
absent: C:\Godot
D:\ and E:\ recursive to depth 3 for 'Godot*': no results
HKLM + HKCU uninstall registry, DisplayName like '*Godot*': no results
no .godot/ directory anywhere under D:\ to depth 2  (the editor has never opened this project)
```

Therefore **the engine version is unknown and the renderer cannot be confirmed from a running
engine**. What exists is a declaration: `project.godot` says
`config/features=PackedStringArray("4.7", "GL Compatibility")` and
`renderer/rendering_method="gl_compatibility"`. A string in a project file is not evidence of an
installed engine, so the contract records `godot_executable_found: false` and test 15 asserts that
this honest field exists rather than an invented version.

Existing game files inspected, not modified (`git status` shows no change under
`Karachi Street Stories/`):

```
Karachi Street Stories/project.godot      config_version=5, main scene res://scenes/main.tscn,
                                          gl_compatibility desktop AND mobile, 1280x720,
                                          physics 3d default_gravity 9.8
Karachi Street Stories/scenes/main.tscn
Karachi Street Stories/scripts/world.gd   procedural blockout: ground box 240x1x240 m, 5x5 grid of
                                          roads at -60/-30/0/30/60 m, 16 box buildings, seafront
                                          box, capsule player, HUD
Karachi Street Stories/scripts/player.gd  CharacterBody3D, WASD + mouse-look, SpringArm3D camera,
                                          move_speed 6.0, jump 4.5
```

Consequence for M2.0: the coordinate system is specified against Godot 4's documented right-handed
Y-up frame and the Compatibility renderer setting already in the file, but **no GDScript was written
and nothing was executed in an engine**, because there is no engine to execute in. M2.0's Phase C
contract is Python-verified only. This is the single largest honest gap in the milestone.

Note also: `scripts/world.gd` builds a fictional 240 m blockout with hard-coded metre positions and
no reference to any projected coordinate. It does not conflict with this contract and was not
touched; replacing it is M2.2/M2.3 work.

## Phase B — canonical GIS audit (verified, unmodified)

`GIS/canonical/v1.0.0/manifest.json`: dataset version `1.0.0`, status frozen, CRS
`EPSG:4326` for storage, L1 layer `extent_policy: full administrative extent preserved including
maritime area`, source "OpenStreetMap relations, assembled by osmium", licence ODbL 1.0,
modification "none; geometry reproduced from source without simplification".

| Check | Result |
|---|---|
| `checksums.sha256` vs files on disk | **8/8 match** (canonical 11, M2.0 13) — dataset untouched by M2.0 |
| District geometries | **7 present**, names Central, East, Keamari, Korangi, Malir, South, West; all valid (`invalid=[]`) |
| Division geodesic area reproduced | got 5,839.9402 km² vs declared 5,839.94, tol 0.05 |
| District partition vs division | symmetric difference **0.000000 km², empty=True** |
| Land/water overlap | 0.000000 km² |
| Geodesic vs EPSG:32642 planar areas | max relative difference 0.0511% |
| Administrative extent in EPSG:32642 | E 225,502.25 … 356,734.09, N 2,703,445.33 … 2,840,930.24 |
| Mask extent in EPSG:32642 | E 215,797.75 … 369,672.53, N 2,688,057.32 … 2,856,522.79 |

The masks reach the clip box, i.e. **22.64 km wider east-west and 30.98 km taller north-south** than
the administrative division. That is a processing artifact of how the gridded coastline products were
cut, so it is deliberately excluded from the world origin rule (test 16 asserts the flag and the
exclusion).

## Phase C — the coordinate contract

Origin rule, deterministic and reproducible from the frozen L1 layer only:

```
E0 = floor(min_easting  / 512) * 512 = floor(225502.25 / 512) * 512 = 225280
N0 = ceil (max_northing / 512) * 512 = ceil (2840930.24 / 512) * 512 = 2841088
```

`225280 = 440 × 512` and `2841088 = 5549 × 512`, so the origin is exactly on a chunk corner and every
chunk index inside the division is non-negative. Test 02 recomputes both from the geometry and fails
on drift.

Transform, identical to the convention in the brief (`X = E − E0`, `Z = −(N − N0)`, `Y = H − H0`):

```
game_x =  easting_m  − E0          east   -> +X
game_z =  N0 − northing_m          north  -> −Z   (so Z increases southward)
game_y =  elevation_m − vertical_origin_m
```

**Vertical datum: explicitly unresolved.** `vertical_origin_m = 0.0` with
`vertical_datum: "UNSET - no licensed elevation source; game Y uses a documented ground-height
fallback of 0 m"`. There is no elevation data in this repository and OSM does not provide heights
for Karachi buildings as a general rule, so a flat 0 is a documented fallback, not a surveyed
surface. Test 14 requires the string to still contain `UNSET`, so nobody can quietly present a plain
as terrain. This matches the brief's instruction not to assume OSM elevation.

Chunk system:

```
chunk_x = floor((easting  − E0) / 512)      local_x = easting  − (E0 + chunk_x*512)  in [0,512)
chunk_z = floor((N0 − northing) / 512)      local_z = (N0 − northing) − chunk_z*512  in [0,512)
```

Division covers **257 × 269 = 69,133 chunks** (153.9 × 168.5 km at 512 m). Measured chunk indices at
the corners: origin → (0,0); division SW → (0,268); division NE → (256,0); a point 1 mm outside the
origin → (−1,−1), which is exactly why the origin rounds outward.

## Phase D — tests and measurements

```
test_world_coordinates_m20.py   16 PASS  0 FAIL   exit 0
test_canonical_m16.py           15 PASS  0 FAIL  SKIP 0   exit 0
test_boundary_m15.py            14 PASS  0 FAIL  SKIP 0   exit 0
                                ----
                                45 PASS
```

Exit codes were captured as `$?` from the interpreter itself, never from a pipe.

| Requirement | Measured |
|---|---|
| Control points, definitional | (69°E, 0°N) → E 500000.000000, N 0.000000 |
| Control points, independent implementation | pyproj vs a hand-written 4th-order Snyder transverse Mercator: max **3.43 mm** over 9 points |
| Metric plausibility | 1° latitude = 110,765.8 m; 1° longitude at 24.5°N = 101,378.8 m |
| Axis direction | Saddar→N.Malir: game_x 74,667.0 → 89,055.6 (east +X) and game_z 90,188.5 → 72,664.5 (north −Z) |
| Round trip 4326→32642→game→32642→4326 | max **0.000000002 m** over 4,554 projected grid points at 2,000 m spacing |
| District boundaries and city extent | all **2,074 L1 vertices** (exterior and interior rings of division + 7 districts) map inside the declared chunk grid, 0 out of range |
| Projection distortion | k = 0.999868 … 1.000497, mean 1.000097, worst **496.7 ppm** (≈50 cm/km) over 418 one-kilometre geodesic baselines |
| Conformality | N-S worst 496.7 ppm, E-W worst 493.5 ppm, largest per-point difference **3.26 ppm** across 209 points |
| Zone safety | extent lon 66.2°–67.7°, wholly inside the 66°–72° zone-42N band, no zone crossing |
| UTM zone 42N vs custom meridian | 67.05°E custom TM evaluated: lower distortion, rejected for breaking the locked EPSG:32642 decision |

**Local origin, as the brief required, and it is a measured requirement not a style preference.**
Godot `Vector3` is float32. The largest global game coordinate needed for the whole division is
137,643 m, where adjacent float32 values differ by **15.62 mm**. Inside a 512 m chunk the same gap is
**0.061 mm** — 256× finer. So raw UTM numbers must never enter a `Vector3`: keep 64-bit global
projected coordinates, and subtract the chunk origin before constructing any engine-side position.
Test 10 fails if either side of that comparison stops being true.

### Two defects that only executing the suite found

1. The round-trip loop stepped **projected metres by 0.02**, so it needed millions of iterations and
   hung for over ten minutes without ever reaching the twelve checks after it. Fixed to a 2,000 m
   step. A hang that silently hides later assertions is worse than a wrong number.
2. Test 08 assumed every feature is one `Polygon` and crashed with
   `'MultiPolygon' object has no attribute 'exterior'`. Replaced with a ring walker that descends
   MultiPolygon and GeometryCollection, yields interior rings too, and **raises on any unexpected
   geometry type** instead of checking nothing. It now prints the 2,074 vertices it examined so it
   cannot pass vacuously.

### Correction to a previously published figure

DECISIONS.md D-043: the **+211 ppm** in `CRS_AND_MEASUREMENT.md` and in the frozen v1.0.0 manifest was
measured at 7 points in the built-up core, which is the eastern, low-distortion part of the city.
Sampling the whole administrative extent gives **496.7 ppm city-wide**. 211 ppm stays correct for the
core; it was never a city-wide number and must not be quoted as one. The EPSG:32642 decision is
unchanged — 50 cm/km is undetectable in gameplay.

## Phase E — documentation and deliverables

Created: `Documentation/WORLD_COORDINATES.md`, `config/world_coordinates.json`,
`GIS/validation/world_coordinates_m20.json` (byte-identical to the config, SHA-256
`fe150bc74a79…` both), `Tools/osm_importer/derive_world_origin_m20.py`,
`Tools/osm_importer/test_world_coordinates_m20.py`, this report.
Modified: `Documentation/CRS_AND_MEASUREMENT.md`, `Documentation/DECISIONS.md` (D-042…D-045),
ten tool scripts now locate the repository from their own path instead of a hardcoded one.
Deleted: nothing. Game scenes and scripts: untouched. Canonical v1.0.0: untouched, checksum-proved.

## Git state

```
46ccd69 Initial commit                     (merge joining remote main; tree = project content)
8d5916f docs(M2.0): record the approved side-branch push resolution in D-045 and the acceptance report
a1bed55 docs(M2.0): add acceptance report and record the GitHub history conflict
456fea3 feat(M2.0): freeze world coordinate foundation E0/N0 and chunk contract   (15 files, +1017/-26)
3d1a7c4 feat(M1.6): freeze canonical GIS dataset v1.0.0 with reproducible build
working tree clean; remote main == local main == 46ccd69
```

## Open items for the project owner

1. **Engine gate.** M2.0's Godot-side mapping is a specification, not verified code, because no engine
   is installed. Installing Godot 4.x is a ~50-120 MB download and needs your approval; until then
   nothing here has been executed in-game.
2. **Push.** Done. `main` was first pushed to the side branch `world-coordinates-m20`, then, on
   request, the whole project was joined to the pre-existing remote history as `46ccd69
   Initial commit` (parents `[8d5916f, 2d10061]`, `-s ours --allow-unrelated-histories`). Because
   `2d10061` is a parent, `2d10061..46ccd69` is a real **fast-forward** — no force push, nothing
   published was rewritten or deleted. Remote and local `main` are both `46ccd69`; the side branch
   still exists and can be deleted in the UI. No `origin` remote was created and git config was not
   edited. See D-045.
3. **Commit authorship.** The import commit is authored and committed as
   `ak.brothers.811@gmail.com` using per-command `-c user.email=` overrides, so git config stays
   yours. The 14 milestone commits keep `k263018@khi.nu.edu.pk`, which is now publicly visible on a
   public repository — an accepted asymmetry, not an oversight. Changing those too would be a history
   rewrite.
