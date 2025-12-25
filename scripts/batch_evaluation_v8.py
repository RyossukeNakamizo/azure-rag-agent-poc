#!/usr/bin/env python3
"""
Batch Evaluation v8: Live Azure AI Search Integration
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
    
    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.get_embedding(query)
        
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector"
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
                "score": r.get("@search.score", 0)
            }
            for r in results
        ]
    
    def generate_answer(self, query: str, context: List[Dict]) -> str:
        context_text = "\n\n".join([
            f"【{c['title']}】\n{c['content']}"
            for c in context
        ])
        
        system_prompt = "あなたはAzure技術の専門家です。提供されたコンテキストのみを使用して、正確かつ実用的な回答をしてください。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"コンテキスト:\n{context_text}\n\n質問: {query}"}
        ]
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def evaluate_coherence(self, answer: str) -> float:
        prompt = f"""以下の回答の一貫性を0-1で評価してください。
評価結果をJSON形式で返してください。
評価基準：
- 論理的な流れがあるか
- 矛盾がないか
- 文章として自然か

回答: {answer}

評価結果を以下の形式で返してください：
{{"score": 0.0-1.0, "reason": "理由"}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 0.5))
        except:
            return 0.5
    
    def evaluate_relevance(self, question: str, answer: str) -> float:
        prompt = f"""以下の質問と回答の関連性を0-1で評価してください。
評価結果をJSON形式で返してください。
評価基準：
- 質問に直接答えているか
- 不要な情報が含まれていないか
- 質問の意図を理解しているか

質問: {question}
回答: {answer}

評価結果を以下の形式で返してください：
{{"score": 0.0-1.0, "reason": "理由"}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 0.5))
        except:
            return 0.5
    
    def evaluate_groundedness(self, answer: str, context: List[Dict]) -> float:
        context_text = "\n\n".join([c['content'] for c in context])
        
        prompt = f"""以下の回答が、提供されたコンテキストに基づいているかを0-1で評価してください。
評価結果をJSON形式で返してください。
評価基準：
- コンテキストに記載されている情報のみを使用しているか
- コンテキストにない情報を追加していないか
- コンテキストの内容を正確に反映しているか

コンテキスト:
{context_text}

回答: {answer}

評価結果を以下の形式で返してください：
{{"score": 0.0-1.0, "reason": "理由"}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.deployment_chat,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 0.5))
        except:
            return 0.5
    
    def evaluate_single(self, qa_item: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        question = qa_item["question"]
        ground_truth = qa_item["ground_truth"]
        category = qa_item.get("category", "Unknown")
        
        if verbose:
            print(f"\n📝 質問: {question[:60]}...")
        
        context = self.retrieve_context(question)
        answer = self.generate_answer(question, context)
        
        coherence = self.evaluate_coherence(answer)
        relevance = self.evaluate_relevance(question, answer)
        groundedness = self.evaluate_groundedness(answer, context)
        
        if verbose:
            print(f"  Coherence: {coherence:.3f}")
            print(f"  Relevance: {relevance:.3f}")
            print(f"  Groundedness: {groundedness:.3f}")
        
        return {
            "question": question,
            "ground_truth": ground_truth,
            "generated_answer": answer,
            "category": category,
            "coherence": coherence,
            "relevance": relevance,
            "groundedness": groundedness,
            "context_count": len(context),
            "retrieved_context": [
                {
                    "title": c.get("title", ""),
                    "content": c.get("content", "")[:500],
                    "category": c.get("category", "")
                }
                for c in context
            ]
        }
    
    def evaluate_batch(self, qa_data: List[Dict], verbose: bool = False) -> Dict[str, Any]:
        results = []
        total = len(qa_data)
        
        print(f"\n🚀 バッチ評価開始: {total}件")
        
        for i, qa_item in enumerate(qa_data, 1):
            if verbose:
                print(f"\n{'='*60}")
                print(f"Progress: {i}/{total}")
            
            try:
                result = self.evaluate_single(qa_item, verbose=verbose)
                results.append(result)
            except Exception as e:
                print(f"❌ エラー (Q{i}): {e}")
                continue
        
        avg_coherence = sum(r["coherence"] for r in results) / len(results)
        avg_relevance = sum(r["relevance"] for r in results) / len(results)
        avg_groundedness = sum(r["groundedness"] for r in results) / len(results)
        
        category_stats = {}
        for r in results:
            cat = r["category"]
            if cat not in category_stats:
                category_stats[cat] = {
                    "count": 0,
                    "coherence": [],
                    "relevance": [],
                    "groundedness": []
                }
            category_stats[cat]["count"] += 1
            category_stats[cat]["coherence"].append(r["coherence"])
            category_stats[cat]["relevance"].append(r["relevance"])
            category_stats[cat]["groundedness"].append(r["groundedness"])
        
        for cat, stats in category_stats.items():
            stats["avg_coherence"] = sum(stats["coherence"]) / len(stats["coherence"])
            stats["avg_relevance"] = sum(stats["relevance"]) / len(stats["relevance"])
            stats["avg_groundedness"] = sum(stats["groundedness"]) / len(stats["groundedness"])
        
        return {
            "total_items": total,
            "evaluated_items": len(results),
            "average_scores": {
                "coherence": avg_coherence,
                "relevance": avg_relevance,
                "groundedness": avg_groundedness
            },
            "category_stats": category_stats,
            "results": results,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def main():
    parser = argparse.ArgumentParser(description="RAG Batch Evaluation v8")
    parser.add_argument("--qa-data", required=True, help="Q&Aデータファイルのパス")
    parser.add_argument("--output-dir", default="reports/evaluation_v8", help="出力ディレクトリ")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    with open(args.qa_data, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"✅ Q&Aデータ読み込み: {len(qa_data)}件")
    
    evaluator = RAGEvaluator()
    results = evaluator.evaluate_batch(qa_data, verbose=args.verbose)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("📊 評価完了")
    print(f"{'='*60}")
    print(f"\n平均スコア:")
    print(f"  Coherence: {results['average_scores']['coherence']:.3f}")
    print(f"  Relevance: {results['average_scores']['relevance']:.3f}")
    print(f"  Groundedness: {results['average_scores']['groundedness']:.3f}")
    
    print(f"\nカテゴリ別スコア:")
    for cat, stats in results['category_stats'].items():
        print(f"\n  {cat} ({stats['count']}件):")
        print(f"    Coherence: {stats['avg_coherence']:.3f}")
        print(f"    Relevance: {stats['avg_relevance']:.3f}")
        print(f"    Groundedness: {stats['avg_groundedness']:.3f}")
    
    print(f"\n💾 結果保存: {output_file}")


if __name__ == "__main__":
    main()