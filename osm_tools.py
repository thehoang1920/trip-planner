#!/usr/bin/env python3
"""
Trip Planner Tools — OSM (free, no key) or Geoapify (free key, more features).

Providers:
  osm       — OpenStreetMap (Nominatim, OSRM, Overpass). No API key needed.
  geoapify  — Geoapify (geocoding, routing, places). Set GEOAPIFY_KEY env var.

Usage:
  python osm_tools.py geocode "Marina Bay Sands Singapore"
  python osm_tools.py geocode "Marina Bay Sands" --provider geoapify
  python osm_tools.py reverse 1.2834 103.8607
  python osm_tools.py reverse 1.2834 103.8607 --provider geoapify
  python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking
  python osm_tools.py route 103.8607,1.2834 103.8636,1.2817 --mode walking --provider geoapify
  python osm_tools.py matrix "103.8607,1.2834" "103.8636,1.2817" --mode driving --provider geoapify
  python osm_tools.py poi "Singapore" --type tourism --provider geoapify
  python osm_tools.py plan "103.8607,1.2834" "103.8636,1.2817" "103.8198,1.3521" --mode walking
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NOMINATIM = "https://nominatim.openstreetmap.org"
OSRM = "https://router.project-osrm.org"
OVERPASS = "https://overpass-api.de/api/interpreter"
GEOAPIFY_V1 = "https://api.geoapify.com/v1"
GEOAPIFY_V2 = "https://api.geoapify.com/v2"

GEOAPIFY_KEY = os.environ.get("GEOAPIFY_KEY", "58ab99b11a52450f93e097c4a0a4accd")

def _fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "osm-trip-planner/1.0"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def _geoapify(path, params, base=GEOAPIFY_V1):
    params["apiKey"] = GEOAPIFY_KEY
    qs = urllib.parse.urlencode(params)
    url = f"{base}/{path}?{qs}"
    return _fetch(url)

def _geoapify_simple(path, params, label="", base=GEOAPIFY_V1):
    try:
        return _geoapify(path, params, base=base)
    except Exception as e:
        print(f"Geoapify error: {e}")
        return None

def _lnglat_to_latlng(pair):
    lng, lat = pair.split(",")
    return f"{lat.strip()},{lng.strip()}"

def geocode_geoapify(query):
    data = _geoapify_simple("geocode/search", {"text": query, "limit": 5, "format": "json"})
    if not data or not data.get("results"):
        print("No results found.")
        return
    for i, r in enumerate(data["results"], 1):
        addr = ", ".join(v for v in [r.get("address_line1"), r.get("address_line2")] if v)
        print(f"{i}. {addr}")
        print(f"   Lat: {r['lat']}, Lng: {r['lon']}")
        print(f"   Country: {r.get('country', 'N/A')}, City: {r.get('city', 'N/A')}")
        print()

def reverse_geoapify(lat, lng):
    data = _geoapify_simple("geocode/reverse", {"lat": lat, "lon": lng, "format": "json"})
    if not data or not data.get("results"):
        print("No results found.")
        return
    r = data["results"][0]
    print(f"Address: {r.get('formatted', 'N/A')}")
    print(f"Lat: {lat}, Lng: {lng}")
    print(f"Country: {r.get('country', 'N/A')}")
    print(f"City: {r.get('city', 'N/A')}")
    print(f"Postcode: {r.get('postcode', 'N/A')}")
    print()

def route_geoapify(src, dst, mode="driving"):
    gmode = {"driving": "drive", "car": "drive", "bike": "bicycle", "motorcycle": "drive",
             "foot": "walk", "walking": "walk", "transit": "drive"}.get(mode, mode)
    wp = f"{_lnglat_to_latlng(src)}|{_lnglat_to_latlng(dst)}"
    data = _geoapify_simple("routing", {
        "waypoints": wp,
        "mode": gmode,
        "details": "instruction_details",
        "units": "metric"
    })
    if not data or not data.get("features"):
        print("No route found.")
        return
    feat = data["features"][0]
    props = feat["properties"]
    dist_m = props.get("distance", 0)
    dist_km = (dist_m / 1000) if isinstance(dist_m, (int, float)) else dist_m.get("value", 0) / 1000
    time_s = props.get("time", 0)
    time_min = (time_s / 60) if isinstance(time_s, (int, float)) else time_s.get("value", 0) / 60
    print(f"Route ({gmode}):")
    print(f"  Distance: {dist_km:.2f} km")
    print(f"  Duration: {time_min:.1f} min")
    legs = props.get("legs", [])
    if legs:
        print("  Steps:")
        for leg in legs:
            for step in leg.get("steps", []):
                inst = step.get("instruction", {}).get("text", "")
                s_dist = step.get("distance", 0)
                d = s_dist if isinstance(s_dist, (int, float)) else s_dist.get("value", 0)
                print(f"    - {inst} ({d:.0f}m)")
    print()

def matrix_geoapify(*coords, mode="driving"):
    gmode = {"driving": "drive", "car": "drive", "bike": "bicycle", "walking": "walk", "foot": "walk"}.get(mode, mode)
    wp = "|".join(_lnglat_to_latlng(c) for c in coords)
    data = _geoapify_simple("matrix", {
        "waypoints": wp,
        "mode": gmode,
        "units": "metric",
        "type": "short"
    })
    if not data or not data.get("sources"):
        print("No matrix data returned.")
        return
    distances = data.get("distances", [])
    durations = data.get("durations", [])
    labels = [f"Stop {i+1}" for i in range(len(coords))]
    print(f"Distance matrix ({gmode}):")
    print(f"{'':<12}", " ".join(f"{l:<14}" for l in labels))
    for i, row in enumerate(distances):
        row_km = [f"{d/1000:<10.1f}km" if d else f"{'--':<10}" for d in row]
        print(f"{labels[i]:<12}", " ".join(row_km))
    print()
    print(f"Duration matrix ({gmode}):")
    print(f"{'':<12}", " ".join(f"{l:<14}" for l in labels))
    for i, row in enumerate(durations):
        row_min = [f"{d/60:<10.1f}min" if d else f"{'--':<10}" for d in row]
        print(f"{labels[i]:<12}", " ".join(row_min))
    print()

def poi_geoapify(area, type_filter="tourism", limit=30):
    cat_map = {"tourism": "tourism", "food": "catering.restaurant", "drink": "catering.pub",
               "museum": "entertainment.museum", "park": "leisure.park",
               "shopping": "commercial", "hotel": "accommodation.hotel"}
    cat = cat_map.get(type_filter, type_filter)
    # Geocode area to get center point for bias
    geo = _geoapify_simple("geocode/search", {"text": area, "limit": 1, "format": "json"})
    if not geo or not geo.get("results"):
        print(f"Could not geocode area '{area}'.")
        return
    center = geo["results"][0]
    bias = f"proximity:{center['lon']},{center['lat']}"
    data = _geoapify_simple("places", {
        "categories": cat,
        "bias": bias,
        "limit": min(limit, 30),
        "format": "json"
    }, base=GEOAPIFY_V2)
    if not data or not data.get("features"):
        print(f"No POIs found near '{area}' for type '{type_filter}'.")
        return
    print(f"POIs near {area} (type: {type_filter}):")
    for e in data["features"][:limit]:
        props = e["properties"]
        name = props.get("name", "(unnamed)")
        lat = props.get("lat", "?")
        lon = props.get("lon", "?")
        addr = props.get("formatted", props.get("address_line1", ""))
        print(f"  {name}: {lat}, {lon}  — {addr}")

def plan_geoapify(*stops_str, mode="walking"):
    if len(stops_str) < 2:
        print("Need at least 2 stops.")
        return
    gmode = {"driving": "drive", "car": "drive", "bike": "bicycle", "walking": "walk", "foot": "walk"}.get(mode, mode)
    wp = "|".join(_lnglat_to_latlng(s) for s in stops_str)
    data = _geoapify_simple("routing", {
        "waypoints": wp,
        "mode": gmode,
        "details": "instruction_details",
        "units": "metric"
    })
    if not data or not data.get("features"):
        print("No route found.")
        return
    feat = data["features"][0]
    props = feat["properties"]
    d_m = props.get("distance", 0)
    total_km = (d_m / 1000) if isinstance(d_m, (int, float)) else d_m.get("value", 0) / 1000
    t_s = props.get("time", 0)
    total_min = (t_s / 60) if isinstance(t_s, (int, float)) else t_s.get("value", 0) / 60
    print(f"{'='*50}")
    print(f"TRIP PLAN ({gmode})")
    print(f"{'='*50}")
    legs = props.get("legs", [])
    for i, leg in enumerate(legs):
        d_m2 = leg.get("distance", 0)
        seg_km = (d_m2 / 1000) if isinstance(d_m2, (int, float)) else d_m2.get("value", 0) / 1000
        t_s2 = leg.get("time", 0)
        seg_min = (t_s2 / 60) if isinstance(t_s2, (int, float)) else t_s2.get("value", 0) / 60
        print(f"  Stop {i+1} -> Stop {i+2}: {seg_km:.2f} km, {seg_min:.1f} min")
    print(f"{'='*50}")
    print(f"Total: {total_km:.2f} km, {total_min:.1f} min")
    print(f"{'='*50}")
    if legs:
        print("Turn-by-turn:")
        for leg in legs:
            for step in leg.get("steps", []):
                inst = step.get("instruction", {}).get("text", "")
                s_d = step.get("distance", 0)
                d = s_d if isinstance(s_d, (int, float)) else s_d.get("value", 0)
                print(f"  - {inst} ({d:.0f}m)")
    print()

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
    p_geo.add_argument("--provider", default="osm", choices=["osm", "geoapify"],
                       help="API provider (default: osm)")

    p_rev = sub.add_parser("reverse", help="Coordinates to address")
    p_rev.add_argument("lat", type=float)
    p_rev.add_argument("lng", type=float)
    p_rev.add_argument("--provider", default="osm", choices=["osm", "geoapify"])

    p_route = sub.add_parser("route", help="Route between 2 points")
    p_route.add_argument("src", help="lng,lat")
    p_route.add_argument("dst", help="lng,lat")
    p_route.add_argument("--mode", default="driving", help="driving|walking|bike")
    p_route.add_argument("--provider", default="osm", choices=["osm", "geoapify"])

    p_matrix = sub.add_parser("matrix", help="Distance matrix for N stops")
    p_matrix.add_argument("coords", nargs="+", help="lng,lat pairs")
    p_matrix.add_argument("--mode", default="driving")
    p_matrix.add_argument("--provider", default="osm", choices=["osm", "geoapify"])

    p_poi = sub.add_parser("poi", help="Search POIs in area")
    p_poi.add_argument("area", help="City/region name")
    p_poi.add_argument("--type", default="tourism", dest="type_filter")
    p_poi.add_argument("--limit", type=int, default=30)
    p_poi.add_argument("--provider", default="osm", choices=["osm", "geoapify"])

    p_plan = sub.add_parser("plan", help="Multi-stop trip plan")
    p_plan.add_argument("stops", nargs="+", help="lng,lat pairs in order")
    p_plan.add_argument("--mode", default="walking")
    p_plan.add_argument("--provider", default="osm", choices=["osm", "geoapify"])

    args = parser.parse_args()

    if args.cmd == "geocode":
        if args.provider == "geoapify":
            geocode_geoapify(args.query)
        else:
            geocode(args.query)
    elif args.cmd == "reverse":
        if args.provider == "geoapify":
            reverse_geoapify(args.lat, args.lng)
        else:
            reverse(args.lat, args.lng)
    elif args.cmd == "route":
        if args.provider == "geoapify":
            route_geoapify(args.src, args.dst, args.mode)
        else:
            route(args.src, args.dst, args.mode)
    elif args.cmd == "matrix":
        if args.provider == "geoapify":
            matrix_geoapify(*args.coords, mode=args.mode)
        else:
            matrix(*args.coords, mode=args.mode)
    elif args.cmd == "poi":
        if args.provider == "geoapify":
            poi_geoapify(args.area, args.type_filter, args.limit)
        else:
            poi(args.area, args.type_filter, args.limit)
    elif args.cmd == "plan":
        if args.provider == "geoapify":
            plan_geoapify(*args.stops, mode=args.mode)
        else:
            plan(*args.stops, mode=args.mode)
