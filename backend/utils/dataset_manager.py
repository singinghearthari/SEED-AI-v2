import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("DatasetManager")

# Resolve knowledge_base path relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_KB_PATH = os.path.join(_PROJECT_ROOT, "knowledge_base")


class DatasetManager:
    """
    Production Dataset Manager.
    Scans the knowledge_base directory (and optionally DATASET_PATH from .env)
    and builds an in-memory index for RAG retrieval.
    """

    def __init__(self):
        self.knowledge_index: Dict[str, Any] = {}

        # Always load from project knowledge_base directory
        self._scan_directory(_DEFAULT_KB_PATH)

        # Also load from external dataset path if configured
        external_path = os.getenv("DATASET_PATH")
        if external_path and os.path.exists(external_path):
            self._scan_directory(external_path)

    def _scan_directory(self, path: str):
        """Scans a directory and loads all JSON files into the index."""
        if not os.path.exists(path):
            logger.warning(f"Path {path} does not exist. Skipping.")
            return

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        key = file.replace(".json", "")
                        self.knowledge_index[key] = data
                        logger.info(f"Loaded knowledge base: {key} ({len(data) if isinstance(data, list) else 'dict'} entries)")
                    except Exception as e:
                        logger.error(f"Failed to load {file}: {e}")

    def query(self, category: str, keyword: str) -> List[Dict[str, Any]]:
        """
        Retrieves relevant entries from a knowledge base category
        by performing keyword matching across all string values.
        """
        if not keyword or category not in self.knowledge_index:
            return []

        data = self.knowledge_index[category]
        results = []

        items = data if isinstance(data, list) else list(data.values())
        keyword_lower = keyword.lower()

        for item in items:
            if isinstance(item, dict):
                if any(keyword_lower in str(val).lower() for val in item.values()):
                    results.append(item)

        return results

    def get_all(self, category: str) -> Any:
        """Returns the full dataset for a category."""
        return self.knowledge_index.get(category, [])

    def list_categories(self) -> List[str]:
        """Returns all indexed knowledge base categories."""
        return list(self.knowledge_index.keys())
