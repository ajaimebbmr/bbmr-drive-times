#!/usr/bin/env python3
"""BBMR Drive Times — poller for all three resort displays."""
import requests, json, os
from datetime import datetime
from zoneinfo import ZoneInfo

KEY = os.environ["TOMTOM_KEY"]

TZ = ZoneInfo("America/Los_Angeles")
# Production window, sized to stay within TomTom's 20K/month free Routing API tier
# at the */8 cron cadence set in crontab (~80-89% of quota depending on month length).
START_HOUR = 10
END_HOUR   = 18
WEB_ROOT = "/var/www/drivetimes"

OVERRIDES = {
    "r1": { "status": "open",   "message": None },
    "r2": { "status": "open",   "message": None },
    "r3": { "status": "open",   "message": None },
    "r4": { "status": "open",   "message": None },
}

DESTINATIONS = [
    { "id": "r1", "num": "CA-210", "via": "via CA-18 Running Springs to CA-330",
      "waypoints": ["34.205167,-117.112798", "34.179970,-117.163001"], "dest": "34.136158,-117.191792" },
    { "id": "r2", "num": "CA-210", "via": "via CA-18 Running Springs",
      "waypoints": ["34.226757,-117.134675"], "dest": "34.147017,-117.279029" },
    { "id": "r3", "num": "CA-10",  "via": "via CA-38",
      "waypoints": ["34.126930,-116.984277"], "dest": "34.070346,-117.182765" },
    { "id": "r4", "num": "CA-15",  "via": "via CA-18 Lucerne Valley",
      "waypoints": ["34.446706,-116.993016"], "dest": "34.416300,-117.301700" },
]

ORIGINS = [
    { "key": "bm", "name": "Bear Mountain", "origin": "34.228479,-116.860377", "out": "routes-bm.json" },
    { "key": "ss", "name": "Snow Summit",   "origin": "34.236555,-116.888996", "out": "routes-ss.json" },
    { "key": "sv", "name": "Snow Valley",   "origin": "34.224625,-117.036427", "out": "routes-sv.json" },
]

def round5(m): return round(m/5)*5

def fetch(origin, route):
    loc = ":".join([origin] + route["waypoints"] + [route["dest"]])
    r = requests.get(f"https://api.tomtom.com/routing/1/calculateRoute/{loc}/json",
        params={"key":KEY,"traffic":"true","computeTravelTimeFor":"all","travelMode":"car"}, timeout=15)
    r.raise_for_status()
    s = r.json()["routes"][0]["summary"]
    return round5(s["travelTimeInSeconds"]/60), round5(s["noTrafficTravelTimeInSeconds"]/60)

def build(origin_cfg):
    rows=[]
    for d in DESTINATIONS:
        ov=OVERRIDES[d["id"]]; row={"num":d["num"],"via":d["via"]}
        if ov["status"]=="closed":
            row["status"]="closed"; row["message"]=ov["message"]
            print(f"  {origin_cfg['key']}/{d['id']}: CLOSED (override)")
        else:
            try:
                mins,typ=fetch(origin_cfg["origin"],d)
                row["status"]="open"; row["minutes"]=mins; row["typical"]=typ
                if ov["message"]: row["message"]=ov["message"]
                print(f"  {origin_cfg['key']}/{d['id']}: {mins} min (typical {typ})")
            except Exception as e:
                print(f"  {origin_cfg['key']}/{d['id']}: FAILED — {e}"); row["status"]="unknown"
        rows.append(row)
    return {"updatedAt":datetime.now(TZ).isoformat(),"routes":rows}

def main():
    now=datetime.now(TZ)
    if not (START_HOUR<=now.hour<END_HOUR):
        print(f"{now:%Y-%m-%d %H:%M} PT — outside window {START_HOUR}:00-{END_HOUR}:00. Skipping."); return
    print(f"{now:%Y-%m-%d %H:%M} PT — fetching all three origins")
    for o in ORIGINS:
        feed=build(o); path=os.path.join(WEB_ROOT,o["out"])
        with open(path,"w") as f: json.dump(feed,f,indent=2)
        print(f"  wrote {path}")
    print("done")

if __name__=="__main__": main()
