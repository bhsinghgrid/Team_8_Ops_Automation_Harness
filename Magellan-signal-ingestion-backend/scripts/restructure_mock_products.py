import json
import os

base_path = "mock-data/products/"
files = ["footwear.json", "bags.json", "outerwear.json", "electronics.json", "camping.json"]

all_products = []
for f in files:
    file_path = os.path.join(base_path, f)
    if os.path.exists(file_path):
        with open(file_path) as file:
            data = json.load(file)
            if "products" in data:
                all_products.extend(data["products"])

if not all_products:
    print("No products found to restructure. Maybe already done?")
    exit(0)

# 1. Catalog Gaps (Missing Attributes)
catalog_gaps = {
    "description": "Products with missing attributes causing zero results for specific filters",
    "error_type": "CATALOG_OPTIMIZATION",
    "products": []
}

# 2. Semantic Index Stale
semantic_stale = {
    "description": "Products with updated text but stale embeddings",
    "error_type": "SEMANTIC_SEARCH",
    "products": []
}

# 3. MXP Rule Conflicts (e.g. out of stock but boosted)
mxp_conflicts = {
    "description": "Products targeted by MXP rules but have inventory or other conflicts",
    "error_type": "MXP_RULES",
    "products": []
}

# 4. True Out of Stock (Clean baseline but 0 inventory)
inventory_oos = {
    "description": "Clean products that are simply out of stock",
    "error_type": "INVENTORY",
    "products": []
}

# 5. Clean Baseline (Good products for normal queries)
clean_baseline = {
    "description": "Clean products that return normally",
    "error_type": "NONE",
    "products": []
}

# Distribute products based on ID
for p in all_products:
    pid = p.get("id", "")
    
    # MXP Conflicts
    if pid in ["FOOT-121", "FOOT-122", "OUT-081", "ELEC-062", "ELEC-061"]:
        p["stock"] = 0
        mxp_conflicts["products"].append(p)
        
    # Catalog Gaps
    elif pid in ["FOOT-002", "FOOT-003", "OUT-002", "ELEC-002", "BAGS-053"]:
        if "attributes" in p:
            if "waterproof" in p["attributes"]: del p["attributes"]["waterproof"]
            if "terrain" in p["attributes"]: del p["attributes"]["terrain"]
            if "gps" in p["attributes"]: del p["attributes"]["gps"]
            if "size" in p["attributes"]: del p["attributes"]["size"]
        catalog_gaps["products"].append(p)
        
    # Semantic Stale
    elif pid in ["FOOT-001", "BAGS-001", "OUT-001", "ELEC-001"]:
        if pid == "FOOT-001": p["title"] = "Waterproof Trail Runner Pro 001"
        if pid == "BAGS-001": p["description"] = "expanded product copy for hybrid commute search"
        if pid == "OUT-001": p["title"] = "Gore-Tex Rain Jacket Storm 001"
        if pid == "ELEC-001": p["description"] = "updated copy emphasizing GPS battery performance"
        semantic_stale["products"].append(p)
        
    # Inventory OOS
    elif pid in ["FOOT-211", "CAMP-106"]:
        p["stock"] = 0
        inventory_oos["products"].append(p)
        
    # Clean baseline
    else:
        clean_baseline["products"].append(p)

# Save new files
with open(os.path.join(base_path, "error_catalog_gaps.json"), "w") as f:
    json.dump(catalog_gaps, f, indent=2)
with open(os.path.join(base_path, "error_semantic_stale.json"), "w") as f:
    json.dump(semantic_stale, f, indent=2)
with open(os.path.join(base_path, "error_mxp_conflicts.json"), "w") as f:
    json.dump(mxp_conflicts, f, indent=2)
with open(os.path.join(base_path, "error_inventory_oos.json"), "w") as f:
    json.dump(inventory_oos, f, indent=2)
with open(os.path.join(base_path, "clean_baseline.json"), "w") as f:
    json.dump(clean_baseline, f, indent=2)

# Remove old files
for f in files:
    file_path = os.path.join(base_path, f)
    if os.path.exists(file_path):
        os.remove(file_path)
    
print("Restructured products based on error type.")
