#!/usr/bin/env python3
"""
OSM Trip Planner Tools — Free OpenStreetMap APIs for trip planning.
No API keys needed.

Usage:
  python osm_tools.py geocode "Marina Bay Sands Singapore"
  python osm_tools.py reverse 1.2834 103.8607
  python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode driving
  python osm_tools.py matrix "1.2834,103.8607" "1.2817,103.8636" "1.2494,103.8303" --mode driving
  python osm_tools.py poi "Singapore" --type tourism
  python osm_tools.py plan "1.2834,103.8607" "1.2817,103.8636" "1.2494,103.8303" --mode walking
"""

import json
import sys
import time
import urllib.parse
import urllib.request

NOMINATIM = "https://nominatim.openstreetmap.org"
OSRM = "https://router.project-osrm.org"
OVERPASS = "https://overpass-api.de/api/interpreter"

def _fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "osm-trip-planner/1.0"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def geocode(query):
    q = urllib.parse.quote(query)
    data = _fetch(f"{NOMINATIM}/search?q={q}&format=json&addressdetails=1&limit=5")
    if not data:
        print("No results found.")
        return
    for i, r in enumerate(data, 1):
        addr = r.get("address", {})
        print(f"{i}. {r['display_name']}")
        print(f"   Lat: {r['lat']}, Lng: {r['lon']}")
        print(f"   Type: {r.get('type', 'N/A')}, Category: {r.get('category', 'N/A')}")
        print()

def reverse(lat, lng):
    data = _fetch(f"{NOMINATIM}/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1")
    addr = data.get("address", {})
    print(f"Address: {data.get('display_name', 'N/A')}")
    print(f"Lat: {lat}, Lng: {lng}")
    print("Details:")
    for key, val in addr.items():
        print(f"  {key}: {val}")

def route(src, dst, mode="driving"):
    lng1, lat1 = src.split(",")
    lng2, lat2 = dst.split(",")
    profile = {"driving": "driving", "car": "driving", "bike": "cycling", "motorcycle": "driving",
               "foot": "walking", "walking": "walking", "transit": "driving"}.get(mode, mode)
    data = _fetch(f"{OSRM}/route/v1/{profile}/{lng1},{lat1};{lng2},{lat2}?overview=false&steps=true")
    if not data.get("routes"):
        print("No route found.")
        return
    r = data["routes"][0]
    dist_km = r["distance"] / 1000
    time_min = r["duration"] / 60
    print(f"Route ({profile}):")
    print(f"  Distance: {dist_km:.2f} km")
    print(f"  Duration: {time_min:.1f} min")
    legs = r.get("legs", [])
    if legs and legs[0].get("steps"):
        print("  Steps:")
        for step in legs[0]["steps"]:
            inst = step.get("maneuver", {}).get("instruction", step.get("name", ""))
            d = step.get("distance", 0)
            print(f"    - {inst} ({d:.0f}m)")
    print()

def matrix(*coords, mode="driving"):
    profile = {"driving": "driving", "car": "driving", "bike": "cycling", "walking": "walking", "foot": "walking"}.get(mode, mode)
    coords_str = ";".join(c.replace(",", ",") for c in coords)
    data = _fetch(f"{OSRM}/table/v1/{profile}/{coords_str}")
    distances = data.get("distances", [])
    durations = data.get("durations", [])
    labels = [f"Stop {i+1}" for i in range(len(coords))]
    print(f"Distance matrix ({profile}):")
    print(f"{'':<12}", " ".join(f"{l:<14}" for l in labels))
    for i, row in enumerate(distances):
        row_km = [f"{d/1000:<10.1f}km" if d else f"{'--':<10}" for d in row]
        print(f"{labels[i]:<12}", " ".join(row_km))
    print()
    print(f"Duration matrix ({profile}):")
    print(f"{'':<12}", " ".join(f"{l:<14}" for l in labels))
    for i, row in enumerate(durations):
        row_min = [f"{d/60:<10.1f}min" if d else f"{'--':<10}" for d in row]
        print(f"{labels[i]:<12}", " ".join(row_min))
    print()

