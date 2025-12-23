"""
Azure AI Search Service

既存インデックスに対するハイブリッド検索（Vector + Keyword）を提供
"""
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

class SearchService:
    """Azure AI Search サービスラッパー"""
    
    def __init__(
        self,
        endpoint: str,
        index_name: str,
        use_key_credential: bool = False,
        api_key: Optional[str] = None
    ):
        """
        Args:
            endpoint: Search Service エンドポイント
            index_name: インデックス名
            use_key_credential: API Key 使用フラグ（開発用）
            api_key: API Key（use_key_credential=True の場合）
        """
        self.endpoint = endpoint
        self.index_name = index_name
        
        # 認証設定
        if use_key_credential and api_key:
            credential = AzureKeyCredential(api_key)
        else:
            credential = DefaultAzureCredential()
        
        # SearchClient 初期化
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )
    
    def hybrid_search(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
        select_fields: Optional[List[str]] = None,
        filter_expression: Optional[str] = None
    ) -> List[Dict]:
        """
        ハイブリッド検索（Vector + Keyword）
        
        Args:
            query: 検索クエリ（キーワード検索用）
            query_vector: クエリのベクトル表現（ベクトル検索用）
            top_k: 取得件数
            select_fields: 取得フィールド（None の場合は全フィールド）
            filter_expression: フィルタ式（OData構文）
        
        Returns:
            検索結果のリスト
        """
        # ベクトルクエリ設定
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="contentVector"  # rag-docs-index の場合
        )
        
        # 検索実行
        results = self.client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=select_fields,
            filter=filter_expression,
            top=top_k
        )
        
        # 結果を辞書リストに変換
        documents = []
        for result in results:
            doc = {
                "score": result.get("@search.score", 0),
                **{k: v for k, v in result.items() if not k.startswith("@")}
            }
            documents.append(doc)
        
        return documents
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        select_fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        キーワード検索のみ
        
        Args:
            query: 検索クエリ
            top_k: 取得件数
            select_fields: 取得フィールド
        
        Returns:
            検索結果のリスト
        """
        results = self.client.search(
            search_text=query,
            select=select_fields,
            top=top_k
        )
        
        return [
            {
                "score": r.get("@search.score", 0),
                **{k: v for k, v in r.items() if not k.startswith("@")}
            }
            for r in results
        ]
