# app/providers/elasticsearch_provider.py
import logging
from elasticsearch import Elasticsearch
from magellan_signal_ingestion_backend.app.core.config import settings

logger = logging.getLogger(__name__)

class ElasticsearchError(RuntimeError):
    pass

class ElasticsearchProvider:
    """
    A provider to fetch signal data from an Elasticsearch instance.
    """

    def __init__(self):
        try:
            self.client = Elasticsearch(settings.ELASTICSEARCH_URL)
            if not self.client.ping():
                raise ConnectionError("Could not connect to Elasticsearch.")
            logger.info("Elasticsearch client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
            raise ElasticsearchError(f"Could not connect to Elasticsearch at {settings.ELASTICSEARCH_URL}.") from e

    def fetch_latest_signal(self) -> dict:
        """
        Fetches the most recent document that could be considered a "signal".

        This is a sample implementation. In a real-world scenario, the query
        would be more sophisticated, looking for specific error patterns,
        anomaly scores, or other indicators of an operational event.
        """
        logger.info("Fetching latest signal from Elasticsearch...")
        
        # This query searches for the most recent document in any index.
        # It's a placeholder for a more specific signal-detection query.
        query = {
            "query": {
                "match_all": {}
            },
            "size": 1,
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ]
        }
        
        try:
            # The search query will look across all indices ('_*')
            response = self.client.search(index="_*", body=query)
            
            hits = response.get("hits", {}).get("hits", [])
            if not hits:
                logger.warning("No signals found in Elasticsearch.")
                raise ElasticsearchError("No documents found in Elasticsearch.")
            
            latest_signal_doc = hits[0]
            logger.info(f"Successfully fetched latest signal document (ID: {latest_signal_doc['_id']})")
            return latest_signal_doc["_source"]
            
        except Exception as e:
            logger.error(f"An error occurred while fetching data from Elasticsearch: {e}")
            raise ElasticsearchError("Failed to fetch data from Elasticsearch.") from e
