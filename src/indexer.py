"""
Azure AI Search Indexer module.

Features:
- Index schema creation with vector search
- Document batch upload
- Skillset configuration (optional AI enrichment)
"""
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from .config import get_azure_credential, get_settings


class SearchIndexManager:
    """
    Manages Azure AI Search index lifecycle.

    Handles index creation, schema updates, and document ingestion.
    """

    def __init__(self):
        """Initialize with Azure credentials."""
        settings = get_settings()
        credential = get_azure_credential()

        self.index_client = SearchIndexClient(
            endpoint=settings.search_endpoint,
            credential=credential,
        )
        self.search_client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index,
            credential=credential,
        )
        self.index_name = settings.search_index

    def create_index(self, vector_dimensions: int = 1536) -> SearchIndex:
        """
        Create or update search index with vector search capability.

        Args:
            vector_dimensions: Embedding vector size (1536 for ada-002)

        Returns:
            SearchIndex: Created/updated index
        """
        # Define fields
        fields = [
            # Primary key
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            # Document reference
            SimpleField(
                name="document_id",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            # Main content (searchable)
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="ja.lucene",  # Japanese analyzer
            ),
            # Vector embedding
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=vector_dimensions,
                vector_search_profile_name="rag-vector-profile",
            ),
            # Metadata fields
            SimpleField(
                name="source",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="category",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="chunk_index",
                type=SearchFieldDataType.Int32,
                sortable=True,
            ),
            SimpleField(
                name="token_count",
                type=SearchFieldDataType.Int32,
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
            ),
        ]

        # Vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="rag-hnsw-config",
                    parameters={
                        "m": 4,  # Bi-directional links per node
                        "efConstruction": 400,  # Index build quality
                        "efSearch": 500,  # Search quality
                        "metric": "cosine",
                    },
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name="rag-vector-profile",
                    algorithm_configuration_name="rag-hnsw-config",
                ),
            ],
        )

        # Create index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
        )

        return self.index_client.create_or_update_index(index)

    def upload_documents(
        self,
        documents: list[dict],
        batch_size: int = 100,
    ) -> dict:
        """
        Upload documents to search index in batches.

        Args:
            documents: List of documents to upload
            batch_size: Documents per upload batch

        Returns:
            dict: Upload results summary
        """
        results = {
            "succeeded": 0,
            "failed": 0,
            "errors": [],
        }

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            try:
                result = self.search_client.upload_documents(batch)
                succeeded = sum(1 for r in result if r.succeeded)
                failed = len(result) - succeeded

                results["succeeded"] += succeeded
                results["failed"] += failed

                # Collect errors
                for r in result:
                    if not r.succeeded:
                        results["errors"].append({
                            "key": r.key,
                            "error": r.error_message,
                        })
            except Exception as e:
                results["failed"] += len(batch)
                results["errors"].append({
                    "batch_start": i,
                    "error": str(e),
                })

        return results

    def delete_index(self) -> None:
        """Delete the search index."""
        self.index_client.delete_index(self.index_name)

    def get_document_count(self) -> int:
        """Get total document count in index."""
        return self.search_client.get_document_count()


class DocumentIngestionPipeline:
    """
    End-to-end document ingestion pipeline.

    Combines processing and indexing for streamlined data loading.
    """

    def __init__(self):
        """Initialize pipeline components."""
        from .embedding import DocumentProcessor

        self.processor = DocumentProcessor()
        self.index_manager = SearchIndexManager()

    def ingest_documents(
        self,
        documents: list[dict],
    ) -> dict:
        """
        Process and ingest multiple documents.

        Args:
            documents: List of documents with format:
                - id: Document ID
                - content: Text content
                - metadata: Optional metadata (source, category, title)

        Returns:
            dict: Ingestion results
        """
        all_chunks = []

        for doc in documents:
            metadata = doc.get("metadata", {})
            chunks = self.processor.process_document(
                document_id=doc["id"],
                text=doc["content"],
                metadata=metadata,
            )
            all_chunks.extend(chunks)

        # Upload to index
        return self.index_manager.upload_documents(all_chunks)

    def ingest_from_blob(
        self,
        container_name: str | None = None,
        prefix: str = "",
    ) -> dict:
        """
        Ingest documents from Azure Blob Storage.

        Args:
            container_name: Blob container name (uses default from settings if None)
            prefix: Optional blob prefix filter

        Returns:
            dict: Ingestion results
        """
        from azure.storage.blob import BlobServiceClient

        settings = get_settings()
        credential = get_azure_credential()

        blob_service = BlobServiceClient(
            account_url=settings.storage_account_url,
            credential=credential,
        )

        container = container_name or settings.storage_container
        container_client = blob_service.get_container_client(container)

        documents = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            if blob.name.endswith((".txt", ".md")):
                blob_client = container_client.get_blob_client(blob.name)
                content = blob_client.download_blob().readall().decode("utf-8")

                documents.append({
                    "id": blob.name.replace("/", "_").replace(".", "_"),
                    "content": content,
                    "metadata": {
                        "source": f"blob://{container}/{blob.name}",
                        "title": blob.name.split("/")[-1],
                    },
                })

        return self.ingest_documents(documents)
