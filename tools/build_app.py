"""Package the planner page as an installable Android web app (PWA).

Usage: python build_app.py <source.html> <out_dir>
"""
import json
import os
import re
import struct
import sys
import zipfile
import zlib

src, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(out, "icons"), exist_ok=True)

page = open(src, encoding="utf-8").read()

# Everything before the first body element (title, font links, style) belongs in <head>.
split = page.index('<header class="hero">')
head_part, body_part = page[:split].strip(), page[split:].strip()

RESET = (":root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);"
         "padding-bottom:env(safe-area-inset-bottom,0px)}"
         "body{margin:0;font:14px/1.4 system-ui,sans-serif}img{max-width:100%}"
         "[hidden]{display:none!important}")

SW_REGISTER = """<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
</script>"""

index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#E9D3B8">
<meta name="description" content="Plan and track what goes into each balikbayan box.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<style>{RESET}</style>
{head_part}
</head>
<body>
{body_part}
{SW_REGISTER}
</body>
</html>
"""
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index)

manifest = {
    "name": "Balikbayan Box Planner",
    "short_name": "Balikbayan",
    "description": "Plan and track what goes into each balikbayan box.",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#FBF5EF",
    "theme_color": "#E9D3B8",
    "categories": ["productivity", "utilities"],
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
open(os.path.join(out, "manifest.webmanifest"), "w", encoding="utf-8").write(json.dumps(manifest, indent=2))

SW = """// Offline support: the app shell is cached on install; fonts are cached the first time they load.
const CACHE = "balikbayan-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest",
  "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon-maskable-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.mode === "navigate") {
    // Network first so updates arrive; fall back to the cached page offline.
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put("./index.html", copy));
      return res;
    }).catch(() => caches.match("./index.html")));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok || res.type === "opaque") {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
    }
    return res;
  })));
});
"""
open(os.path.join(out, "sw.js"), "w", encoding="utf-8").write(SW)


# ---------- icons: a kraft box with marigold packing tape, drawn without any image library ----------
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

KRAFT_BG = hexrgb("#FBF5EF")
BOX = hexrgb("#C98F5C")
LID = hexrgb("#DBA472")
SHADE = hexrgb("#A8703F")
TAPE = hexrgb("#E39B17")
INK = hexrgb("#2B1D16")


def make_icon(size, inset):
    """inset: fraction of the canvas left as padding around the drawing (larger for maskable)."""
    px = [[KRAFT_BG] * size for _ in range(size)]

    def rect(x0, y0, x1, y1, col):
        # coordinates are in a 0..1 design space mapped into the padded area
        span = size * (1 - 2 * inset)
        off = size * inset
        X0, Y0 = int(off + x0 * span), int(off + y0 * span)
        X1, Y1 = int(off + x1 * span), int(off + y1 * span)
        for y in range(max(0, Y0), min(size, Y1)):
            row = px[y]
            for x in range(max(0, X0), min(size, X1)):
                row[x] = col

    rect(0.12, 0.30, 0.88, 0.90, INK)        # outline
    rect(0.14, 0.32, 0.86, 0.88, BOX)        # box body
    rect(0.14, 0.32, 0.86, 0.40, SHADE)      # shadow under the lid
    rect(0.08, 0.18, 0.92, 0.33, INK)        # lid outline
    rect(0.10, 0.20, 0.90, 0.31, LID)        # lid
    rect(0.43, 0.20, 0.57, 0.88, TAPE)       # vertical tape
    rect(0.14, 0.62, 0.86, 0.68, TAPE)       # horizontal tape
    rect(0.22, 0.46, 0.36, 0.52, KRAFT_BG)   # label lines
    rect(0.22, 0.54, 0.33, 0.58, KRAFT_BG)

    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


for name, size, inset in [("icon-192.png", 192, 0.06), ("icon-512.png", 512, 0.06), ("icon-maskable-512.png", 512, 0.16)]:
    open(os.path.join(out, "icons", name), "wb").write(make_icon(size, inset))

# Zip for easy transfer / upload
zpath = out.rstrip("/\\") + ".zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(out):
        for f in files:
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, out))
print("built", out, "and", zpath)
