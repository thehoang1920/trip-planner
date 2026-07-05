# AGENTS.md — Trip Planner

## What This Is

A personal trip planning workspace using OpenStreetMap APIs (free, no key) + Geoapify (free key) + Leaflet.js for interactive maps.

**Live URL:** https://thehoang1920.github.io/trip-planner/2026-Singapore/plan-overview.html
**Repo:** https://github.com/thehoang1920/trip-planner (public — GitHub Pages requires public repo on free tier)

**IMPORTANT — Git Sync Rule (STRICT):** Every time you modify any files in this repo — especially `plan-overview.html` — immediately run:
```powershell
git add -A && git commit -m "..." && git push
```
The live GitHub Pages site must reflect local changes at all times. The user accesses the planner remotely via the live URL, so never leave local changes unpushed.

- **Core tool:** `osm_tools.py` — Python CLI. Supports two providers:
  - `osm` (default): Nominatim (geocoding), OSRM (routing), Overpass (POIs). No API key needed.
  - `geoapify`: Geoapify API. Requires `GEOAPIFY_KEY` env var (or hardcoded default fallback).
- **Trip data:** `<year>-<city>/` folders with itinerary, hotel info, README
- **Skill reference:** `osm-planner` skill loaded via OpenCode for API patterns and Leaflet map templates

## Commands

```powershell
# ── Geocoding (address ↔ coordinates) ──
python osm_tools.py geocode "Marina Bay Sands Singapore"
python osm_tools.py geocode "Marina Bay Sands" --provider geoapify
python osm_tools.py reverse 1.2834 103.8607
python osm_tools.py reverse 1.2834 103.8607 --provider geoapify

# ── Routing (A→B) ──
python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking
python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking --provider geoapify

# ── Distance/Time matrix ──
python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" "103.8303,1.2494" --mode driving
python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" --mode driving --provider geoapify

# ── POI/Places search ──
python osm_tools.py poi "Singapore" --type tourism
python osm_tools.py poi "Singapore" --type food --provider geoapify

# ── Multi-stop trip plan ──
python osm_tools.py plan "103.8607,1.2834" "103.8636,1.2817" "103.8303,1.2494" --mode walking
python osm_tools.py plan "103.8607,1.2834" "103.8636,1.2817" --mode driving --provider geoapify
```

## Provider Recommendations

| Task | Recommended | Why |
|------|------------|-----|
| Quick geocode | `osm` (default) | No key, fast enough for most cases |
| Precise geocode | `geoapify` | Better address parsing, more details |
| Reverse geocode | `geoapify` | Returns formatted address, city, postcode |
| Walking route | `geoapify` | Road names, turn-by-turn with local characters |
| Driving route | Either | Both work well; Geoapify has better instructions |
| Distance matrix | `osm` (default) | Unlimited stops; Geoapify free tier limited |
| POI search | `geoapify` | Richer data (address, categories, photos) |
| Multi-stop plan | `osm` (default) | Unlimited waypoints; Geoapify free = 2 only |

## Coordinate Format

All coordinates on the CLI use `lng,lat` order regardless of provider.
`osm_tools.py` auto-converts to `lat,lng` when calling Geoapify internally.
Example: `103.8607,1.2834` = Marina Bay Sands.

## Rate Limits

- **Nominatim (OSM):** 1 req/sec max. Always set `User-Agent` header.
- **OSRM (OSM):** ~10k req/hr. Max ~100 coordinate pairs per request.
- **Overpass (OSM):** Rate-limited. Use `out 30;` to cap results.
- **Geoapify:** Free tier = 3,000 requests/day across all endpoints.

## Trip Folder Structure

Each trip lives in `<year>-<city>/` and should contain:
- `README.md` — flight details, hotel, timeline table
- `itinerary.md` — day-by-day plan with checkboxes
- `hotel-area.md` — nearby MRT, food, transit times
- `plan-overview.html` — interactive planner page (the main deliverable)

## Current Trips

- `2026-Singapore/` — Dec 26–31, 2026. Hotel: Hotel 81 Premier Star (Geylang). Flight: SGN↔SIN via Singapore Airlines.

## Key Conventions

