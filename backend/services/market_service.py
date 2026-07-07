import os
import logging
from utils.api_gateway import APIGateway

logger = logging.getLogger("MarketService")


class MarketService:
    """
    Production market price service using Data.gov.in Agmarknet API.
    Returns live market data or a structured error if unavailable.
    """

    def __init__(self):
        self.api_url = os.getenv(
            "AGMARKNET_API_URL",
            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
        )
        self.api_key = os.getenv("DATA_GOV_IN_API_KEY")

    def get_price(self, crop: str, state: str = None) -> dict:
        if not self.api_key:
            logger.warning("DATA_GOV_IN_API_KEY not configured.")
            return {"error": "DATA_GOV_IN_API_KEY not set", "crop": crop, "source": "none"}

        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "filters[commodity]": crop,
            }
            if state:
                params["filters[state]"] = state

            data = APIGateway.fetch_json(self.api_url, params=params, timeout=8)

            records = data.get("records", [])
            if not records:
                return {"crop": crop, "price": None, "trend": "no data available", "source": "data.gov.in"}

            avg_price = sum(float(r["modal_price"]) for r in records) / len(records)
            return {
                "crop": crop,
                "price_per_quintal": round(avg_price, 2),
                "num_records": len(records),
                "source": "data.gov.in",
            }
        except Exception as e:
            logger.error(f"Market API call failed: {e}")
            return {"error": f"Market service unavailable: {str(e)}", "crop": crop, "source": "none"}
