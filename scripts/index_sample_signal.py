import datetime
from elasticsearch import Elasticsearch
import time

def index_sample_signal():
    es = Elasticsearch("http://localhost:9200")
    
    index_name = "magellan-signals"
    
    # Sample signal data
    signal_doc = {
        "@timestamp": datetime.datetime.now().isoformat(),
        "event": {
            "kind": "catalog_update_failure",
            "module": "ingestion-service"
        },
        "message": "CRITICAL: Catalog update failed for product category 'Electronics'. 500 items rejected due to schema mismatch.",
        "details": {
            "category": "Electronics",
            "error_code": "SCHEMA_MISMATCH",
            "affected_count": 500
        }
    }
    
    print(f"Indexing sample signal into index '{index_name}'...")
    
    try:
        res = es.index(index=index_name, body=signal_doc)
        print(f"Signal indexed successfully. Result: {res['result']}")
        
        # Refresh the index to make the doc immediately searchable
        es.indices.refresh(index=index_name)
        print("Index refreshed.")
        
    except Exception as e:
        print(f"Error indexing signal: {e}")

if __name__ == "__main__":
    index_sample_signal()
