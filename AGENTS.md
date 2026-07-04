# AGENTS.md — Trip Planner

## What This Is

A personal trip planning workspace using free OpenStreetMap APIs + Leaflet.js for interactive maps. No API keys needed.

**Live URL:** https://thehoang1920.github.io/trip-planner/2026-Singapore/plan-overview.html
**Repo:** https://github.com/thehoang1920/trip-planner (public — GitHub Pages requires public repo on free tier)

**IMPORTANT — Git Sync Rule:** Every time you modify any files in this repo, immediately `git add -A && git commit -m "..." && git push` so the online Pages site stays in sync. The user accesses the planner remotely via the live URL.

- **Core tool:** `osm_tools.py` — Python CLI wrapping Nominatim (geocoding), OSRM (routing), Overpass (POIs)
- **Trip data:** `<year>-<city>/` folders with itinerary, hotel info, README
- **Skill reference:** `osm-planner` skill loaded via OpenCode for API patterns and Leaflet map templates

## Commands

```powershell
# Geocode address to coordinates
python osm_tools.py geocode "Marina Bay Sands Singapore"

# Get route between two points (driving|walking|bike)
python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking

# Distance/time matrix for multiple stops
python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" "103.8303,1.2494" --mode driving

# Search POIs in an area
python osm_tools.py poi "Singapore" --type tourism

# Multi-stop trip plan with turn-by-turn
python osm_tools.py plan "103.8607,1.2834" "103.8636,1.2817" "103.8303,1.2494" --mode walking
```

## Coordinate Format

OSM APIs use `lng,lat` order (NOT `lat,lng`). Example: `103.8607,1.2834` = Marina Bay Sands.

## Rate Limits

- **Nominatim:** 1 req/sec max. Always set `User-Agent` header.
- **OSRM:** ~10k req/hr. Max ~100 coordinate pairs per request.
- **Overpass:** Rate-limited. Use `out 30;` to cap results.

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

### Preview Panel (Right Column)

```html
<div class="col-right">
  <div class="preview-panel" id="previewPanel">
    <div class="preview-placeholder" id="previewPlaceholder">Hover a stop to see photo</div>
    <img class="preview-img" id="previewImg" style="display:none;">
    <div class="preview-caption" id="previewCaption"></div>
  </div>
</div>
```

Triggered by `mouseenter`/`mouseleave` on both:
- Timeline stops with `data-img` (via `.stop[data-img]` selector)
- Map markers with `data-img` (via Leaflet `mouseover`/`mouseout` events)

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
5. **For each stop add:** `data-lat`, `data-lng`, `data-location`, `data-img`, `data-caption`
6. **Set day label** — short description of the day's theme
7. **Empty days** get `empty-day` class + placeholder text
8. **Find images** on Wikimedia Commons for each location
9. **Create wishlist section** — attractions with cards, Google Maps links, hover images
10. **Create food section** — restaurants with name, rating, notes, Google Maps link
11. **Add `.nojekyll`** file at repo root if not present
12. **Commit and push** to deploy to GitHub Pages
