import json
import os

logs_file = "mock-data/logs/search_events.jsonl"
products_dir = "mock-data/products/"

# Load all products into a dictionary mapping ID to Title
products_db = {}
for f in os.listdir(products_dir):
    if f.endswith('.json'):
        with open(os.path.join(products_dir, f), 'r') as file:
            data = json.load(file)
            for p in data.get('products', []):
                products_db[p['id']] = p.get('title', '')

# Check logs
mismatches = []
missing_products = set()

with open(logs_file, 'r') as f:
    for line in f:
        if not line.strip(): continue
        event = json.loads(line)
        query = event.get("query", {}).get("text", "")
        results = event.get("response", {}).get("results", [])
        
        for r in results:
            pid = r.get("product_id")
            if pid not in products_db:
                missing_products.add(pid)
            else:
                title = products_db[pid]
                # Basic heuristic: if the query doesn't share any words with the title, flag it
                query_words = set(query.lower().split())
                title_words = set(title.lower().split())
                
                # Check for overlap (excluding common words and numbers)
                common = query_words.intersection(title_words)
                if len(common) == 0:
                    mismatches.append({"query": query, "product_id": pid, "title": title})

print(f"Total Missing Products: {len(missing_products)}")
if missing_products:
    print(f"Missing IDs: {list(missing_products)[:10]}...")

print(f"Total Conceptual Mismatches (0 shared words): {len(mismatches)}")
if mismatches:
    for m in mismatches[:10]:
        print(f"Query: '{m['query']}' -> Returned ID: {m['product_id']} (Title: '{m['title']}')")