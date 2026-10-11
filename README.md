# Balikbayan Box Planner

Plan and track what goes into each balikbayan box: items by category, quantity, unit and total price, weight and recipient, box details (size, carrier, tracking, status), a packing checklist, shipping labels and print-friendly packing lists.

It's an installable web app (PWA): it works offline and keeps your list on your phone.

## Use it on Android

1. Turn on GitHub Pages for this repo: **Settings → Pages → Source: Deploy from a branch → `main`, `/ (root)` → Save**.
2. After a minute, open `https://rencevibe.github.io/balikbayan-planner/` in **Chrome on your phone**.
3. Tap **⋮ → Install app** (or **Add to Home screen**).

### Want an .apk file?

Go to **https://www.pwabuilder.com**, paste the link above, then **Package for stores → Android → Generate Package**. The download includes an `.apk` you can install directly (allow *Install unknown apps*) and an `.aab` for Google Play.

## Good to know

- **Your data stays on the device.** Use **Settings → Backup** to save a backup file, and **Restore from backup** on a new phone.
- **Printing:** open a packing list and tap **Print** (or choose *Save as PDF*).

## Files

| Path | What it is |
|---|---|
| `index.html` | The app |
| `manifest.webmanifest`, `icons/` | App name, colours and home-screen icons |
| `sw.js` | Offline support |
| `tools/balikbayan.html` | Source page (also the Claude artifact version) |
| `tools/build_app.py` | Rebuilds the app files from the source page |

### Updating

Edit `tools/balikbayan.html`, then run:

```bash
python tools/build_app.py tools/balikbayan.html .
```

Also change `CACHE` in `sw.js` (for example to `balikbayan-v2`) so installed apps pick up the update.