- Use `Invoke-RestMethod` in PowerShell for raw API calls
- URL-encode queries with `[System.Web.HttpUtility]::UrlEncode()`
- For Singapore transit details (bus/MRT schedules), use LTA DataMall API (requires free signup)
- `.nojekyll` file at repo root so GitHub Pages doesn't ignore files starting with `_`
- GitHub Pages URL pattern: `https://<user>.github.io/<repo>/<year>-<city>/plan-overview.html`

---

## HTML Planner — Complete Reference (`plan-overview.html`)

This section documents the full interactive planner pattern built for Singapore 2026. Use this as a template for future trips.

### Architecture Overview

Single self-contained HTML file with:
- Embedded `<style>` block (no external CSS except Leaflet CDN)
- Embedded `<script>` block at end of body
- Leaflet.js CDN for the map
- CartoDB Positron tiles for clean Google-like appearance
- No build tools, no frameworks — works by opening the file in a browser

### Two-Column Layout

```css
.layout { display: flex; gap: 24px; align-items: flex-start; }
.col-left { flex: 1; min-width: 0; }
.col-right { width: 320px; flex-shrink: 0; position: sticky; top: 24px; }
```

- **Left column:** Info card → Mini map → Timeline (day cards)
- **Right column:** Sticky preview panel for hover images
- **Responsive:** `@media (max-width: 900px)` stacks columns, preview panel becomes static

### Day Card Structure (Collapsible)

```html
<div class="day-card">
  <div class="day-dot arrive|depart|empty">✈|2</div>
  <div class="day-header">
    <span class="day-num">Day 1</span>
    <span class="day-date">Sat, Dec 26</span>
    <span class="collapse-icon">▼</span>
  </div>
  <div class="day-body">
    <div class="day-label">Description</div>
    <!-- stops here -->
  </div>
</div>
```

- Clicking `.day-header` toggles `.collapsed` class on `.day-card`
- `.day-body` uses `max-height` + `opacity` transition for smooth collapse
- **Empty days** get `empty-day` class for dashed border + reduced opacity
- Each `.day-body` wraps all content below `.day-header` (label + stops)

### CSS for Collapse

```css
.day-card .day-body { overflow: hidden; transition: max-height .3s ease, opacity .2s; max-height: 2000px; opacity: 1; }
.day-card.collapsed .day-body { max-height: 0; opacity: 0; }
.day-card.collapsed .collapse-icon { transform: rotate(-90deg); }
```

### Stop / Sub-Event Structure

```html
<div class="stop" data-lat="1.31155" data-lng="103.88085" data-location="Hotel 81 Star" data-img="URL" data-caption="Caption">
  <span class="emoji">🏨</span>
  <span class="name">Stop name</span>
  <span class="time">~17:00</span>
</div>

<div class="stop parent expanded" onclick="toggleSub(this)" data-lat="..." data-lng="..." data-location="..." data-img="..." data-caption="...">
  <span class="expand-icon">▶</span>
  <span class="emoji">🛫</span>
  <span class="name">Main Event<span class="sub-count">4 activities</span></span>
  <span class="time">~2 hrs</span>
</div>
<div class="sub-events open">
  <div class="stop" data-img="..." data-caption="...">...</div>
</div>
```

### Data Attributes Reference

| Attribute | Used on | Purpose |
|-----------|---------|---------|
| `data-lat`, `data-lng` | `.stop` | Map marker coordinates + numbering |
| `data-location` | `.stop` | Map marker tooltip text |
| `data-img` | `.stop`, `.wl-card`, `.food-card` | Hover/click preview image |
| `data-caption` | `.stop`, `.wl-card`, `.food-card` | Preview panel name |
| `data-address` | `.stop`, `.wl-card`, `.food-card` | Preview panel address |
| `data-dist` | `.stop`, `.wl-card`, `.food-card` | Preview panel distance |
| `data-gmaps` | `.stop`, `.wl-card`, `.food-card` | Google Maps link in preview |
| `data-time` | `.wl-card` | Operating hours in preview |
| `data-video` | `.wl-card`, `.food-card` | YouTube URL for video preview |
| `data-food-lat`, `data-food-lng` | `.food-card` | Food marker coordinates |

