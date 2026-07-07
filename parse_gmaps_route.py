#!/usr/bin/env python3
"""
Parse Google Maps direction text (copy-paste or PDF) into structured route data
for the trip planner interactive map.

Usage:
  python parse_gmaps_route.py parse "raw_text.txt"
  python parse_gmaps_route.py parse "raw_text.txt" --geocode
  python parse_gmaps_route.py pdf "mapdata.pdf"
  python parse_gmaps_route.py generate "parsed_route.json" --origin-coords lat,lng --dest-coords lat,lng
  python parse_gmaps_route.py full "mapdata.pdf" --origin-coords lat,lng --dest-coords lat,lng
"""

import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ── 1. Parser ──────────────────────────────────────────────────────────────

def parse_gmaps_text(text):
    """
    Parse raw Google Maps direction text into structured leg data.

    Handles the format produced by:
      - Copy-pasting directions from Google Maps web
      - PDF export of Google Maps directions
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    result = {
        "origin": "",
        "destination": "",
        "total_time_min": 0,
        "legs": []
    }

    i = 0
    current_leg = None

    # Extract header: origin → destination + total time
    # Pattern: "Origin to Destination (57 min)" on a single line
    header_match = re.search(
        r'([A-Z][\w\s\&\(\)\-\',\.]+?)\s+to\s+([A-Z][\w\s\&\(\)\-\',\.]+?)\s+\((\d+)\s*min\)',
        text
    )
    if header_match:
        result["origin"] = header_match.group(1).strip()
        result["destination"] = header_match.group(2).strip()
        result["total_time_min"] = int(header_match.group(3))

    while i < len(lines):
        line = lines[i]

        # Time marker: hh:mm AM/PM — start of a new leg
        time_match = re.match(r'^(\d{1,2}:\d{2}(?: ?[AP]M)?)$', line)
        if time_match:
            if current_leg:
                result["legs"].append(current_leg)
            current_leg = {
                "start_time": time_match.group(1).replace("\u202f", " "),
                "mode": "unknown",
                "mode_icon": "❓",
                "duration_min": 0,
                "distance": "",
                "from": "",
                "to": "",
                "instructions": []
            }
            i += 1
            continue

        if current_leg is None:
            i += 1
            continue

        # Location name (bold, usually a station or address)
        # Lines like "Hotel 81 (Premier) Star" or "Aljunied" or "Universal Studios Singapore"
        loc_match = re.match(r'^[A-Z][\w\s&\'\-\.\(\)]+$', line)
        skip_locs = {"Walk", "About", "Use", "Head", "Turn", "Enter", "Exit", "Platform"}
        if loc_match and line not in skip_locs and not line.startswith("About") and not line.startswith("Use"):
            if not current_leg["from"]:
                current_leg["from"] = line
            elif current_leg["from"] != line and current_leg.get("from") != line:
                # Only set "to" if it looks like a location (not a service provider line)
                if not any(x in line for x in ["Service run by", "SBS Transit", "SMRT", "Sentosa"]):
                    if not current_leg["to"] or current_leg["to"] in skip_locs:
                        current_leg["to"] = line

        # Mode detection
        mode_lower = line.lower()
        if mode_lower == "walk" or mode_lower == "walkwalk":
            current_leg["mode"] = "walk"
            current_leg["mode_icon"] = "\U0001f6b6"
        elif "tuas link" in mode_lower or "harbourfront" in mode_lower:
            current_leg["mode"] = "mrt"
            current_leg["mode_icon"] = "\U0001f687"
            # Extract line name
            line_match = re.match(r'(\w[\w\s]+)', line)
            if line_match:
                current_leg["line"] = line_match.group(1).strip()
        elif "sentosa express" in mode_lower:
            current_leg["mode"] = "sentosa"
            current_leg["mode_icon"] = "\U0001f69d"
            dir_match = re.search(r'(Beach Station|Resorts World)', line)
            if dir_match:
                current_leg["direction"] = dir_match.group(1)

        # Duration/distance: "About 13 min, 750 m" or "19 min (7 stops)"
        dur_match = re.search(r'About?\s*(\d+)\s*min', line)
        if dur_match:
            current_leg["duration_min"] = int(dur_match.group(1))

        dist_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(km|m)\b', line)
        if dist_match:
            val_str = dist_match.group(1)
            val = float(val_str.replace(",", ""))
            # Guard: ignore matches where "X min" is parsed as "X m"
            prev_dur = re.search(r'About?\s*(\d+)\s*min', line)
            if not prev_dur or prev_dur.group(1) != dist_match.group(1):
                current_leg["distance"] = dist_match.group(0)

        stops_match = re.search(r'\((\d+)\s+stop', line)
        if stops_match:
            current_leg["stops"] = int(stops_match.group(1))

        # Station codes: "Stop ID: EW9"
        code_match = re.search(r'Stop ID:\s*(\w+\d+)', line)
        if code_match:
            current_leg["station_code"] = code_match.group(1)

        # Platform info
        plat_match = re.search(r'Platform\s+(\w+)', line)
        if plat_match:
            current_leg["platform"] = plat_match.group(1)

        # Walking instructions
        if line.startswith("Head ") or line.startswith("Turn ") or line.startswith("Enter") or line.startswith("Exit"):
            current_leg["instructions"].append(line)

        i += 1

    if current_leg:
        result["legs"].append(current_leg)

    # Post-process: merge consecutive walk legs (Hotel → Walk → Walk → MRT → ...)
    merged = []
    for leg in result["legs"]:
        if merged and leg["mode"] == "walk" and merged[-1]["mode"] == "walk":
            merged[-1]["duration_min"] += leg["duration_min"]
            if leg.get("distance"):
                merged[-1]["distance"] = leg["distance"]
            merged[-1]["to"] = leg.get("to", "")
            merged[-1]["instructions"].extend(leg.get("instructions", []))
        else:
            merged.append(leg)
    result["legs"] = merged

    return result


# ── 2. Geocoding ──────────────────────────────────────────────────────────

def geocode(query):
    """Geocode an address/place name using Nominatim OSM API."""
    import urllib.request
    import urllib.parse

    q = urllib.parse.urlencode({
        "q": query + " Singapore",
        "format": "json",
        "limit": "1"
    })
    url = "https://nominatim.openstreetmap.org/search?" + q
    req = urllib.request.Request(url, headers={"User-Agent": "gmaps-route-importer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lng": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", "")
                }
    except Exception as e:
        return {"error": str(e)}
    return None


def geocode_legs(result):
    """Geocode all unique locations in the parsed route."""
    locations = set()
    for leg in result.get("legs", []):
        if leg.get("from"): locations.add(leg["from"])
        if leg.get("to"): locations.add(leg["to"])
    if result.get("origin"): locations.add(result["origin"])
    if result.get("destination"): locations.add(result["destination"])

    geo = {}
    for loc in sorted(locations):
        coords = geocode(loc)
        geo[loc] = coords
        print(f"  {loc} → {coords.get('lat','?')}, {coords.get('lng','?')}" if coords else f"  {loc} → NOT FOUND")
        import time
        time.sleep(1.1)  # Nominatim rate limit: 1 req/sec

    result["geocoded"] = geo
    return result


# ── 3. HTML Generator ─────────────────────────────────────────────────────

def generate_html(result, origin_coords=None, dest_coords=None):
    """Generate HTML stop elements from parsed route data."""
    lines = []

    if not result.get("legs"):
        return "<!-- No route data -->"

    first_leg = result["legs"][0]
    last_leg = result["legs"][-1]

    origin_name = result.get("origin") or first_leg.get("from", "Origin")
    dest_name = result.get("destination") or last_leg.get("to", "Destination")

    # Build dist summary string
    parts = []
    total_min = 0
    for leg in result["legs"]:
        icon = leg.get("mode_icon", "?")
        label = leg.get("line", leg.get("mode", "")).upper()
        dur = leg.get("duration_min", 0)
        total_min += dur
        if leg["mode"] == "walk":
            parts.append(f"{icon} {dur} ph")
        else:
            parts.append(f"{icon} {label} {dur} ph")

    dist_str = " · ".join(parts) + f" (total ~{total_min} min)"
    if total_min == 0:
        dist_str = f"~{result.get('total_time_min', '?')} min"

    # Origin stop
    if origin_coords:
        lat, lng = origin_coords
        lines.append(f"""    <div class="stop" data-lat="{lat}" data-lng="{lng}" data-location="{origin_name}"
          data-address="{origin_name}"
          data-dist="{dist_str}"
          data-gmaps="https://www.google.com/maps/search/{origin_name.replace(' ', '+')}"
          data-caption="{origin_name}">
      <span class="emoji">🏨</span>
      <span class="name">{origin_name}</span>
      <span class="time">09:00</span>
    </div>""")

    # Destination stop
    if dest_coords:
        lat, lng = dest_coords
        lines.append(f"""    <div class="stop" data-lat="{lat}" data-lng="{lng}" data-location="{dest_name}"
          data-address="{dest_name}"
          data-dist="{dist_str}"
          data-gmaps="https://www.google.com/maps/search/{dest_name.replace(' ', '+')}"
          data-caption="{dest_name}">
      <span class="emoji">🎯</span>
      <span class="name">{dest_name}</span>
      <span class="time">~{total_min} min</span>
    </div>""")

    return "\n".join(lines)


# ── 4. Full Pipeline ──────────────────────────────────────────────────────

def parse_pdf(path):
    """Extract text from a PDF using PyMuPDF."""
    import fitz
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def full_pipeline(pdf_path, origin_coords=None, dest_coords=None):
    """Full pipeline: PDF → parse → geocode → generate HTML."""
    print("=== Step 1: Extract text from PDF ===")
    text = parse_pdf(pdf_path)
    print(f"Extracted {len(text)} chars\n")

    print("=== Step 2: Parse route ===")
    result = parse_gmaps_text(text)
    print(f"Origin: {result.get('origin', '?')}")
    print(f"Destination: {result.get('destination', '?')}")
    print(f"Total time: {result.get('total_time_min', '?')} min")
    print(f"Legs: {len(result.get('legs', []))}")
    for leg in result["legs"]:
        print(f"  {leg.get('mode_icon','?')} {leg.get('mode','?')}: {leg.get('from','?')} → {leg.get('to','?')} ({leg.get('duration_min',0)} min)")
    print()

    print("=== Step 3: Geocode ===")
    result = geocode_legs(result)
    print()

    print("=== Step 4: Generate HTML ===")
    if origin_coords:
        result["origin_coords"] = origin_coords
    if dest_coords:
        result["dest_coords"] = dest_coords
    html = generate_html(result, origin_coords, dest_coords)
    print(html)

    return result


# ── 5. CLI ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse Google Maps direction text into trip planner route data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="cmd")

    p_parse = sub.add_parser("parse", help="Parse raw Google Maps text file")
    p_parse.add_argument("input", help="Path to text file containing Google Maps directions")
    p_parse.add_argument("--geocode", "-g", action="store_true", help="Geocode locations after parsing")
    p_parse.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    p_pdf = sub.add_parser("pdf", help="Parse Google Maps data from PDF")
    p_pdf.add_argument("input", help="Path to PDF file")
    p_pdf.add_argument("--output", "-o", help="Output JSON file")

    p_generate = sub.add_parser("generate", help="Generate HTML stops from parsed JSON")
    p_generate.add_argument("input", help="Path to parsed route JSON")
    p_generate.add_argument("--origin-coords", help="Origin lat,lng (e.g. 1.31155,103.88085)")
    p_generate.add_argument("--dest-coords", help="Destination lat,lng (e.g. 1.25404,103.82381)")

    p_full = sub.add_parser("full", help="Full pipeline: PDF → parse → geocode → generate")
    p_full.add_argument("input", help="Path to PDF file")
    p_full.add_argument("--origin-coords", help="Origin lat,lng")
    p_full.add_argument("--dest-coords", help="Destination lat,lng")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    # Parse command
    if args.cmd == "parse":
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
        result = parse_gmaps_text(text)
        if args.geocode:
            result = geocode_legs(result)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)

    elif args.cmd == "pdf":
        text = parse_pdf(args.input)
        result = parse_gmaps_text(text)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)

    elif args.cmd == "generate":
        with open(args.input, encoding="utf-8") as f:
            result = json.load(f)
        origin = None
        dest = None
        if args.origin_coords:
            origin = tuple(float(x) for x in args.origin_coords.split(","))
        if args.dest_coords:
            dest = tuple(float(x) for x in args.dest_coords.split(","))
        html = generate_html(result, origin, dest)
        print(html)

    elif args.cmd == "full":
        origin = None
        dest = None
        if args.origin_coords:
            origin = tuple(float(x) for x in args.origin_coords.split(","))
        if args.dest_coords:
            dest = tuple(float(x) for x in args.dest_coords.split(","))
        result = full_pipeline(args.input, origin, dest)
        # Also save the full result as JSON
        base = os.path.splitext(args.input)[0]
        out_json = base + "_parsed.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nFull result saved to: {out_json}")


if __name__ == "__main__":
    main()
