#!/usr/bin/env python3
"""
Batch Evaluation v8: Live Azure AI Search Integration (修正版)
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI


class RAGEvaluator:
    """RAG評価システム"""
    
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX", "rag-index")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_chat = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o")
        self.deployment_embedding = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
        
        self.credential = DefaultAzureCredential()
        
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index,
            credential=self.credential
        )
        
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            azure_ad_token_provider=self._get_token,
            api_version="2024-10-01-preview"
        )
    
    def _get_token(self) -> str:
        return self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    
    def get_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            model=self.deployment_embedding,
            input=text
        )
        return response.data[0].embedding
    
    def hybrid_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        embedding = self.get_embedding(query)
        
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector"  # 修正: contentVector → content_vector
        )
        
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "title", "content", "category"],
            top=top_k
        )
        
        return [
            {
                "id": r.get("id", ""),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "category": r.get("category", ""),
                "score": r.get("@search.score", 0.0)
            }
            for r in results
        ]
    
    def generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        # app/api/routes/rag.pyからプロンプトをインポート
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from app.api.routes.rag import DEFAULT_RAG_SYSTEM_PROMPT
        
        context_text = "\n\n".join([
            f"【{c['title']}】\n{c['content']}"
            for c in context
        ])
        
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{query}"""
        
        messages = [
            {"role": "system", "content": DEFAULT_RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )
        
        return response.choices[0].message.content
    
    def evaluate_metric(self, query: str, answer: str, context: List[Dict[str, Any]], metric: str) -> float:
        """メトリクス評価（LLM-as-Judge）"""
        
        metric_prompts = {
            "coherence": """以下の回答の論理的一貫性を0-1のスコアで評価してください。

質問: {query}
回答: {answer}

評価基準:
- 1.0: 完全に論理的で矛盾がない
- 0.5: 部分的に論理的だが改善の余地あり
- 0.0: 論理的でない、矛盾が多い

スコアのみを数値で回答してください（例: 0.85）""",
            
            "relevance": """以下の回答が質問に対してどの程度関連性があるかを0-1のスコアで評価してください。

質問: {query}
回答: {answer}

評価基準:
- 1.0: 完全に質問に答えている
- 0.5: 部分的に関連している
- 0.0: 質問と無関係

スコアのみを数値で回答してください（例: 0.92）""",
            
            "groundedness": """以下の回答がコンテキストに基づいているかを0-1のスコアで評価してください。

コンテキスト: {context}
回答: {answer}

評価基準:
- 1.0: 回答の全てがコンテキストに基づいている
- 0.5: 一部がコンテキスト外の情報を含む
- 0.0: ほとんどがコンテキスト外の情報

スコアのみを数値で回答してください（例: 0.78）"""
        }
        
        context_text = "\n".join([c['content'][:200] for c in context])  # 長さ制限
        prompt = metric_prompts[metric].format(
            query=query,
            answer=answer,
            context=context_text
        )
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        
        try:
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except:
            return 0.0


def main():
    parser = argparse.ArgumentParser(description="RAG評価システム v8")
    parser.add_argument("--qa-data", required=True, help="評価データセット（JSONL形式）")
    parser.add_argument("--output-dir", default="evaluation_results/D21-4", help="出力ディレクトリ")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ")
    
    args = parser.parse_args()
    
    # 出力ディレクトリ作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 評価データ読み込み（JSONL対応）
    qa_pairs = []
    with open(args.qa_data, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                qa_pairs.append(json.loads(line))
    
    print(f"📊 評価データ件数: {len(qa_pairs)}")
    
    # 評価実行
    evaluator = RAGEvaluator()
    results = []
    
    for i, qa in enumerate(qa_pairs, 1):
        query = qa.get("question", qa.get("query", ""))
        
        if args.verbose:
            print(f"\n[{i}/{len(qa_pairs)}] 質問: {query[:50]}...")
        
        try:
            # RAG実行
            context = evaluator.hybrid_search(query, top_k=3)
            answer = evaluator.generate_answer(query, context)
            
            # メトリクス評価
            coherence = evaluator.evaluate_metric(query, answer, context, "coherence")
            relevance = evaluator.evaluate_metric(query, answer, context, "relevance")
            groundedness = evaluator.evaluate_metric(query, answer, context, "groundedness")
            
            results.append({
                "question": query,
                "answer": answer,
                "context_count": len(context),
                "coherence": coherence,
                "relevance": relevance,
                "groundedness": groundedness,
            })
            
            if args.verbose:
                print(f"  Coherence: {coherence:.3f}, Relevance: {relevance:.3f}, Groundedness: {groundedness:.3f}")
        
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            continue
    
    # 集計
    avg_coherence = sum(r["coherence"] for r in results) / len(results) if results else 0
    avg_relevance = sum(r["relevance"] for r in results) / len(results) if results else 0
    avg_groundedness = sum(r["groundedness"] for r in results) / len(results) if results else 0
    
    # 結果保存
    output_file = output_dir / "evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(qa_pairs),
            "successful_evaluations": len(results),
            "aggregate_metrics": {
                "coherence": avg_coherence,
                "relevance": avg_relevance,
                "groundedness": avg_groundedness,
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 評価完了")
    print(f"成功: {len(results)}/{len(qa_pairs)}")
    print(f"平均 Coherence: {avg_coherence:.3f}")
    print(f"平均 Relevance: {avg_relevance:.3f}")
    print(f"平均 Groundedness: {avg_groundedness:.3f}")
    print(f"\n結果: {output_file}")


if __name__ == "__main__":
    main()