### Preview Panel Structure

```html
<div class="col-right">
  <div class="preview-panel" id="previewPanel">
    <div class="preview-placeholder" id="previewPlaceholder">...</div>
    <img class="preview-img" id="previewImg" style="display:none;">
    <div class="preview-youtube-container" id="previewYoutubeContainer" style="display:none;"></div>
    <div class="preview-video-btn" id="previewVideoBtn" style="display:none; margin-top:6px;">▶ Xem video</div>
    <div class="preview-info" id="previewInfo" style="display:none;">
      <div class="preview-name" id="previewName"></div>
      <div class="preview-addr" id="previewAddr"></div>
      <div class="preview-dist" id="previewDist"></div>
      <div class="preview-time" id="previewTime"></div>
      <div class="preview-gmaps" id="previewGmaps"></div>
    </div>
  </div>
</div>
```

**`#previewVideoBtn` must NOT contain child elements with `wl-video-btn` or `food-video-btn` class** — the global query selector will create a duplicate handler. Use plain text.

### State Variables

```js
let pinnedEl = null;          // Pinned element (null = nothing pinned)
let pinnedMode = 'image';     // 'image' | 'video' — what to re-render for pinnedEl
let currentPreviewEl = null;  // Currently hovered element (video button fallback)
let hideTimeout = null;       // setTimeout ID for mouseout debounce (150ms)
let previewYoutube = null;    // Current YouTube iframe reference
```

**Declared ONCE — duplicate `let` in same `<script>` block causes SyntaxError.**

### showPreview(el, type)

```js
function showPreview(el, type) {
  currentPreviewEl = el;
  // Destroy old iframe
  if (previewYoutube) { previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null; }
  previewYoutubeContainer.style.display = 'none';

  if (type === 'video' && el.dataset.video) {
    // Create YouTube iframe
    previewYoutube = document.createElement('iframe');
    previewYoutube.className = 'preview-img';
    previewYoutube.allow = 'autoplay; encrypted-media; fullscreen';
    previewYoutube.allowfullscreen = true;
    previewYoutube.src = 'https://www.youtube-nocookie.com/embed/' + ytId + '?autoplay=1&rel=0&playsinline=1';
    previewYoutubeContainer.appendChild(previewYoutube);
    previewYoutubeContainer.style.display = 'block';
  } else {
    // Show image
    previewImg.src = el.dataset.img;
    previewImg.style.display = 'block';
  }

  // Update info
  previewName.textContent = el.dataset.caption || '';
  previewVideoBtn.style.display = el.dataset.video && type !== 'video' ? 'block' : 'none';
  previewVideoBtn._lastEl = el.dataset.video ? el : null;
  previewInfo.style.display = 'block';
}
```

### hidePreview()

```js
function hidePreview() {
  if (pinnedEl) { showPreview(pinnedEl, pinnedMode); return; }
  pinnedMode = 'image';
  if (previewYoutube) { previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null; }
  previewYoutubeContainer.style.display = 'none';
  previewPlaceholder.style.display = 'flex';
  previewInfo.style.display = 'none';
}
```

### Map Click — Unpin

```js
map.on('click', function() {
  pinnedEl = null;
  pinnedMode = 'image';
  hidePreview();
});
```

**No `ignoreMapClick` — Leaflet markers don't fire map's click event.**

### Card/Marker Click — Pin/Unpin

```js
el.addEventListener('click', function(e) {
  if (e.target.closest('.wl-video-btn, .food-video-btn')) return;
  pinnedEl = pinnedEl === el ? null : el;
  pinnedMode = 'image';  // ← CRITICAL: reset to image on non-video click
  if (pinnedEl) showPreview(el, 'image'); else hidePreview();
});
```

### Marker Mouseover/Mouseout

```js
m.on('mouseover', () => { if (pinnedEl) return; clearTimeout(hideTimeout); showPreview(card); });
m.on('mouseout', () => { if (pinnedEl) return; hideTimeout = setTimeout(hidePreview, 150); });
```

Preview panel cancels timeout on mouseenter, hides on mouseleave (if unpinned).

### Video Button — Card Level

