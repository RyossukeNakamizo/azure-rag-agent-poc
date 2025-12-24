"""
Azure AI Search Service

Phase 2-2/2-3: ハイブリッド検索（Vector + Keyword）実装
"""
import logging
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

logger = logging.getLogger(__name__)


class SearchService:
    """Azure AI Search サービスクラス"""
    
    def __init__(
        self,
        endpoint: str,
        index_name: str,
        credential: Optional[DefaultAzureCredential] = None,
    ):
        self.endpoint = endpoint
        self.index_name = index_name
        self.credential = credential or DefaultAzureCredential()
        
        self._client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential,
        )
        logger.info(f"SearchService initialized: {endpoint}, index={index_name}")
    
    def hybrid_search(
        self,
        query: str,
        embedding: list[float],
        top_k: int = 5,
        filter_expression: Optional[str] = None,
    ) -> list[dict]:
        """
        ハイブリッド検索（Vector + Keyword）
        """
        try:
            vector_query = VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=top_k,
                fields="content_vector",
            )
            
            results = self._client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_expression,
                select=["id", "title", "content", "source", "category"],
                top=top_k,
            )
            
            output = []
            for result in results:
                output.append({
                    "id": result.get("id", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "category": result.get("category", ""),
                    "score": result.get("@search.score", 0.0),
                })
            
            logger.info(f"Hybrid search: query='{query[:30]}...', results={len(output)}")
            return output
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}", exc_info=True)
            raise
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        filter_expression: Optional[str] = None,
    ) -> list[dict]:
        """
        キーワード検索（BM25）
        """
        try:
            results = self._client.search(
                search_text=query,
                filter=filter_expression,
                select=["id", "title", "content", "source", "category"],
                top=top_k,
            )
            
            output = []
            for result in results:
                output.append({
                    "id": result.get("id", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "category": result.get("category", ""),
                    "score": result.get("@search.score", 0.0),
                })
            
            logger.info(f"Keyword search: query='{query[:30]}...', results={len(output)}")
            return output
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}", exc_info=True)
            raise