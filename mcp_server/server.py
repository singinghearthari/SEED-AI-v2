"""
SEED AI — MCP Server
Exposes agricultural knowledge bases as MCP tools.
Run: python mcp_server/server.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP
from kb_loader import (
    search_diseases, search_treatments, search_crops,
    search_schemes, search_pests, list_categories,
    get_crops, get_diseases, get_treatments, get_pests,
    get_soil_types, get_schemes, get_fertilizers, get_market_data,
)

mcp = FastMCP("SEED AI Knowledge Server", instructions="Agricultural knowledge base for crop diseases, treatments, pests, government schemes, and crop guidance in India.")

@mcp.tool()
def get_disease_info(query: str) -> str:
    """Search for crop diseases by disease name or affected crop. Returns symptoms, risk level, yield loss, spread mechanism, and affected regions."""
    results = search_diseases(query)
    if not results:
        return f"No diseases found matching '{query}'."
    lines = [f"Found {len(results)} disease(s):"]
    for r in results:
        lines.append(
            f"\n{r['name']} ({r.get('scientific_name', 'N/A')})"
            f"\n  Crops affected: {', '.join(r.get('crops_affected', []))}"
            f"\n  Risk: {r.get('risk_level', 'N/A')} | Yield loss: {r.get('yield_loss_potential', 'N/A')}"
            f"\n  Symptoms: {'; '.join(r.get('symptoms', []))}"
            f"\n  Spread: {r.get('spread_mechanism', 'N/A')}"
            f"\n  Conditions: {r.get('favorable_conditions', 'N/A')}"
            f"\n  Regions: {', '.join(r.get('regions_common', []))}"
        )
    return "\n".join(lines)

@mcp.tool()
def get_treatment_plan(disease_name: str) -> str:
    """Get treatment options for a specific disease by name. Returns chemical, organic, biological, and cultural treatments with dosages, costs, and effectiveness."""
    results = search_treatments(disease_name)
    if not results:
        return f"No treatments found for '{disease_name}'."
    lines = [f"Treatments for {disease_name}:"]
    for t in results:
        lines.append(
            f"\n- {t['type']}: {t['name']}"
            f"\n  Dosage: {t.get('dosage', 'N/A')}"
            f"\n  Application: {t.get('application', 'N/A')}"
            f"\n  Cost: ₹{t.get('cost_estimate_inr', 'N/A')}"
            f"\n  Effectiveness: {t.get('effectiveness', 'N/A')}"
            f"\n  Waiting period: {t.get('waiting_period_days', 'N/A')} days"
        )
    return "\n".join(lines)

@mcp.tool()
def get_crop_guide(crop_name: str) -> str:
    """Get agronomic information for a crop. Returns season, sowing, harvest, soil, water, temperature, diseases, pests, yield, market price, and varieties."""
    results = search_crops(crop_name)
    if not results:
        return f"No crop found matching '{crop_name}'."
    c = results[0]
    return (
        f"{c['name']} ({c.get('scientific_name', 'N/A')})"
        f"\nCategory: {c.get('category', 'N/A')}"
        f"\nSeason: {', '.join(c.get('season', []))}"
        f"\nSowing: {', '.join(c.get('sowing_months', []))}"
        f"\nHarvest: {', '.join(c.get('harvest_months', []))}"
        f"\nDuration: {c.get('duration_days', 'N/A')}"
        f"\nSpacing: {c.get('spacing', 'N/A')}"
        f"\nSeed rate: {c.get('seed_rate_per_acre', 'N/A')}"
        f"\nSoil: {', '.join(c.get('soil_type', []))}"
        f"\nWater: {c.get('water_requirement_mm', 'N/A')}mm"
        f"\nTemperature: {c.get('temperature_range_c', 'N/A')}"
        f"\nYield: {c.get('yield_potential_tonnes_per_acre', 'N/A')} tonnes/acre"
        f"\nMarket price: ₹{c.get('market_price_range_inr_per_kg', 'N/A')}/kg"
        f"\nMajor diseases: {', '.join(c.get('major_diseases', []))}"
        f"\nMajor pests: {', '.join(c.get('major_pests', []))}"
        f"\nVarieties: {', '.join(c.get('popular_varieties_india', []))}"
        f"\nProducers: {', '.join(c.get('states_major_producers', []))}"
    )

@mcp.tool()
def find_government_schemes(query: str) -> str:
    """Search for Indian government agricultural schemes by name or type. Returns eligibility, benefits, premiums, application process, and contact info."""
    results = search_schemes(query)
    if not results:
        return f"No schemes found matching '{query}'."
    lines = [f"Found {len(results)} scheme(s):"]
    for s in results:
        lines.append(
            f"\n{s['name']}"
            f"\n  Type: {s.get('type', 'N/A')} | Ministry: {s.get('ministry', 'N/A')}"
            f"\n  Description: {s.get('description', 'N/A')}"
            f"\n  Benefits: {s.get('benefits', 'N/A')}"
            f"\n  Eligibility: {'; '.join(s.get('eligibility', []))}"
            f"\n  Premium/Cost: {s.get('premium_rate', s.get('interest_rate', 'N/A'))}"
            f"\n  How to apply: {'; '.join(s.get('how_to_apply', []))}"
            f"\n  Website: {s.get('website', 'N/A')}"
            f"\n  Helpline: {s.get('helpline', 'N/A')}"
        )
    return "\n".join(lines)

@mcp.tool()
def get_pest_management(query: str) -> str:
    """Search for agricultural pests by pest name or affected crop. Returns identification, lifecycle, economic threshold, and management strategies (cultural, biological, chemical, organic)."""
    results = search_pests(query)
    if not results:
        return f"No pests found matching '{query}'."
    lines = [f"Found {len(results)} pest(s):"]
    for p in results:
        mgmt = p.get("management", {})
        lines.append(
            f"\n{p['name']} ({p.get('scientific_name', 'N/A')})"
            f"\n  Category: {p.get('category', 'N/A')}"
            f"\n  Crops affected: {', '.join(p.get('crops_affected', []))}"
            f"\n  Identification: {p.get('identification', 'N/A')}"
            f"\n  Life cycle: {p.get('life_cycle_days', 'N/A')} days"
            f"\n  Economic threshold: {p.get('economic_threshold_level', 'N/A')}"
            f"\n  Cultural controls: {'; '.join(mgmt.get('cultural', []))}"
            f"\n  Biological controls: {'; '.join(mgmt.get('biological', []))}"
            f"\n  Chemical controls: {'; '.join(mgmt.get('chemical', []))}"
            f"\n  Organic controls: {'; '.join(mgmt.get('organic', []))}"
            f"\n  Peak season: {p.get('peak_season', 'N/A')}"
        )
    return "\n".join(lines)

@mcp.tool()
def get_soil_guide(soil_type: str) -> str:
    """Get information about a soil type by name. Returns coverage, regions, characteristics, nutrient status, best crops, and management recommendations."""
    q = soil_type.lower()
    for s in get_soil_types():
        if q in s["soil_type"].lower():
            n = s.get("nutrient_status", {})
            return (
                f"{s['soil_type']}"
                f"\nCoverage: {s.get('coverage_percent_india', 'N/A')}% of India"
                f"\nRegions: {', '.join(s.get('regions', []))}"
                f"\nTexture: {s.get('characteristics', {}).get('texture', 'N/A')}"
                f"\npH: {s.get('characteristics', {}).get('pH_range', 'N/A')}"
                f"\nOrganic carbon: {s.get('characteristics', {}).get('organic_carbon_percent', 'N/A')}"
                f"\nWater retention: {s.get('characteristics', {}).get('water_retention', 'N/A')}"
                f"\nDrainage: {s.get('characteristics', {}).get('drainage', 'N/A')}"
                f"\nNitrogen: {n.get('nitrogen', 'N/A')}"
                f"\nPhosphorus: {n.get('phosphorus', 'N/A')}"
                f"\nPotassium: {n.get('potassium', 'N/A')}"
                f"\nZinc: {n.get('zinc', 'N/A')}"
                f"\nBest crops: {', '.join(s.get('best_crops', []))}"
                f"\nManagement: {'; '.join(s.get('management_recommendations', []))}"
            )
    return f"No soil type found matching '{soil_type}'. Available: Alluvial, Black, Red, Laterite, Saline-Sodic"

@mcp.tool()
def get_market_prices(crop: str = "") -> str:
    """Get MSP (Minimum Support Price) data for Indian crops. Optionally filter by crop name. Returns MSP per quintal and cost of production."""
    data = get_market_data()
    if not data or "msp_2024_25" not in data:
        return "Market data not available."
    msp = data["msp_2024_25"]
    q = crop.lower() if crop else ""
    lines = ["MSP 2024-25 (₹ per quintal):"]
    for season in ["kharif", "rabi", "other"]:
        items = msp.get(season, {})
        if not items:
            continue
        lines.append(f"\n{season.title()}:")
        for name, info in items.items():
            if q and q not in name.lower():
                continue
            cost = info.get("cost_of_production", "N/A")
            note = info.get("note", "")
            lines.append(f"  {name}: MSP ₹{info['msp_per_quintal']}/quintal (CoP: ₹{cost}{' — ' + note if note else ''})")
    return "\n".join(lines)

@mcp.tool()
def knowledge_base_categories() -> str:
    """List all available knowledge base categories in the SEED AI system."""
    cats = list_categories()
    return "Available categories:\n" + "\n".join(f"- {c}" for c in cats)

@mcp.resource("seedai://diseases/list")
def diseases_list() -> str:
    """List all diseases in the knowledge base."""
    names = [d["name"] for d in get_diseases()]
    return "Diseases:\n" + "\n".join(f"- {n}" for n in names)

@mcp.resource("seedai://crops/list")
def crops_list() -> str:
    """List all crops in the knowledge base."""
    names = [c["name"] for c in get_crops()]
    return "Crops:\n" + "\n".join(f"- {n}" for n in names)

@mcp.resource("seedai://schemes/list")
def schemes_list() -> str:
    """List all government schemes in the knowledge base."""
    names = [s["name"] for s in get_schemes()]
    return "Government Schemes:\n" + "\n".join(f"- {n}" for n in names)

@mcp.resource("seedai://pests/list")
def pests_list() -> str:
    """List all pests in the knowledge base."""
    names = [p["name"] for p in get_pests()]
    return "Pests:\n" + "\n".join(f"- {n}" for n in names)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="sse")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
