# Site Designer

A Figma-style visual website builder. Drag shapes, text, buttons, images and inputs on a canvas,
then export clean HTML, CSS and optional JavaScript. The editor is plain JavaScript; the engine
(export, ready-made sections, assistant) is **Python running in the browser via WebAssembly (Pyodide)**.
No server, no build step, no API key.

## AI
Click **AI settings**, paste your own Anthropic API key, and tick **Use AI**. The browser calls the model directly
(`api.anthropic.com`) and the design is edited through validated JSON operations (`ai_request` / `ai_apply` in `web/app.py`).
Never commit a key. Visitors to your published site use their own key. Without a key the free rule-based assistant is used.
For a public app without asking visitors for keys you would add a small backend proxy that holds the key.

## Deploy on GitHub
1. Upload this folder's contents to a repo's `main` branch (keep `web/` and `.github/`).
2. Settings -> Pages -> Source: **GitHub Actions**.
3. Open the Actions tab; when it is green your site is at `https://<user>.github.io/<repo>/`.

## Run locally
`python3 -m http.server -d web 8000` then open http://localhost:8000

## Shortcuts
Space+drag or middle mouse: pan. Ctrl+scroll: zoom. Shift+click: multi-select. Double-click text: edit.
Ctrl+Z / Ctrl+Y: undo/redo. Ctrl+D: duplicate. Delete: remove. Arrow keys: nudge (Shift = 10px).