```html
<div class="wl-video-btn">▶ Xem video</div>
```

```js
btn.addEventListener('click', function(e) {
  e.stopPropagation();
  const card = this.closest('[data-img]');
  pinnedEl = pinnedEl === card ? null : card;
  pinnedMode = 'video';
  if (pinnedEl) showPreview(card, 'video'); else hidePreview();
});
```

### Video Button — Preview Panel (`#previewVideoBtn`)

```js
previewVideoBtn.addEventListener('click', function() {
  const el = currentPreviewEl || this._lastEl;
  if (!el || !el.dataset.video) return;

  if (pinnedEl === el && pinnedMode === 'video') {
    // Toggle off
    pinnedEl = null; pinnedMode = 'image'; hidePreview(); return;
  }
  if (pinnedEl && pinnedEl !== el) { pinnedEl = null; pinnedMode = 'image'; }

  pinnedEl = el;
  pinnedMode = 'video';
  // create iframe...
});
```

Uses `currentPreviewEl || this._lastEl` fallback — `_lastEl` is set by `showPreview()`.

### Hover/Pin Interaction Matrix

| Action | pinnedEl | pinnedMode | Result |
|---|---|---|---|
| Hover element | unchanged | unchanged | Image + video button |
| Click element | set | `'image'` | Pins image |
| Click same again | null | `'image'` | Unpins |
| Click different | changed | `'image'` | Pins new image |
| Click video btn (1st) | set | `'video'` | Plays video |
| Click video btn (same) | null | `'image'` | Unpins video |
| Click blank map | null | `'image'` | Hides everything |

### Map Route Toggle

```js
if (wasCollapsed) {
  Object.keys(dayRoutes).forEach(k => map.removeLayer(dayRoutes[k].layer));
  map.addLayer(dayRoutes[dayNum].layer);
  map.fitBounds(coords, { padding: [30, 30], maxZoom: 14 });
} else if (activeDay === dayNum) {
  map.removeLayer(dayRoutes[dayNum].layer);
  activeDay = null;
}
```

### Emoji Markers

```js
const icon = L.divIcon({ className: '',
  html: '<div style="font-size:18px;line-height:1;text-align:center;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.5));">🎢</div>',
  iconSize: [22,22], iconAnchor: [11,11]
});
```

### YouTube ID Regex

```js
url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/)[1]
```

### YouTube Embed

```js
// privacy: youtube-nocookie.com, always create fresh iframe per play
previewYoutube = document.createElement('iframe');
previewYoutube.allow = 'autoplay; encrypted-media; fullscreen';
previewYoutube.allowfullscreen = true;
previewYoutube.src = 'https://www.youtube-nocookie.com/embed/' + ytId + '?autoplay=1&rel=0&playsinline=1';
previewYoutubeContainer.appendChild(previewYoutube);
```

### Common Bugs

1. **Duplicate `let` declarations** — causes SyntaxError, entire script fails.
2. **`ignoreMapClick` flag** — unnecessary (Leaflet markers don't fire map click), causes first map-click to be silently dropped.
3. **`pinnedMode` not reset on marker click** — video button sees `pinnedEl === el && pinnedMode === 'video'` and toggles off instead of playing. Always set `pinnedMode = 'image'` after non-video clicks.
4. **Preview panel button class collision** — `<span class="wl-video-btn">` inside `#previewVideoBtn` matches global selector, creates duplicate handler. Use plain text instead.
5. **`display:none` buttons not clickable** — ensure button is visible (`display:block`) before users can click it.
6. **Iframe not destroyed** — old video continues audio after unpin. Always do `previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null;` in both showPreview and hidePreview.

### Leaflet CDN

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### New Trip Checklist

1. Create `<year>-<city>/` folder
2. Copy template from existing `plan-overview.html`
3. Update trip info, dates, hotel, flight
4. Create day cards (one per day)
5. Add stops with data attributes (lat, lng, img, caption, address, dist, gmaps, video)
6. Label empty days with `empty-day` class
7. Find images on Wikimedia Commons (500px width)
8. Add wishlist section with cards + YouTube videos
9. Add food section with cards
10. Add `.nojekyll` at repo root
11. Commit + push
