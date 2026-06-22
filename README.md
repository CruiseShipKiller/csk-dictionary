# Cruise Dictionary (PWA)

An offline-capable cruise terminology dictionary. Installable to a phone
home screen; works without a connection once it has been opened online once.

## Repo contents

| File | Purpose |
|------|---------|
| `index.html` | The app. Loads data from `dictionary.json` at runtime. |
| `dictionary.json` | The dictionary data (entries + categories). **Generated — do not hand-edit.** |
| `cruise_dictionary_complete.csv` | The **source of truth**. Edit this to change the dictionary. |
| `build.py` | Converts the CSV into `dictionary.json`. |
| `sw.js` | Service worker. Enables offline use. |
| `manifest.json` | PWA manifest (app name, icons, install behavior). |
| `dictionarybackgrond.png` | Splash screen hero image. |
| `icons/` | App icons for install + home screen. |

## Updating the dictionary

1. Edit `cruise_dictionary_complete.csv` (add/change/remove rows).
   Columns: `term, def, context, type, cat`
   - `context` is optional (leave blank if none)
   - `type` must be: `passenger`, `crew`, or `nautical`
   - `cat` must match a category name in `build.py`
2. Run the build:
   ```
   python3 build.py
   ```
   It validates the CSV and writes `dictionary.json`. If anything is wrong
   (bad type, unknown category, duplicate term, empty field) it stops and
   tells you what to fix, without writing a broken file.
3. Commit `cruise_dictionary_complete.csv` and `dictionary.json` together.

Online visitors see the new data immediately (the service worker fetches
`dictionary.json` network-first). Offline users get it the next time they
open the app with a connection.

## Adding or reordering categories

Edit the `CATEGORIES` list at the top of `build.py` (name + icon, in display
order), then re-run the build. Category order in that list = order in the app.

## Changing the app shell (index.html, icons, hero image)

After changing any of those, bump `CACHE_VERSION` in `sw.js` (e.g. `v1` → `v2`)
and commit. That tells installed devices to refresh their cached copy. You do
**not** need to bump it for `dictionary.json` updates.

## Testing locally

Because the app fetches `dictionary.json`, opening `index.html` directly from
disk (`file://`) will fail (browser security). Serve it instead:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000`. On the live GitHub Pages URL it just works.
