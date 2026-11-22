# Project Plan: Karachi: Street Stories

## 1. Product definition

**Working title:** Karachi: Street Stories  
**Genre:** Third-person, single-player, open-world action-adventure / city sandbox  
**Setting:** A fictionalized, research-led version of contemporary Karachi  
**Initial release target:** Windows PC prototype  
**Long-term targets:** Windows, Linux, macOS, Android, iOS, then consoles through approved platform access and a porting plan

The ambition is a large, systemic city game with the freedom and activity density associated with major open-world titles. The project must have original characters, dialogue, plot, missions, UI, logos, code, music and art. It must not reuse GTA names, characters, maps, missions, assets, source code, logos or distinctive branding.

## 2. Scope discipline

Do not start by recreating all of Karachi. Start with one compact, walkable district blockout inspired by the urban texture around Saddar and Burns Road. The supplied starter is only about 150 × 150 metres of playable blockout. After movement, camera, collisions, navigation and performance are stable, expand the first proper vertical slice toward 500–800 metres across in game-space, with fictionalized road geometry and a small number of recognizable environmental cues.

The first playable milestone is deliberately limited:

- Third-person walking and jumping.
- Camera orbit and collision.
- A small network of roads and sidewalks.
- Low-rise residential and commercial buildings.
- A market strip with simple stalls and decorative rickshaws.
- A basic seafront blockout.

Not in milestone one: driving, combat, wanted levels, police systems, crowds, full mission chains, multiplayer, online services or a complete city map.

## 3. Engine and technical direction

Use **Godot 4.7.2 stable** (or a later stable 4.x release), GDScript and the **Compatibility renderer** for the first prototype. Avoid beta/dev builds for the project baseline. It is open source and suitable for an inexpensive, code-first learning path. The current developer laptop is an older dual-core i5 with integrated Intel HD 520 graphics, so keep geometry simple, avoid expensive real-time lighting, use small textures and test at 720p or lower.

Godot can export to Windows, macOS, Linux, Android, iOS and web. Console distribution is a separate programme: the developer must obtain platform-holder approval, SDK access and usually a certified porting route. Do not claim that one click builds for every console.

If the project later secures a capable workstation, a funded team and a high-fidelity target, reassess Unreal Engine. Do not switch engines merely because a generated demo looks more impressive; switching would require rebuilding systems and validating assets.

## 4. Karachi world-building plan

Use real Karachi as a research reference, not as a promise of 1:1 simulation. Prioritize the city's recognizable everyday systems:

- Street hierarchy: arterial roads, service roads, tight lanes, markets and coastal access.
- Mobility: motorcycles, rickshaws, minibuses, cars, buses, delivery riders and pedestrians.
- Street commerce: chai stalls, biryani shops, bakeries, pharmacies, mobile shops, repair workshops and roadside vendors.
- Built environment: mixed-use buildings, balconies, rooftop water tanks, boundary walls, shop shutters, signboards, overhead cabling and varied road conditions.
- Soundscape: traffic horns, market chatter, vendors, generators, sea/wind ambience and original music.
- Language: Urdu, Sindhi and English in context, with respectful localization and proofreading.

Potential future districts: Saddar / old commercial core, Lyari-inspired blocks, Clifton / seafront, Korangi / industrial areas, Gulshan-e-Iqbal / residential-commercial zones and Malir outskirts. Use a fictionalized layout and compress distances for enjoyable gameplay. Verify public landmarks and district boundaries from reliable sources before building them.

For map data, OpenStreetMap may be used as a base where appropriate, but it is licensed under ODbL and has attribution/share-alike obligations. Keep a record of data sources and licences. Government and planning maps can help validate district structure. Do not scrape proprietary map tiles or copy Google Maps imagery into the game.

## 5. Development roadmap

### Phase 0 — Foundations
- Install Godot 4.x, Git and a code editor.
- Import and run this starter project.
- Create a Git repository and commit the untouched baseline.
- Learn nodes, scenes, scripts, signals, physics bodies and the debugger.

### Phase 1 — Walking prototype
- Stabilize player movement and camera.
- Add collision-safe buildings, stairs, doors and simple interaction prompts.
- Add an in-game pause menu and settings for mouse sensitivity and graphics quality.
- Test frame rate and collision behaviour on the actual laptop.

### Phase 2 — Driving prototype
- Add one original motorcycle or compact car.
- Implement enter/exit, throttle, braking, steering and camera follow.
- Add basic traffic rules and simple road navigation.
- Test keyboard and controller input before adding more vehicles.

### Phase 3 — Living district
- Add low-cost pedestrian and vehicle spawners.
- Use navigation and simple state machines, not a large language model, for real-time NPC movement.
- Add shops, interactions, time-of-day and ambient sound.
- Keep NPC counts and simulation distance configurable.

### Phase 4 — Mission framework
- Create a data-driven mission state machine.
- Add objective markers, dialogue, checkpoints and fail/retry logic.
- Write an original story and original characters rooted in the fictionalized setting.

### Phase 5 — Expand Karachi
- Build districts as separate streamed scenes or chunks.
- Create a road graph and district data model.
- Add traffic density, landmarks, interiors and mission hubs incrementally.
- Use profiling before increasing world size or NPC count.

### Phase 6 — Release engineering
- Windows first; then Android and iOS after mobile performance work.
- Linux and macOS builds after input, graphics and packaging tests.
- Console ports only after approval, SDK access, certification planning and budget.
- Add accessibility, localization, crash reporting, save migration and QA before release.

## 6. AI / vibe-coding workflow

Use AI to accelerate implementation, not to replace engineering judgement.

1. Give the coding agent the current project folder and `docs/AI_CODING_RULES.md`.
2. Ask it to inspect the project before editing.
3. Assign one feature at a time, with explicit acceptance criteria.
4. Ask it to list the files it intends to change before making broad edits.
5. Have it explain the implementation and give manual test steps.
6. Run the game yourself after every change. Keep only changes that pass.
7. Commit working states to Git so a broken AI edit can be reverted.

Suggested division of labour:
- ChatGPT: design decisions, task breakdowns, code explanations, debugging hypotheses and review checklists.
- Claude Code / Cursor / Windsurf: edit files in the project, implement one scoped task and run available checks.
- Blender: create or modify original 3D models and collision meshes.
- Audio tools: create or commission original ambience, effects and music.

Do not let an AI agent rewrite the whole project to fix one bug. Do not accept unreviewed generated assets whose licences or provenance are unknown.

## 7. Success criteria for the first milestone

The prototype is successful when:
- It imports and launches in Godot without script errors.
- The player can walk around the blockout without falling through the ground.
- The camera orbits and can be released/re-captured.
- Buildings block the player.
- The market strip and seafront are visible enough to communicate the setting.
- The project can be committed to Git and reopened from a clean checkout.

## 8. Important reality check

A polished, full-city, GTA-scale game is a multi-year, multi-discipline production. AI can speed up code, placeholder art and documentation, but it cannot remove the need for game design, original art direction, animation, audio, optimization, QA, legal review and platform certification. The correct first goal is a small game that works, not a giant map full of broken systems.
