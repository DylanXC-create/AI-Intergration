from flask import Flask
from flask_cors import CORS
import requests
from typing import Tuple, Dict, Any

app = Flask(__name__)
CORS(app)

HERE_API_KEY: str = "6gbAUK7xvwNxdcExWOPDcKizVzc7fkLkeXAjuc1uwPk"

INTERSECTIONS: Dict[str, Dict[str, Any]] = {
    "main_st_bailey": {"location": "Main St and Bailey Ave", "coords": (42.8864, -78.8784)},
    "walden_bailey": {"location": "Walden Ave and Bailey Ave", "coords": (42.9051, -78.7949)},
    "hertel_main": {"location": "Hertel Ave and Main St", "coords": (42.9462, -78.8675)},
    "clinton_bailey": {"location": "Clinton St and Bailey Ave", "coords": (42.8923, -78.8316)},
    "transit_sheridan": {"location": "Transit Rd and Sheridan Dr", "coords": (42.9650, -78.6950)},
    "ferry_mass_richmond": {"location": "Ferry St, Massachusetts Ave, and Richmond Ave", "coords": (42.9060, -78.8780)},
    "porter_jersey_normal": {"location": "Porter Ave, Jersey Ave, and Normal Ave", "coords": (42.9180, -78.8920)},
    "niagara_east_robinson": {"location": "Niagara Falls Blvd and East Robinson Rd", "coords": (42.9840, -78.7200)},
    "elmwood_forest": {"location": "Elmwood Ave and Forest Ave", "coords": (42.9260, -78.8750)},
    "grant_ferry": {"location": "Grant St and Ferry St", "coords": (42.9100, -78.8800)},
}

def fetch_traffic_data(coords: Tuple[float, float]) -> Dict[str, int]:
    lat, lon = coords
    url = f"https://data.traffic.hereapi.com/v7/flow?locationReferencing=shape&in=circle:{lat},{lon};r=500&apiKey={HERE_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if results:
            for result in results:
                current_flow = result.get("currentFlow", {})
                speed = current_flow.get("speed")
                if speed is not None:
                    avg_speed = float(speed)
                    baseline_speed = 40
                    delay_reduction = max(0, (baseline_speed - avg_speed) / baseline_speed) * 0.15
                    vehicles_per_day = 5000
                    days_saved = (vehicles_per_day * delay_reduction * 24 * 60 * 60) / (24 * 60 * 60) * 365
                    cost_saved = days_saved * (vehicles_per_day * 0.005 / 60) * 365
                    return {"days_saved": round(days_saved), "cost_saved_usd": round(cost_saved)}
        return {"days_saved": 0, "cost_saved_usd": 0}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching traffic data: {e}")
        return {"days_saved": 0, "cost_saved_usd": 0}

@app.route('/')
def index():
    return {"message": "Welcome to the Traffic API. Use /traffic/<location> or /traffic/summary for data."}

@app.route('/traffic/<location>')
def traffic(location: str):
    if location not in INTERSECTIONS:
        return {"error": "Location not found"}
    intersection = INTERSECTIONS[location]
    savings = fetch_traffic_data(intersection["coords"])
    return {
        "location": intersection["location"],
        "days_saved": savings["days_saved"],
        "cost_saved_usd": savings["cost_saved_usd"]
    }

@app.route('/traffic/summary')
def summary():
    total_days = 0
    total_cost = 0
    for loc in INTERSECTIONS:
        savings = fetch_traffic_data(INTERSECTIONS[loc]["coords"])
        total_days += savings["days_saved"]
        total_cost += savings["cost_saved_usd"]
    return {
        "total_locations": len(INTERSECTIONS),
        "locations": list(INTERSECTIONS.keys()),
        "total_days_saved": total_days,
        "total_cost_saved_usd": total_cost
    }

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)