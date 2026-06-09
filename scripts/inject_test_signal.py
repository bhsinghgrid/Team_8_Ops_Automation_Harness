from elasticsearch import Elasticsearch
from datetime import datetime
import uuid

def inject_signal():
    client = Elasticsearch("http://localhost:9200")
    
    # New scenario: Query NOT in Golden Dataset (test production baseline fallback)
    signal_data = {
        "@timestamp": datetime.utcnow().isoformat(),
        "event": {"kind": "relevance_alert"},
        "message": "CRITICAL: Relevance regression detected for 'trail running shoes'.",
        "metadata": {
            "category": "Footwear",
            "query": "trail running shoes",
            "impacted_users": 500
        }
    }
    
    res = client.index(index="magellan-signals", document=signal_data)
    print(f"✅ Injected test signal: {res['result']}")
    print(f"   Summary: {signal_data['message']}")

if __name__ == "__main__":
    inject_signal()
