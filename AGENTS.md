# AGENTS.md — Trip Planner

## What This Is

A personal trip planning workspace using free OpenStreetMap APIs. No API keys needed.

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
- HTML map files (Leaflet-based, rendered locally)

## Current Trips

- `2026-Singapore/` — Dec 26–31, 2026. Hotel: Hotel 81 Premier Star (Geylang). Flight: SGN↔SIN via Singapore Airlines.

## Key Conventions

- Use `Invoke-RestMethod` in PowerShell for raw API calls
- URL-encode queries with `[System.Web.HttpUtility]::UrlEncode()`
- Leaflet maps use CDN build — no server needed, just open HTML in browser
- For Singapore transit details (bus/MRT schedules), use LTA DataMall API (requires free signup at https://datamall.lta.gov.sg)

## HTML Planner Conventions

All `plan-overview.html` files follow this pattern.

### Layout

Two-column flex layout:
- **Left** (`.col-left`, `flex: 1`) — info card, minimap, timeline
- **Right** (`.col-right`, `width: 320px`, `position: sticky`) — preview panel for hover photos
- Responsive: stacks vertically below 900px

### Preview Panel (right side)

Sticky panel shows photo on hover. Stops use `data-img` and `data-caption` attributes:
```html
<div class="stop" data-img="URL" data-caption="Caption text">
  <span class="emoji">💧</span>
  <span class="name">Stop name</span>
  <span class="time">Time</span>
</div>
```
JavaScript listens for `mouseenter`/`mouseleave` to swap the panel content.

### Collapsible Events (main vs sub)

Main events with sub-activities use this structure:
```html
<div class="stop parent" onclick="toggleSub(this)">
  <span class="expand-icon">▶</span>
  <span class="emoji">🛫</span>
  <span class="name">Main Event<span class="sub-count">4 activities</span></span>
  <span class="time">~2 hrs</span>
</div>
<div class="sub-events">
  <div class="stop" data-img="..." data-caption="...">...sub event...</div>
  <div class="stop">...another sub...</div>
</div>
```
- Add `expanded` class to start open: `<div class="stop parent expanded">`
- `toggleSub()` rotates arrow and toggles `.open` on `.sub-events`
- Sub-events indented with left border, slightly darker background

### Day Card Structure

```html
<div class="day-card">
  <div class="day-dot arrive|depart|empty">✈|2</div>
  <div class="day-header">
    <span class="day-num">Day 1</span>
    <span class="day-date">Sat, Dec 26</span>
  </div>
  <div class="day-label">Description</div>
  <!-- stops here -->
</div>
```
- Empty days: add `empty-day` class, use dashed border, reduced opacity
