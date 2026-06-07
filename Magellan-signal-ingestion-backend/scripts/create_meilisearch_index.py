import meilisearch

client = meilisearch.Client("http://localhost:7700")

client.create_index(
    uid="products",
    options={
        "primaryKey": "product_id"
    }
)

index = client.index("products")

index.update_searchable_attributes([
    "title",
    "description",
    "attributes",
    "brand",
    "category"
])

index.update_filterable_attributes([
    "category",
    "brand",
    "stock",
    "quality_flags"
])

print("Products index created")
