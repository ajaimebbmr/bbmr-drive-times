import requests, json, os
from datetime import datetime, timezone

KEY = os.environ["TOMTOM_KEY"]

# ── OVERRIDES ──────────────────────────────────────────────────────────────────
# This is the manual control panel. Change status to "open" when a road reopens.
# Add or remove a message for any route by changing the text (or setting to None).
# ──────────────────────────────────────────────────────────────────────────────
OVERRIDES = {
    "330":  { "status": "open",   "message": None },
    "18rs": { "status": "open",   "message": None },
    "38":  { "status": "open", "message": None },
    "18lv": { "status": "open",   "message": None },
}

# ── ORIGIN ─────────────────────────────────────────────────────────────────────
# Snow Summit / Bear Mountain base area.
# Swap this for the Snow Valley coordinates when building the SV feed.
ORIGIN = "34.237021,-116.888654"

# ── ROUTES ─────────────────────────────────────────────────────────────────────
# Waypoints pin the route to a specific road so TomTom can't pick a shortcut.
# If a drive time looks wrong after launch, nudge the waypoint coordinates on
# Google Maps until it follows the right road.
# ──────────────────────────────────────────────────────────────────────────────
ROUTES = [
    {
        "id": "330",
        "headline": "To 210 Freeway",
        "via": "via CA-18 Running Springs to CA-330",
        "desc": "Toward Highland · LA / OC / Inland Empire",
        "waypoints": ["34.164402, -117.182765"],
        "dest": "34.131517, -117.201018",
    },
    {
        "id": "18rs",
        "headline": "To 210 Freeway",
        "via": "via CA-18 through Running Springs",
        "desc": "Toward Crestline & San Bernardino",
        "waypoints": ["34.227517, -117.272656"],
        "dest": "34.145807, -117.278808",
    },
    {
        "id": "38",
        "headline": "To 10 Freeway",
        "via": "via CA-38",
        "desc": "Toward Angelus Oaks & Redlands",
        "waypoints": ["34.099401, -117.026577"],
        "dest": "34.070172, -117.182595",
    },
    {
        "id": "18lv",
        "headline": "To 15 Freeway",
        "via": "via CA-18 Lucerne Valley",
        "desc": "The back way · High Desert & Las Vegas",
        "waypoints": ["34.47197002629797, -117.09936486651272"],
        "dest": "34.470457, -117.346081",
    },
]

def round5(minutes):
    """Round to nearest 5 — avoids implying false precision on the board."""
    return round(minutes / 5) * 5

def fetch_times(route):
    locations = ":".join([ORIGIN] + route["waypoints"] + [route["dest"]])
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"
    r = requests.get(url, params={
        "key": KEY,
        "traffic": "true",
        "computeTravelTimeFor": "all",
        "travelMode": "car"
    }, timeout=15)
    r.raise_for_status()
    summary = r.json()["routes"][0]["summary"]
    return {
        "minutes": round5(summary["travelTimeInSeconds"] / 60),
        "typical": round5(summary["noTrafficTravelTimeInSeconds"] / 60),
    }

results = []
for route in ROUTES:
    override = OVERRIDES[route["id"]]
    row = {
        "headline": route["headline"],
        "via":      route["via"],
        "desc":     route["desc"],
    }

    if override["status"] == "closed":
        row["status"]  = "closed"
        row["message"] = override["message"]
        print(f"  — {route['id']}: CLOSED (override)")
    else:
        try:
            times = fetch_times(route)
            row["status"]  = "open"
            row["minutes"] = times["minutes"]
            row["typical"] = times["typical"]
            if override["message"]:
                row["message"] = override["message"]
            print(f"  ✓ {route['id']}: {times['minutes']} min (typical {times['typical']} min)")
        except Exception as e:
            print(f"  ✗ {route['id']}: API call failed — {e}")
            row["status"] = "unknown"

    results.append(row)

output = {
    "updatedAt": datetime.now(timezone.utc).isoformat(),
    "routes": results
}

with open("routes.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nroutes.json written successfully.")
