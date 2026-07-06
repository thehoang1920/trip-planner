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

### Wishlist Sub-Event / Location Block Pattern

When multiple wishlist items share the same address, merge them into a single `.wl-location-block`. This keeps the 2-column grid intact while grouping sub-events.

```html
<div class="wl-location-block">
  <div class="wl-card parent expanded" onclick="toggleSub(this)" data-address="..." data-dist="..." data-gmaps="..." data-img="..." data-caption="Location Overview">
    <span class="expand-icon">▶</span>
    <span class="wl-emoji">🎢</span>
    <div class="wl-info">
      <div class="wl-name">Location Name <span class="sub-count">3 hoạt động</span></div>
      <div class="wl-loc">Address</div>
      <div class="wl-dist">Distance info</div>
      <div class="wl-coord">1.2542, 103.8227</div>
      <div class="wl-link"><a href="..." target="_blank">Xem trên Google Maps</a></div>
    </div>
  </div>
  <div class="wl-sub-events open">
    <div class="wl-card" data-address="..." data-dist="..." data-time="..." data-price="..." data-img="..." data-video="..." data-caption="Event 1 Caption">
      <span class="wl-emoji">🎢</span>
      <div class="wl-info">
        <div class="wl-name">Event 1</div>
        <div class="wl-time">🕐 Operating hours</div>
        <div class="wl-price">💰 Price</div>
        <div class="wl-event-desc">Detailed description of the event.</div>
        <div class="wl-video-btn">▶ Xem video</div>
      </div>
    </div>
  </div>
</div>
```

CSS:
```css
.wl-location-block { background: #0f172a; border-radius: 8px; border: 1px solid #334155; overflow: hidden; }
.wl-location-block .wl-card.parent { background: transparent; border: none; border-radius: 0; padding: 12px 12px 4px; margin: 0; cursor: pointer; display: flex; align-items: flex-start; }
.wl-location-block .wl-card.parent .expand-icon { font-size: 0.7rem; color: #64748b; width: 16px; text-align: center; transition: transform .2s; flex-shrink: 0; display: inline-block; vertical-align: middle; }
.wl-location-block .wl-card.parent.expanded .expand-icon { transform: rotate(90deg); }
.wl-location-block .wl-sub-events { display: none; padding-left: 10px; margin: 0 6px 6px 16px; border-left: 2px solid #334155; }
.wl-location-block .wl-sub-events.open { display: block; }
.wl-location-block .wl-sub-events .wl-card { background: #1a2638; font-size: 0.82rem; padding: 10px 12px; margin-bottom: 6px; }
.wl-location-block .wl-sub-events .wl-card:hover { background: #23304a; }
```

Key points:
- `.wl-location-block` is a single grid item in `.wishlist-grid` (2-column layout)
- Parent `.wl-card.parent` has location info + `onclick="toggleSub(this)"` for expand/collapse
- `.wl-sub-events` is a sibling (not child) of `.wl-card.parent` — `toggleSub()` uses `el.nextElementSibling`
- Each sub-event `.wl-card` has its own data-img, data-caption, data-video, data-time, data-price — independently hoverable/clickable
- Parent `.wl-card` has data-img/data-caption for location overview (used by map marker clicks)
- Sub-event `.wl-card` elements do NOT have `.wl-coord` — they inherit the marker from the parent
- `toggleSub()` function checks for both `sub-events` and `wl-sub-events` classes:
  ```js
  function toggleSub(el) {
    el.classList.toggle('expanded');
    const sub = el.nextElementSibling;
    if (sub && (sub.classList.contains('sub-events') || sub.classList.contains('wl-sub-events'))) {
      sub.classList.toggle('open');
    }
  }
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
| `data-video` | `.wl-card`, `.food-card`, `.wl-video-btn` | YouTube URL for video preview |
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
let activeVideoUrl = null;    // Video URL for per-button video (overrides card's data-video)
```

**Declared ONCE — duplicate `let` in same `<script>` block causes SyntaxError.**

### showPreview(el, type)

