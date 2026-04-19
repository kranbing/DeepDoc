# DeepDOC Design Generator (Figma Plugin)

This is a tiny Figma plugin that generates **DeepDOC** design frames directly from the current repo's UI tokens (mirrors `web/styles.css`).

It creates:

- A page named `DeepDOC`
- Two desktop frames: `Landing (Projects)` and `Workspace (Chat)`
- A small `Tokens` section (colors, radii, shadow)

## How to run in Figma

1. In Figma Desktop: `Plugins` -> `Development` -> `Import plugin from manifest...`
2. Select `manifest.json` in this folder.
3. Run: `Plugins` -> `Development` -> `DeepDOC Design Generator`

## Notes

- This plugin is intentionally simple: it builds a **clean, editable starting point** (frames, layout, basic components).
- If you want it to generate more details (real card grids, full chat layout, etc.), tell me which screen(s) you care about most and I will extend the generator.

