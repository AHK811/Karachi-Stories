# Karachi: Street Stories — Starter Prototype

A small Godot 4 third-person 3D blockout inspired by Karachi. This is an original project and is not affiliated with Rockstar Games or the Grand Theft Auto franchise.

## What is included

- A third-person character controller.
- Mouse camera control, WASD movement and jumping.
- A lightweight, generated city blockout with roads, low-rise buildings, a small market strip, chai/biryani kiosks, two decorative rickshaws and a simple seafront.
- Godot's Compatibility renderer, selected for low-end hardware.

## What is not included yet

There is no vehicle driving, traffic AI, pedestrian AI, combat, mission system, save system, final art, accurate street geometry or complete Karachi map. The city is a greybox prototype, not a geographically accurate reconstruction.

## Run it

1. Install the current stable Godot 4 release from https://godotengine.org/download/.
2. Extract this folder to a local drive.
3. Open Godot Project Manager.
4. Choose **Import** and select this folder's `project.godot` file.
5. Open the project and press **F5** to run the whole project.

## Controls

| Input | Action |
|---|---|
| W / A / S / D | Move |
| Mouse | Look around |
| Space | Jump |
| Escape | Release mouse cursor |
| Left mouse button | Capture mouse cursor again |

## Hardware note

The project uses simple primitive meshes and the Compatibility renderer. It is intended as a small test scene, not a benchmark or a promise of smooth performance on every device. Reduce the viewport size and keep the scene small if the editor struggles.

## Folder structure

```text
Karachi_Street_Stories_Starter/
├── project.godot
├── scenes/
│   └── main.tscn
├── scripts/
│   ├── player.gd
│   └── world.gd
└── docs/
    ├── PROJECT_PLAN.md
    └── AI_CODING_RULES.md
```
