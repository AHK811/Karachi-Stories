# AI Coding Rules

You are contributing to **Karachi: Street Stories**, an original Karachi-inspired open-world prototype built in Godot 4.x with GDScript.

## Before editing
1. Inspect the full project structure and read `README.md` and `docs/PROJECT_PLAN.md`.
2. Identify the exact feature requested and its acceptance criteria.
3. Explain the intended implementation and list files to be changed.
4. Do not invent existing APIs or assume a node exists without checking the project.

## Implementation rules
- Use Godot 4.x APIs only.
- Keep scripts small and focused.
- Prefer typed GDScript where it improves clarity.
- Use signals or clear interfaces rather than hard-coding dependencies between unrelated systems.
- Do not add plugins or external assets without explaining their licence, size and purpose.
- Do not introduce multiplayer, cloud services or paid APIs unless specifically requested.
- Preserve the Compatibility renderer and low-end hardware target unless there is an explicit architecture decision to change it.
- Avoid large textures, expensive shaders and high-poly meshes in early milestones.
- Do not copy GTA code, maps, branding, characters, missions, UI, audio or assets.
- Never delete or overwrite user work outside the requested scope.

## After editing
1. Summarize each file changed and why.
2. Identify assumptions and known limitations.
3. Run any available static checks or Godot headless import checks.
4. Provide precise manual test steps, including expected behaviour.
5. Do not claim a feature was tested unless it was actually run.
6. If you cannot run Godot, say so and provide a cautious review instead of claiming success.

## Task prompt template

**Feature:** [one feature only]  
**Current behaviour:** [what happens now]  
**Expected behaviour:** [specific result]  
**Acceptance tests:** [observable tests]  
**Constraints:** Keep Godot 4.x, GDScript, Compatibility renderer and low-end PC performance. Do not refactor unrelated systems.
