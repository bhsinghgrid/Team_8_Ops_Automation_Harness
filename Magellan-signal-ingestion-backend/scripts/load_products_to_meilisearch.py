import json
import meilisearch

client = meilisearch.Client("http://localhost:7700")

index = client.index("products")

with open(
    "mock_data/products/products.json",
    "r"
) as file:

    products = json.load(file)

index.add_documents(products)

print("Products loaded")
