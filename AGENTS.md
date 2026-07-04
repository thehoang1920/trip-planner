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
#   Use OSM for quick lookups, Geoapify for more precise results
python osm_tools.py geocode "Marina Bay Sands Singapore"
python osm_tools.py geocode "Marina Bay Sands" --provider geoapify
python osm_tools.py reverse 1.2834 103.8607
python osm_tools.py reverse 1.2834 103.8607 --provider geoapify

# ── Routing (A→B) ──
#   OSRM: fast, good for rough estimates.  Geoapify: better turn-by-turn
#   with road names (including local characters like 薛尔思道)
python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking
python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking --provider geoapify

# ── Distance/Time matrix ──
#   OSRM: unlimited stops.  Geoapify: better accuracy, free tier may limit size
python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" "103.8303,1.2494" --mode driving
python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" --mode driving --provider geoapify

# ── POI/Places search ──
#   Overpass: flexible query with tags (tourism, food, etc).  Geoapify: richer
#   results with address details and categories
python osm_tools.py poi "Singapore" --type tourism
python osm_tools.py poi "Singapore" --type food --provider geoapify

# ── Multi-stop trip plan ──
#   OSRM works well for any number of stops.  Geoapify free tier limited to 2.
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
- **Empty days** (not yet planned) get `empty-day` class for dashed border + reduced opacity
- Each `.day-body` wraps all content below `.day-header` (label + stops)

### CSS for Collapse

```css
.day-card .day-body { overflow: hidden; transition: max-height .3s ease, opacity .2s; max-height: 2000px; opacity: 1; }
.day-card.collapsed .day-body { max-height: 0; opacity: 0; }
.day-card.collapsed .collapse-icon { transform: rotate(-90deg); }
```

### Stop / Sub-Event Structure

