import json
import os

logs_file = "mock-data/logs/search_events.jsonl"

if not os.path.exists(logs_file):
    print("Logs file not found.")
    exit(0)

with open(logs_file, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if not line.strip():
        continue
    try:
        event = json.loads(line.strip())
        query = event.get("query", {}).get("text", "")
        
        # Syncing Zero Results with the newly added autocomplete queries
        if query in ["waterp", "backp", "runnng", "hyb", "campn", "elec"]:
            event["response"]["result_count"] = 0
            event["response"]["results"] = []
            
        new_lines.append(json.dumps(event) + "\n")
    except Exception as e:
        new_lines.append(line)

# Add the new autocomplete queries to the logs if they aren't there
existing_queries = []
for line in new_lines:
    if line.strip():
        try:
            existing_queries.append(json.loads(line).get("query", {}).get("text", ""))
        except:
            pass

new_queries = ["waterp", "backp", "runnng", "hyb", "campn", "elec"]

for q in new_queries:
    if q not in existing_queries:
        event = {
            "tenant": "retail_tenant_001",
            "source": "gd_ai_search",
            "timestamp": "2026-06-06T12:00:00Z",
            "request_id": f"req_auto_{q}",
            "session_id": "sess_auto_001",
            "user_id_hash": "usr_auto_001",
            "query": {
                "text": q,
                "normalized_text": q,
                "filters": {},
                "sort": None
            },
            "response": {
                "status_code": 200,
                "latency_ms": 15,
                "result_count": 0,
                "results": []
            },
            "interaction": {
                "clicks": [],
                "cart_adds": []
            },
            "error": None,
            "context": {
                "channel": "mobile",
                "device_type": "mobile",
                "locale": "en-US"
            }
        }
        new_lines.append(json.dumps(event) + "\n")

with open(logs_file, "w") as f:
    f.writelines(new_lines)

print("Synced search_events.jsonl with autocomplete zero results.")