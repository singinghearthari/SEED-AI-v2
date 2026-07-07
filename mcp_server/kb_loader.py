import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "knowledge_base"

_cache = {}

def _load(name):
    if name not in _cache:
        path = BASE / f"{name}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                _cache[name] = json.load(f)
        else:
            _cache[name] = []
    return _cache[name]

def get_crops():
    return _load("crops")

def get_diseases():
    return _load("diseases")

def get_treatments():
    return _load("treatments")

def get_fertilizers():
    return _load("fertilizers")

def get_pests():
    return _load("pests")

def get_soil_types():
    return _load("soil_health")

def get_schemes():
    return _load("government_schemes")

def get_market_data():
    return _load("market_intelligence")

def search_diseases(query: str) -> list:
    q = query.lower()
    results = []
    for d in get_diseases():
        if q in d["name"].lower() or any(q in c.lower() for c in d.get("crops_affected", [])):
            results.append({
                "id": d["id"],
                "name": d["name"],
                "scientific_name": d.get("scientific_name"),
                "crops_affected": d.get("crops_affected"),
                "symptoms": d.get("symptoms"),
                "risk_level": d.get("risk_level"),
                "yield_loss_potential": d.get("yield_loss_potential"),
                "favorable_conditions": d.get("favorable_conditions"),
                "spread_mechanism": d.get("spread_mechanism"),
                "regions_common": d.get("regions_common"),
            })
    return results

def search_treatments(disease_name: str) -> list:
    q = disease_name.lower()
    for t in get_treatments():
        if q in t["disease_name"].lower():
            return t.get("treatments", [])
    return []

def search_crops(query: str) -> list:
    q = query.lower()
    results = []
    for c in get_crops():
        if q in c["name"].lower() or q in c.get("category", "").lower():
            results.append(c)
    return results

def search_schemes(query: str) -> list:
    q = query.lower()
    results = []
    for s in get_schemes():
        if q in s["name"].lower() or q in s.get("type", "").lower():
            results.append(s)
    return results

def search_pests(query: str) -> list:
    q = query.lower()
    results = []
    for p in get_pests():
        if q in p["name"].lower() or any(q in c.lower() for c in p.get("crops_affected", [])):
            results.append(p)
    return results

def list_categories() -> list:
    return [
        "crops", "diseases", "treatments", "fertilizers",
        "pests", "soil_health", "government_schemes", "market_intelligence"
    ]