```js
function showPreview(el, type) {
  if (type !== 'video') activeVideoUrl = null;
  const videoUrl = activeVideoUrl || el.dataset.video;
  const useVideo = type === 'video' && videoUrl;
  currentPreviewEl = el;
  // Destroy old iframe
  if (previewYoutube) { previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null; }
  previewYoutubeContainer.style.display = 'none';

  if (useVideo) {
    // Create YouTube iframe
    const ytId = getYoutubeId(videoUrl);
    previewYoutube = document.createElement('iframe');
    previewYoutube.className = 'preview-img';
    previewYoutube.allow = 'autoplay; encrypted-media; fullscreen';
    previewYoutube.allowfullscreen = true;
    previewYoutube.src = 'https://www.youtube-nocookie.com/embed/' + ytId + '?autoplay=1&rel=0&playsinline=1';
    previewYoutubeContainer.appendChild(previewYoutube);
    previewYoutubeContainer.style.display = 'block';
  } else {
    previewImg.src = el.dataset.img;
    previewImg.style.display = 'block';
  }

  // Update info
  previewName.textContent = el.dataset.caption || '';
  previewVideoBtn.style.display = videoUrl && type !== 'video' ? 'block' : 'none';
  previewVideoBtn._lastEl = videoUrl ? el : null;
  previewInfo.style.display = 'block';
}
```

`activeVideoUrl` allows multiple `.wl-video-btn` within one card to use different video URLs. Set in click handler via `videoBtn.dataset.video || card.dataset.video`.

### hidePreview()

```js
function hidePreview() {
  activeVideoUrl = null;
  if (pinnedEl) { showPreview(pinnedEl, pinnedMode); return; }
  pinnedMode = 'image';
  if (previewYoutube) { previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null; }
  previewYoutubeContainer.style.display = 'none';
  previewPlaceholder.style.display = 'flex';
  previewInfo.style.display = 'none';
}
```

### Map Click/Unpin — mousedown catches drags

`map.on('click', ...)` does NOT fire when Leaflet detects a drag (mousedown + mousemove). Use `mousedown` to catch all map interactions:

```js
map.on('click', function() {
  pinnedEl = null;
  pinnedMode = 'image';
  hidePreview();
});
map.on('mousedown', function() {
  if (pinnedEl) {
    pinnedEl = null;
    pinnedMode = 'image';
    hidePreview();
  }
});
```

- `mousedown` fires immediately on mouse press, before Leaflet's drag detection (catches both clicks and drags)
- `click` fires only for non-drag clicks (redundant with mousedown but kept for safety)
- **No `ignoreMapClick`** — Leaflet markers stop propagation, they don't fire map events

### Card Click — Consolidated Handler (video button + card body)

Merge video-button and card-body clicks into ONE `addEventListener` per card. Use `e.target.closest()` to distinguish, avoiding `stopPropagation` race conditions:

```js
el.addEventListener('click', function(e) {
  clearTimeout(hideTimeout);  // ← prevent stale mouseout timer
  const videoBtn = e.target.closest('.wl-video-btn, .food-video-btn');
  if (videoBtn) {
    const card = this;
    activeVideoUrl = videoBtn.dataset.video || card.dataset.video;
    if (pinnedEl === card && pinnedMode === 'video') {
      pinnedEl = null; pinnedMode = 'image'; hidePreview();
    } else {
      if (pinnedEl && pinnedEl !== card) { pinnedEl = null; pinnedMode = 'image'; }
      pinnedEl = card; pinnedMode = 'video';
      showPreview(card, 'video');
    }
  } else {
    pinnedEl = this; pinnedMode = 'image';
    showPreview(this, 'image');
  }
});
```

This pattern must be applied via one query selector that matches ALL interactive card types:
```js
document.querySelectorAll('.stop[data-img], .wl-card[data-img], .food-card[data-img]')
```

There is NO separate `document.querySelectorAll('.wl-video-btn, .food-video-btn')` — all video button clicks are handled by this consolidated card handler. Adding separate handlers causes race conditions between the two.

### Marker Click — Pin Image

```js
m.on('click', function() {
  pinnedEl = card;
  pinnedMode = 'image';  // ← CRITICAL: reset to image
  showPreview(card);
});
```

`clearTimeout(hideTimeout)` not needed here (marker click has no DOM-level timeout) but `pinnedMode = 'image'` is mandatory.

### Marker Mouseover/Mouseout

```js
m.on('mouseover', () => { if (pinnedEl) return; clearTimeout(hideTimeout); showPreview(card); });
m.on('mouseout', () => { if (pinnedEl) return; hideTimeout = setTimeout(hidePreview, 150); });
```

Preview panel cancels timeout on mouseenter, hides on mouseleave (if unpinned).

