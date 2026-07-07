import requests
from requests.exceptions import RequestException
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import logging

logger = logging.getLogger("APIGateway")

class APIGateway:
    """
    Robust API wrapper for external services.
    Implements timeout, exponential backoff, and error recovery.
    """
    
    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RequestException),
        reraise=True
    )
    def fetch_json(url: str, params: dict = None, headers: dict = None, timeout: int = 10) -> dict:
        """
        Fetches JSON from an external API with robust error handling.
        """
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.warning(f"API Request failed for {url}: {e}. Retrying...")
            raise