```html
<!-- Regular stop -->
<div class="stop" data-lat="1.31155" data-lng="103.88085" data-location="Hotel 81 Star" data-img="URL" data-caption="Caption">
  <span class="emoji">🏨</span>
  <span class="name">Stop name</span>
  <span class="time">~17:00</span>
</div>

<!-- Parent with sub-events (collapsible) -->
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

Key attributes on stops:
- `data-lat` / `data-lng` — coordinates for map markers (only add when stop has a physical location)
- `data-location` — clean location name for map tooltip (e.g. "Changi Airport", "Hotel 81 Star")
- `data-img` — URL for hover preview image
- `data-caption` — caption for the preview image

### Numbering System (CSS Counters)

Only stops with coordinates (`data-lat`) receive a sequential number within each day:

```css
.day-card { counter-reset: stop-order; }
.stop[data-lat] { counter-increment: stop-order; }
.stop[data-lat] .name::before { content: counter(stop-order) ". "; font-weight: 700; color: #fbbf24; }
```

- Numbers restart per day-card
- Sub-events without `data-lat` are NOT numbered
- Map markers show the same number as the timeline stop

### Preview Panel (Right Column) — Hover Detail + Pin

The preview panel shows a photo + location info (name, address, distance, Google Maps link) when hovering any item with `data-img`. Clicking locks the preview until clicked again or blank space is clicked.

**HTML structure:**
```html
<div class="col-right">
  <div class="preview-panel" id="previewPanel">
    <div class="preview-placeholder" id="previewPlaceholder">Hover a stop to see photo</div>
    <img class="preview-img" id="previewImg" style="display:none;">
    <div class="preview-info" id="previewInfo" style="display:none;">
      <div class="preview-name" id="previewName"></div>
      <div class="preview-addr" id="previewAddr"></div>
      <div class="preview-dist" id="previewDist"></div>
      <div class="preview-gmaps" id="previewGmaps"></div>
    </div>
  </div>
</div>
```

**Data attributes required on every hoverable element:**
- `data-img` — image URL for preview
- `data-caption` — location name shown in preview
- `data-address` — full address
- `data-dist` — distance from hotel
- `data-gmaps` — Google Maps search URL

**CSS:**
```css
.preview-panel .preview-info { padding: 12px 16px; border-top: 1px solid #334155; }
.preview-panel .preview-name { font-size: 0.9rem; font-weight: 600; color: #f1f5f9; margin-bottom: 6px; }
.preview-panel .preview-addr { font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; }
.preview-panel .preview-dist { font-size: 0.8rem; color: #60a5fa; margin-bottom: 4px; }
.preview-panel .preview-gmaps { margin-top: 6px; }
.preview-panel .preview-gmaps a { color: #60a5fa; font-size: 0.8rem; text-decoration: none; }
.preview-panel .preview-gmaps a:hover { text-decoration: underline; }
```

**JS — helpers + pin logic (copy verbatim):**
```js
let pinnedEl = null;

function showPreview(el) {
  const img = el.dataset.img;
  if (!img) return;
  previewImg.src = img;
  previewImg.style.display = 'block';
  previewPlaceholder.style.display = 'none';
  previewName.textContent = el.dataset.caption || '';
  previewAddr.textContent = el.dataset.address || '';
  previewDist.textContent = el.dataset.dist || '';
  previewGmaps.innerHTML = el.dataset.gmaps ? '<a href="' + el.dataset.gmaps + '" target="_blank">View on Google Maps</a>' : '';
  previewInfo.style.display = 'block';
}

function hidePreview() {
  if (pinnedEl) {
    showPreview(pinnedEl);
    return;
  }
  previewImg.style.display = 'none';
  previewPlaceholder.style.display = 'flex';
  previewInfo.style.display = 'none';
}
```

**Pin on click — apply to all hoverable elements:**
```js
el.addEventListener('click', function() {
  pinnedEl = pinnedEl === el ? null : el;
  if (pinnedEl) showPreview(el); else hidePreview();
});
```

**Map blank-space unpin — place after tile layer:**
```js
let ignoreMapClick = false;
map.on('click', function() {
  if (ignoreMapClick) { ignoreMapClick = false; return; }
  pinnedEl = null;
  hidePreview();
});
```

**Marker click (prevent map click from unpinning):**
```js
m.on('click', function() {
  ignoreMapClick = true;
  pinnedEl = pinnedEl === s ? null : s;
  if (pinnedEl) showPreview(s); else hidePreview();
});
```

Triggered by `mouseenter`/`mouseleave` on:
- Timeline stops with `data-img` (`.stop[data-img]`)
- Wishlist cards with `data-img` (`.wl-card[data-img]`)
- Food cards with `data-img` (`.food-card[data-img]`)
- Map markers with `data-img` (via Leaflet `mouseover`/`mouseout`)

### Map System (Leaflet + CartoDB)

**Tile layer:** CartoDB Positron for clean, light, Google-like appearance:
```js
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 })
```

**Per-day route layers:** Each day with geo-stops gets a numbered layer group:
- Created on page load but removed from map (hidden)
- Clicking a day header adds the layer to the map and fits bounds
- Toggling off removes the layer
- Route polyline drawn between consecutive stops in yellow (`#fbbf24`)

**Numbered markers:**
```js
const icon = L.divIcon({ className: 'num-marker', html: '' + num, iconSize: [26, 26], iconAnchor: [13, 13] });
const marker = L.marker([lat, lng], { icon }).bindTooltip(num + '. ' + loc, { direction: 'top' });
```

**Numbered marker CSS:**
```css
.num-marker { background: #fbbf24; color: #0f172a; border-radius: 50%; width: 26px; height: 26px; line-height: 22px; text-align: center; font-weight: 700; font-size: 0.8rem; border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
```

### Map Route Toggle Logic

```js
// Click header to collapse/expand
card.classList.toggle('collapsed');

if (wasCollapsed) {
  // Expanding: show route, hide other days' routes
  map.addLayer(dayRoutes[dayNum].layer);
  map.fitBounds(coords, { padding: [30, 30], maxZoom: 14 });
} else {
  // Collapsing: remove route from map
  map.removeLayer(dayRoutes[dayNum].layer);
}
```

### YouTube Video Preview

Each wishlist/food card can have a YouTube video shown in the preview panel. Add `data-video` attribute with the URL:

```html
<div class="wl-card" data-video="https://www.youtube.com/watch?v=kkqyRLX2PGk" ...>
```

The preview panel shows a **▶ Xem video** button when hovering/clicking a card/marker that has `data-video`. Clicking it pins and plays the video in a YouTube iframe:

```js
previewYoutube = document.createElement('iframe');
previewYoutube.allow = 'autoplay; encrypted-media; fullscreen';
previewYoutube.allowfullscreen = true;
previewYoutube.src = 'https://www.youtube-nocookie.com/embed/' + ytId + '?autoplay=1&rel=0&playsinline=1';
```

Uses `youtube-nocookie.com` for privacy. The `▶ Xem video` button is a `<span>` with CSS classes `wl-video-btn` / `food-video-btn` (red border badge). Clicking the card itself only shows the image — video is opt-in via the button.

**CSS:**
```css
.wl-video-btn, .food-video-btn { display: inline-block; font-size: 0.7rem; color: #ef4444; background: #2d1a1a; border: 1px solid #ef4444; border-radius: 4px; padding: 1px 8px; margin-top: 4px; cursor: pointer; transition: all .15s; text-decoration: none; }
.wl-video-btn:hover, .food-video-btn:hover { background: #ef4444; color: #fff; }
```

### Preview Panel — Video Button (in-panel)

A second video button sits inside the preview panel itself (`#previewVideoBtn`), so hovering a map marker also shows the video button:

```html
<div class="preview-video-btn" id="previewVideoBtn" style="display:none; margin-top:6px;">
  <span class="wl-video-btn">▶ Xem video</span>
</div>
```

In `showPreview()`: `previewVideoBtn.style.display = videoUrl && type !== 'video' ? 'block' : 'none';`

### Pin Logic — Hover Doesn't Interrupt Video

Three state variables control the preview:

| Variable | Purpose |
|----------|---------|
| `pinnedEl` | The element whose preview is pinned (clicked to lock) |
| `pinnedMode` | `'image'` or `'video'` — what to show when re-rendering |
| `currentPreviewEl` | The element currently being hovered (used by preview video button) |

**Key rule:** When `pinnedEl` is set, all `mouseenter`/`mouseleave`/`mouseover`/`mouseout` handlers return immediately. This prevents hover from interrupting a pinned video:

```js
el.addEventListener('mouseenter', () => {
  if (pinnedEl) return;  // Don't override pinned content
  showPreview(el);
});
```

### Marker ↔ Card Sync

Map markers and wishlist/food cards share the same preview panel. Both:
- Call `showPreview(el)` on hover → shows image + video button (if `data-video`)
- Call `hidePreview()` on leave
- Call `showPreview(el, 'video')` on video button click

The preview panel is the sync point — hovering a marker shows the same info and video button as its corresponding wishlist card. Markers use emoji-based `L.divIcon`:

```js
const icon = L.divIcon({ className: '', html: '<div style="font-size:18px;...">🎢</div>', iconSize: [22,22], iconAnchor: [11,11] });
```

### Image Sources (Free, No API Key)

- **Wikimedia Commons:** Best source for landmark/attraction photos
  - URL pattern: `https://upload.wikimedia.org/wikipedia/commons/thumb/<path>/<width>px-<filename>`
  - Use 500px width for preview images
- **Blog images:** Can use direct image URLs from travel blogs (check for hotlinking permission)
- **Avoid:** Google Places API (requires API key + billing)

### Leaflet CDN

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### Full HTML Template Pattern

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>City YYYY — Plan Overview</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    /* === Layout === */
    /* === Day Cards === */
    /* === Stops / Sub-events / Numbering === */
    /* === Map + Numbered Markers === */
    /* === Preview Panel === */
    /* === Wishlist / Food Sections === */
    /* === Responsive === */
  </style>
</head>
<body>

  <div class="layout">
    <div class="col-left">
      <!-- Info Card -->
      <!-- Mini Map -->
      <div id="minimap"></div>
      <!-- Timeline -->
      <div class="timeline">
        <!-- Day cards here -->
      </div>
      <!-- Wishlist + Food sections (inside col-left for sticky scroll) -->
    </div>
    <div class="col-right">
      <!-- Preview Panel -->
    </div>
  </div>

  <script>
    // Map initialization + per-day route layers
    // Day click handler (collapse + route toggle)
    // Hover preview panel logic
    // toggleSub() for parent stops
  </script>
</body>
</html>
```

### Building a New Trip — Step Checklist

1. **Create folder:** `<year>-<city>/`
2. **Copy template structure** from an existing `plan-overview.html`
3. **Update trip info** (flight, hotel, dates) in info card and subtitle
4. **Create day cards** — one per day of trip
5. **For each stop add:** `data-lat`, `data-lng`, `data-location`, `data-address`, `data-dist`, `data-gmaps`, `data-img`, `data-caption`
6. **Set day label** — short description of the day's theme
7. **Empty days** get `empty-day` class + placeholder text
8. **Find images** on Wikimedia Commons for each location
9. **Create wishlist section** — attractions with cards, Google Maps links, hover images
10. **Add YouTube videos** to wishlist cards: add `data-video` attribute + `<div class="wl-video-btn">▶ Xem video</div>` inside card
11. **Create food section** — restaurants with name, rating, notes, Google Maps link
12. **Add `.nojekyll`** file at repo root if not present
13. **Commit and push** to deploy to GitHub Pages