### Video Button — Card Level (NO separate handler)

Video buttons are handled INSIDE the card's consolidated click handler via `e.target.closest('.wl-video-btn, .food-video-btn')`. Do NOT add separate `document.querySelectorAll('.wl-video-btn, .food-video-btn')` handlers — they create a race condition where the card handler and video handler both run.

```html
<div class="wl-video-btn">▶ Xem video</div>
<!-- No JS handler needed — the card's consolidated click handles it -->
```

### Video Button — Preview Panel (`#previewVideoBtn`)

```html
<div id="previewVideoBtn" style="display:none; margin-top:6px;">
  <span style="display:inline-block; font-size:0.7rem; color:#ef4444; background:#2d1a1a; border:1px solid #ef4444; border-radius:4px; padding:1px 8px; cursor:pointer; transition:all .15s;">▶ Xem video</span>
</div>
```

**Must NOT use `wl-video-btn` class** — the global selector creates a duplicate click handler.

```js
// Click handler
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

// Hover effect — CSS :hover on nested &lt;span&gt; can be unreliable; use JS instead
previewVideoBtn.addEventListener('mouseenter', function() {
  const s = this.querySelector('span');
  if (s) { s.style.background = '#ef4444'; s.style.color = '#fff'; }
});
previewVideoBtn.addEventListener('mouseleave', function() {
  const s = this.querySelector('span');
  if (s) { s.style.background = '#2d1a1a'; s.style.color = '#ef4444'; }
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
| Click video btn (diff) | changed | `'video'` | Plays new video |
| Click blank map | null | `'image'` | Hides everything |
| Map mousedown (drag) | null | `'image'` | Hides everything |

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

#### Route Rendering — Draw Day Route

```js
async function drawDayRoute(stops, completedUpTo) {
  const token = ++activeRouteToken;
  const legendEl = document.getElementById('routeLegend');
  legendEl.innerHTML = '<span class="legend-title">Tuyến tối ưu:</span><span class="route-loading">⏳ Đang tính...</span>';
  legendEl.style.display = 'flex';
  clearRoute();
  if (!stops || stops.length < 2) { legendEl.style.display = 'none'; return; }

  const legs = [];
  for (let i = 0; i < stops.length - 1; i++) {
    if (i < completedUpTo) { legs.push(null); continue; } // skip completed
    const from = stops[i], to = stops[i + 1];
    const segs = await getOptimalRoute(from.lat, from.lng, to.lat, to.lng);
    if (token !== activeRouteToken) return;
    legs.push({ fromStopIdx: i, segments: segs });
  }

  // Flatten + draw all non-completed segments
  const allSegments = [];
  for (const leg of legs) {
    if (!leg) continue;
    for (const s of leg.segments) allSegments.push(s);
  }
  // ... draw polylines on routeLayer, add tooltips
  routeLayer.addTo(map);
  currentRouteLayer = routeLayer;
  buildRouteLegend(allSegments);
  map.fitBounds(allCoords, { padding: [40, 40], maxZoom: 14 });
  updateMarkerIcons(activeDay);
}
```

### Completion Checkmarks (○/✓)

Each stop marker shows a clickable ○/✓ button to track progress:

```js
// Marker creation
var iconHtml = '<span class="num">' + stopNum + '</span><span class="chk" data-toggle="1">○</span>';
const icon = L.divIcon({ className: 'num-marker', html: iconHtml, iconSize: [32, 26], iconAnchor: [16, 13] });
const m = L.marker([lat, lng], { icon: icon }).bindTooltip(stopNum + '. ' + loc, { direction: 'top' });

