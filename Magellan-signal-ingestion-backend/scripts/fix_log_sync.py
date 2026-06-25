import json
import os
import random

logs_file = "mock-data/logs/search_events.jsonl"
products_dir = "mock-data/products/"

# Load all products into a searchable list
products_db = []
for f in os.listdir(products_dir):
    if f.endswith('.json'):
        with open(os.path.join(products_dir, f), 'r') as file:
            data = json.load(file)
            for p in data.get('products', []):
                products_db.append({
                    "id": p['id'],
                    "title": p.get('title', '').lower(),
                    "desc": p.get('description', '').lower(),
                    "category": p.get('category', '').lower()
                })

def score_product(query_words, p):
    score = 0
    for w in query_words:
        if w in p['title']: score += 3
        if w in p['desc']: score += 1
        if w in p['category']: score += 2
    return score

with open(logs_file, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if not line.strip(): continue
    event = json.loads(line)
    
    # Only fix queries that have > 0 results
    if event.get("response", {}).get("result_count", 0) > 0:
        query = event.get("query", {}).get("text", "").lower()
        query_words = [w for w in query.split() if w not in ["inch", "liters", "grams", "size", "under", "with", "for"]]
        
        # Score all products
        scored_products = []
        for p in products_db:
            score = score_product(query_words, p)
            if score > 0:
                scored_products.append((score, p['id']))
                
        # Sort by score desc
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N matching products (based on original result_count)
        original_count = len(event["response"]["results"])
        top_matches = [pid for score, pid in scored_products[:original_count]]
        
        # Fallback if no matches found (unlikely but possible)
        if not top_matches:
            top_matches = [p['id'] for p in random.sample(products_db, min(original_count, len(products_db)))]
            
        # Rebuild results array
        new_results = []
        for i, pid in enumerate(top_matches):
            new_results.append({
                "product_id": pid,
                "rank": i + 1,
                "score": round(0.95 - (i * 0.05), 2)
            })
            
        event["response"]["results"] = new_results
        
    new_lines.append(json.dumps(event) + "\n")

with open(logs_file, 'w') as f:
    f.writelines(new_lines)

print("Fixed log sync. Products now semantically match queries.")