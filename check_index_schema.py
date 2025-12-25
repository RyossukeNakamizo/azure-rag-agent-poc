from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
import os

credential = DefaultAzureCredential()
index_client = SearchIndexClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=credential
)

index = index_client.get_index(os.getenv("AZURE_SEARCH_INDEX"))

print(f"=== インデックススキーマ: {index.name} ===\n")
print("フィールド一覧:")

for field in index.fields:
    field_type = field.type
    if hasattr(field, 'vector_search_dimensions'):
        print(f"  📊 {field.name}: {field_type} (Vector: {field.vector_search_dimensions}次元)")
    else:
        print(f"  📝 {field.name}: {field_type}")