// Click handler checks if target is .chk
m.on('click', function(e) {
  if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.classList.contains('chk')) {
    toggleComplete(m, dayNum);
    return;
  }
  pinnedEl = s; pinnedMode = 'image'; showPreview(s);
});
m._stopIdx = stopNum - 1;
```

```js
function toggleComplete(m, dayNum) {
  var st = routeState[dayNum];
  var target = m._stopIdx;
  if (st.completedUpTo === target) st.completedUpTo = Math.max(0, target - 1);
  else st.completedUpTo = target;
  clearRoute();
  drawDayRoute(st.stops, st.completedUpTo);
}
```

Marker icon states:
- **○** = not yet reached
- **●** = current stop (in progress)
- **✓** = completed (route segment before this stop is hidden)

CSS:
```css
.num-marker { background: #fbbf24; width: 32px; height: 26px; display: flex; align-items: center; justify-content: center; }
.num-marker .chk { cursor: pointer; font-size: 0.7rem; opacity: 0.4; user-select: none; }
.num-marker .chk:hover { opacity: 1; }
.num-marker.done { background: #334155; border-color: #22c55e; }
.num-marker.done .chk { opacity: 1; color: #22c55e; }
.num-marker.current { background: #fbbf24; border-color: #3b82f6; }
```

### Route Legend

```js
function buildRouteLegend(segments) {
  container.innerHTML = '<span class="legend-title">Tuyến tối ưu:</span>';
  for (const mode of modeOrder) {
    if (!modeSet[mode]) continue;
    // Show ████ colored line + mode label for each mode present
  }
  // Total distance/time
  total.textContent = 'Tổng: ' + formatDist(totalDist) + ' · ' + formatDur(totalDur);
}
```

---

## Routing Engine — Complete Reference

This section documents the multi-mode routing system built for the Singapore 2026 planner. Use this as a template for future trips.

### Architecture Overview

The routing system is embedded entirely in the HTML planner. It provides:
1. **MRT station DB** with BFS pathfinding (Singapore MRT/LRT network)
2. **Sentosa Express monorail** as an extension of the MRT network
3. **Optimal route engine** with priority: MRT > Bus > Walking > Car
4. **OSRM integration** for real road/walking geometry
5. **Route cache** to avoid redundant API calls
6. **Stale-request guard** using incrementing token (prevents race conditions)

### MRT Station Database

```js
const S = {}; // stations keyed by station code
const C = {}; // connections (adjacency list)

function addStation(code, name, lat, lng) {
  S[code] = { code, name, lat, lng };
  if (!C[code]) C[code] = [];
}

function connect(c1, c2) {
  if (!C[c1].includes(c2)) C[c1].push(c2);
  if (!C[c2].includes(c1)) C[c2].push(c1);
}
```

**Station format:** `{ code: 'EW9', name: 'Aljunied', lat: 1.3164, lng: 103.8834 }`

**Code convention:** 2-letter line prefix + number (e.g., `EW9` = East-West line, station 9; `NE1` = North-East line, station 1; `CC3` = Circle line, station 3; `CG2` = Changi Airport branch; `SE1` = Sentosa Express).

### BFS Route Finder

```js
function findMRT(fromCode, toCode) {
  const q = [[fromCode]];
  const visited = new Set([fromCode]);
  while (q.length) {
    const path = q.shift();
    const last = path[path.length - 1];
    for (const n of (C[last] || [])) {
      if (visited.has(n)) continue;
      visited.add(n);
      const newPath = path.concat([n]);
      if (n === toCode) return newPath;
      q.push(newPath);
    }
  }
  return null; // no path found
}
```

Returns array of station codes representing the shortest path, or `null` if unreachable.

### Nearest Station

```js
function nearestStation(lat, lng) {
  let best = null, bestDist = Infinity;
  for (const code in S) {
    const s = S[code];
    const d = (s.lat - lat) ** 2 + (s.lng - lng) ** 2;
    if (d < bestDist) { bestDist = d; best = code; }
  }
  return best;
}
```

Simple Euclidean distance (squared) — sufficient for station proximity checks (not for distance measurement).

### MRT Lines Covered

| Line | Codes | Stations |
|------|-------|----------|
| East-West (main) | EW4–EW19 | Tanah Merah → Queenstown + interchanges |
| Changi Branch | CG1–CG2 | Tanah Merah → Changi Airport |
| Circle Line | CC1–CC3, CC8–CC9 | Outram Park → HarbourFront, Dakota → Paya Lebar |
| North-East | NE1, NE3–NE6 | HarbourFront → Dhoby Ghaut |
| North-South | NS22, NS24–NS25, NS27–NS28 | Orchard → Marina Bay |
| Downtown | DT16–DT20 | Bayfront → Marina Bay |
| Sentosa Express | SE1–SE3 | Waterfront → Imbiah → Beach (connected to NE1 HarbourFront) |

### Sentosa Express (Special)

The Sentosa Express monorail is added as MRT stations (`SE1`, `SE2`, `SE3`) connected to HarbourFront MRT (`NE1`):

```js
addStation('SE1','Waterfront Sentosa',1.2546,103.8206);
addStation('SE2','Imbiah',1.2528,103.8137);
addStation('SE3','Beach Sentosa',1.2505,103.8200);
connect('NE1','SE1');
connect('SE1','SE2');
connect('SE2','SE3');
```

This means Universal Studios Singapore (nearest station: SE1 Waterfront, ~240m) automatically routes via Sentosa Express instead of walking 1.2km from HarbourFront MRT.

### OSRM Route Fetching

```js
async function fetchRoute(profile, coords) {
  const url = 'https://router.project-osrm.org/route/v1/' + profile + '/'
    + coords.map(c => c[1] + ',' + c[0]).join(';')
    + '?geometries=geojson&overview=full';
  const controller = new AbortController();
  const timer = setTimeout(function() { controller.abort(); }, 8000);
  // ...
}
```

**IMPORTANT — Do NOT use `AbortSignal.timeout()`:** Not supported in legacy browsers. Use manual `AbortController` + `setTimeout` pattern.

**Profiles:**
- `walking` — used for actual walking + MRT track geometry (approximated via walking path)
- `driving` — used for bus and car routes (buses follow roads)

**Caching:** Routes are cached in `routeCache` by `profile|coord1,coord2;coord3,coord4` key to avoid redundant API calls. Pending requests are tracked in `pendings` to deduplicate concurrent identical requests.

### Haversine Distance

```js
function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLng/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
```

Returns distance in meters.

### Format Helpers

```js
function formatDist(m) {
  if (!m) return '?';
  return (m / 1000).toFixed(1) + ' km';
}

function formatDur(s) {
  if (!s) return '?';
  const m = s / 60;
  if (m < 60) return Math.round(m) + ' min';
  const h = Math.floor(m / 60);
  const min = Math.round(m % 60);
  return h + 'h ' + min + 'min';
}
```

### Optimal Route Engine

```js
async function getOptimalRoute(fromLat, fromLng, toLat, toLng) {
  const directDist = haversine(fromLat, fromLng, toLat, toLng);
```

**Priority order:**

1. **MRT** (if stations within 2km of both ends):
   - Walk from origin → first station (yellow dashed)
   - MRT through stations (green solid, OSRM walking profile for geometry)
   - Walk from last station → destination (yellow dashed)
   
2. **Bus** (if direct distance > 300m):
   - Single segment using OSRM driving profile (blue dashed)

3. **Walking** (always available):
   - Single straight line from origin → destination (yellow dashed)
   
4. **Car** (last resort):
   - Single segment using OSRM driving profile (purple solid)

**Returns:** Array of `{ mode, coords, distance, duration }` objects.

### Route Segment Styles

```js
const SEG_STYLES = {
  mrt:  { color: '#22c55e', weight: 5, dash: '',       label: 'MRT',      icon: '🚇' },
  walk: { color: '#eab308', weight: 3, dash: '4,4',    label: 'Walking',  icon: '🚶' },
  bus:  { color: '#3b82f6', weight: 3, dash: '8,4',    label: 'Bus',      icon: '🚌' },
  car:  { color: '#a855f7', weight: 3, dash: '',       label: 'Car/Taxi', icon: '🚗' }
};
```

- Solid lines = MRT, Car
- Dashed lines = Walking (4,4), Bus (8,4)
- MRT is boldest (weight: 5)

### Stale Request Guard

```js
let activeRouteToken = 0;

async function drawDayRoute(stops, completedUpTo) {
  const token = ++activeRouteToken;
  // ... fetch routes in loop ...
  if (token !== activeRouteToken) return; // stale check after each await
}
```

Each day-click generates a new token. If a previous async `getOptimalRoute` resolves after a newer click, the stale result is discarded. This prevents race conditions when rapidly switching days.

### Adding to a New Trip

1. Define MRT stations using `addStation()` + `connect()` for Singapore's network
2. Add any special transit (like Sentosa Express) as stations connected to the nearest MRT
3. Copy `getOptimalRoute()`, `SEG_STYLES`, `fetchRoute()`, `haversine()`, `formatDist()`, `formatDur()`, `nearestStation()`, `findMRT()`
4. Copy `drawDayRoute()`, `buildRouteLegend()`, `clearRoute()`, `toggleComplete()`, `updateMarkerIcons()`
5. Add `routeState`, `dayMarkers`, `activeDay`, `activeRouteToken`, `currentRouteLayer` state variables
6. Hook the day click handler to call `drawDayRoute(stopData, 0)` when expanding a day

---

## Common Bugs — Lessons Learned

1. **Duplicate `let` declarations** — causes SyntaxError, entire script fails.
2. **`ignoreMapClick` flag** — unnecessary (Leaflet markers don't fire map click), causes first map-click to be silently dropped.
3. **`pinnedMode` not reset on marker click** — video button sees `pinnedEl === el && pinnedMode === 'video'` and toggles off instead of playing. Always set `pinnedMode = 'image'` after non-video clicks.
4. **Preview panel button class collision** — `<span class="wl-video-btn">` inside `#previewVideoBtn` matches global selector, creates duplicate handler. Use plain text instead.
5. **`display:none` buttons not clickable** — ensure button is visible (`display:block`) before users can click it.
6. **Iframe not destroyed** — old video continues audio after unpin. Always do `previewYoutube.src = ''; previewYoutube.remove(); previewYoutube = null;` in both showPreview and hidePreview.
7. **CSS `:hover` on nested span unreliable** — `#previewVideoBtn span:hover` may not work consistently. Use JS `mouseenter`/`mouseleave` events to toggle inline background/color instead.
8. **Separate video button handlers cause race conditions** — Card-level video buttons (`wl-video-btn`, `food-video-btn`) MUST NOT have their own event listeners. Merge into the card's single click handler via `e.target.closest('.wl-video-btn, .food-video-btn')`. A separate handler with `e.stopPropagation()` fights the card handler and produces intermittent failures.
9. **`map.on('click', ...)` doesn't fire for drags** — Leaflet suppresses `click` events when mousedown + mousemove is detected (a drag). Add `map.on('mousedown', ...)` which fires before drag detection. This is the correct way to catch ALL map interactions including drags.
10. **Stale `hideTimeout` fires after click** — A 150ms `setTimeout` from a previous `mouseout` on a card/marker can fire `hidePreview()` milliseconds after a click handler sets new state, showing the placeholder. Fix: `clearTimeout(hideTimeout)` at the top of every click handler.
11. **Document-level handlers are unnecessary** — Map `mousedown` + map `click` + card/marker click handlers cover all blank-area unpin scenarios. Document-level `click`/`mouseup` handlers add complexity and potential bugs (e.g., excluding `.leaflet-container` prevents map drag detection).
12. **Console logging for debugging** — When a bug's root cause is unclear, add `console.log` traces at every key decision point (`showPreview`, `hidePreview`, each click handler) to trace the exact code path. This is faster than guessing.
13. **`data-video` on `.wl-video-btn` ignored** — If the click handler only reads `card.dataset.video`, video buttons with their own `data-video` attribute won't work. Fix: `activeVideoUrl = videoBtn.dataset.video || card.dataset.video;` and pass `activeVideoUrl` to `showPreview()`.
14. **Parent card hover conflicts with sub-event hover** — If both parent `.wl-card.parent` and sub-event `.wl-card` have `data-img`, mouseleave from a sub-event calls `hidePreview()` even if still inside the parent. Acceptable UX — sub-events show their own preview, and moving between sub-events briefly shows placeholder. Parent's `data-img` is needed for map marker click previews.
15. **`wl-sub-events` not found by `toggleSub`** — The `toggleSub` function checks for `sub-events` class. If you use a different class like `wl-sub-events`, update the check to `sub.classList.contains('sub-events') || sub.classList.contains('wl-sub-events')`.
16. **Grid layout broken by parent/sub siblings** — `.wl-card.parent` and `.wl-sub-events` are separate grid items in `.wishlist-grid`. Without `grid-column: 1 / -1`, they occupy separate columns. Fix: wrap both in `.wl-location-block` which is a single grid item (no special grid-column needed).
17. **Map marker creates duplicate preview for sub-event cards** — Sub-event `.wl-card` elements don't have `.wl-coord`, so the marker loop (`document.querySelectorAll('.wl-card')`) skips them. Only the parent `.wl-card` creates a map marker, which correctly shows the location overview on click.

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
   - If multiple items share the same address, merge into a `.wl-location-block` with sub-events (see "Wishlist Sub-Event / Location Block Pattern" above)
9. Add food section with cards
10. Add `.nojekyll` at repo root
11. Commit + push
