import json

queries_file = "mock-data/queries/zero_result_queries.json"

with open(queries_file, "r") as f:
    data = json.load(f)

# Add autocomplete/typo failure queries
new_queries = [
    "waterp",
    "backp",
    "runnng",
    "hyb",
    "campn",
    "elec"
]

for q in new_queries:
    if q not in data["queries"]:
        data["queries"].append(q)

with open(queries_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"Added {len(new_queries)} autocomplete failure queries.")