def poi(area, type_filter="tourism", limit=30):
    query = f'[out:json];area[name="{area}"];node[{type_filter}](area);out center {limit};'
    data = _fetch(f"{OVERPASS}?data={urllib.parse.quote(query)}")
    elements = data.get("elements", [])
    if not elements:
        print(f"No POIs found in '{area}' for type '{type_filter}'.")
        return
    print(f"POIs in {area} (type: {type_filter}):")
    for e in elements[:limit]:
        name = e.get("tags", {}).get("name", "(unnamed)")
        lat = e.get("lat", e.get("center", {}).get("lat", "?"))
        lon = e.get("lon", e.get("center", {}).get("lon", "?"))
        print(f"  {name}: {lat}, {lon}")

def plan(*stops_str, mode="walking"):
    if len(stops_str) < 2:
        print("Need at least 2 stops.")
        return
    profile = {"driving": "driving", "car": "driving", "bike": "cycling", "walking": "walking", "foot": "walking"}.get(mode, mode)
    coords = ";".join(stops_str)
    data = _fetch(f"{OSRM}/route/v1/{profile}/{coords}?overview=false")
    if not data.get("routes"):
        print("No route found.")
        return
    r = data["routes"][0]
    total_km = r["distance"] / 1000
    total_min = r["duration"] / 60
    legs = r.get("legs", [])
    print(f"{'='*50}")
    print(f"TRIP PLAN ({profile})")
    print(f"{'='*50}")
    total_dist = 0
    total_dur = 0
    for i, leg in enumerate(legs):
        seg_km = leg["distance"] / 1000
        seg_min = leg["duration"] / 60
        total_dist += seg_km
        total_dur += seg_min
        print(f"  Stop {i+1} -> Stop {i+2}: {seg_km:.2f} km, {seg_min:.1f} min")
    print(f"{'='*50}")
    print(f"Total: {total_km:.2f} km, {total_min:.1f} min")
    print(f"{'='*50}")
    if legs and legs[0].get("steps"):
        print("Turn-by-turn:")
        for leg in legs:
            for step in leg.get("steps", []):
                inst = step.get("maneuver", {}).get("instruction",
                       step.get("name", ""))
                d = step.get("distance", 0)
                print(f"  - {inst} ({d:.0f}m)")
    print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OSM Trip Planner Tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_geo = sub.add_parser("geocode", help="Address to coordinates")
    p_geo.add_argument("query", help="Address query")

    p_rev = sub.add_parser("reverse", help="Coordinates to address")
    p_rev.add_argument("lat", type=float)
    p_rev.add_argument("lng", type=float)

    p_route = sub.add_parser("route", help="Route between 2 points")
    p_route.add_argument("src", help="lng,lat")
    p_route.add_argument("dst", help="lng,lat")
    p_route.add_argument("--mode", default="driving", help="driving|walking|bike")

    p_matrix = sub.add_parser("matrix", help="Distance matrix for N stops")
    p_matrix.add_argument("coords", nargs="+", help="lng,lat pairs")
    p_matrix.add_argument("--mode", default="driving")

    p_poi = sub.add_parser("poi", help="Search POIs in area")
    p_poi.add_argument("area", help="City/region name")
    p_poi.add_argument("--type", default="tourism", dest="type_filter")
    p_poi.add_argument("--limit", type=int, default=30)

    p_plan = sub.add_parser("plan", help="Multi-stop trip plan")
    p_plan.add_argument("stops", nargs="+", help="lng,lat pairs in order")
    p_plan.add_argument("--mode", default="walking")

    args = parser.parse_args()

    if args.cmd == "geocode":
        geocode(args.query)
    elif args.cmd == "reverse":
        reverse(args.lat, args.lng)
    elif args.cmd == "route":
        route(args.src, args.dst, args.mode)
    elif args.cmd == "matrix":
        matrix(*args.coords, mode=args.mode)
    elif args.cmd == "poi":
        poi(args.area, args.type_filter, args.limit)
    elif args.cmd == "plan":
        plan(*args.stops, mode=args.mode)
