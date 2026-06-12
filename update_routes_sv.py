import requests, json, os
from datetime import datetime, timezone

KEY = os.environ["TOMTOM_KEY"]

# ── OVERRIDES ──────────────────────────────────────────────────────────────────
OVERRIDES = {
    "330":  { "status": "open", "message": None },
    "18rs": { "status": "open", "message": None },
    "38":   { "status": "open", "message": None },
    "18lv": { "status": "open", "message": None },
}

# ── ORIGIN ─────────────────────────────────────────────────────────────────────
# Snow Valley Mountain Resort — Running Springs, CA
ORIGIN = "34.2246,-117.0362"

# ── ROUTES ─────────────────────────────────────────────────────────────────────
# Snow Valley sits right at the CA-18 / CA-330 junction, so routes 330 and 18rs
# are short and direct. Routes 38 and 18lv require backtracking east through
# Big Bear — waypoints force that path. Remove them if they're not useful to
# show guests from this base.
# ──────────────────────────────────────────────────────────────────────────────
ROUTES = [
    {
        "id": "330",
        "headline": "To 210 Freeway",
        "via": "via CA-330",
        "desc": "Toward Highland · LA / OC / Inland Empire",
        "waypoints": ["34.1900,-117.1400"],
        "dest": "34.136158,-117.191792",
    },
    {
        "id": "18rs",
        "headline": "To 210 Freeway",
        "via": "via CA-18 through Running Springs",
        "desc": "Toward Crestline & San Bernardino",
        "waypoints": ["34.2300,-117.1200"],
        "dest": "34.147017,-117.279029",
    },
    {
        "id": "38",
        "headline": "To 10 Freeway",
        "via": "via CA-38",
        "desc": "Toward Angelus Oaks & Redlands",
        "waypoints": ["34.236818,-116.888750", "34.126930,-116.984277"],
        "dest": "34.070346,-117.182765",
    },
    {
        "id": "18lv",
        "headline": "To 15 Freeway",
        "via": "via CA-18 Lucerne Valley",
        "desc": "The back way · High Desert & Las Vegas",
        "waypoints": ["34.236818,-116.888750", "34.446706,-116.993016"],
        "dest": "34.4163,-117.3017",
    },
]

def round5(minutes):
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

with open("routes-sv.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nroutes-sv.json written successfully.")
