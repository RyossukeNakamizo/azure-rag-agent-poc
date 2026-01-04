#!/usr/bin/env python3
"""
D22-2: Query Expansion効果の評価スクリプト（ヘルスチェック修正版）
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import requests
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

# 設定
API_BASE_URL = "http://localhost:8000"
DATASET_PATH = "evaluation/evaluation_dataset_25items.jsonl"
OUTPUT_DIR = Path("evaluation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Azure OpenAI初期化中...")
credential = DefaultAzureCredential()

def get_azure_token():
    return credential.get_token("https://cognitiveservices.azure.com/.default").token

openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=get_azure_token,
    api_version="2024-10-01-preview"
)
print("✅ Azure OpenAI初期化完了")

def check_api_health():
    """FastAPI健全性チェック（/chatエンドポイントで確認）"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": "test"},
            timeout=5
        )
        if response.status_code in [200, 422]:
            print(f"✅ FastAPI接続成功: {API_BASE_URL}")
            return True
        else:
            print(f"❌ FastAPI応答異常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FastAPI接続失敗: {e}")
        return False

def evaluate_conditions():
    """2条件での評価実行"""
    conditions = [
        {"name": "baseline", "use_query_expansion": False, "description": "D21-4再現（Query Expansion無効）"},
        {"name": "query_expansion", "use_query_expansion": True, "description": "Query Expansion有効"}
    ]
    
    results = {}
    for condition in conditions:
        print(f"\n{'='*70}")
        print(f"評価条件: {condition['name']}")
        print(f"説明: {condition['description']}")
        print(f"{'='*70}")
        
        eval_results = run_evaluation(condition)
        
        if not eval_results:
            print(f"❌ {condition['name']} 評価失敗")
            continue
        
        metrics = calculate_metrics(eval_results)
        
        results[condition['name']] = {
            "config": condition,
            "metrics": metrics,
            "details": eval_results
        }
        
        print(f"\n【{condition['name']} 結果】")
        print(f"  Coherence:    {metrics['coherence_avg']:.3f}")
        print(f"  Relevance:    {metrics['relevance_avg']:.3f}")
        print(f"  Groundedness: {metrics['groundedness_avg']:.3f}")
        print(f"  サンプル数:    {metrics['num_samples']}")
    
    return results

def run_evaluation(condition: Dict) -> List[Dict]:
    """評価データセット全25項目を実行"""
    if not Path(DATASET_PATH).exists():
        print(f"❌ データセット不在: {DATASET_PATH}")
        return []
    
    with open(DATASET_PATH, encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]
    
    print(f"データセット読込: {len(dataset)}項目")
    
    results = []
    for i, item in enumerate(dataset, 1):
        query = item.get("query", "")
        print(f"\n[{i}/{len(dataset)}] Query: {query[:60]}...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": query,
                    "use_query_expansion": condition["use_query_expansion"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ API Error: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                continue
            
            rag_output = response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request Error: {e}")
            continue
        
        try:
            scores = judge_response(
                query=query,
                answer=rag_output.get("answer", ""),
                contexts=rag_output.get("contexts", [])
            )
        except Exception as e:
            print(f"  ❌ Judge Error: {e}")
            continue
        
        result = {
            "query": query,
            "answer": rag_output.get("answer", ""),
            "expanded_queries": rag_output.get("expanded_queries", []),
            "num_contexts": len(rag_output.get("contexts", [])),
            "scores": scores
        }
        results.append(result)
        
        print(f"  ✅ Coherence: {scores['coherence']:.3f} | "
              f"Relevance: {scores['relevance']:.3f} | "
              f"Groundedness: {scores['groundedness']:.3f}")
        
        if condition["use_query_expansion"] and rag_output.get("expanded_queries"):
            print(f"     展開クエリ数: {len(rag_output['expanded_queries'])}")
        
        time.sleep(1.5)
    
    return results

def judge_response(query: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    """LLM-as-Judge評価"""
    context_text = "\n".join([f"[{i+1}] {c}" for i, c in enumerate(contexts)])
    
    judge_prompt = f"""以下の質問と回答を評価してください。

質問: {query}

回答: {answer}

参照コンテキスト:
{context_text}

以下3つの観点で1-5のスコアを付けてください：

1. Coherence（一貫性）: 回答が論理的で読みやすいか
2. Relevance（関連性）: 回答が質問に適切に答えているか
3. Groundedness（事実性）: 回答がコンテキストの情報のみに基づいているか

JSON形式で出力してください：
{{"coherence": 5, "relevance": 4, "groundedness": 5}}
"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは公平で厳格な評価者です。"},
            {"role": "user", "content": judge_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    scores = json.loads(response.choices[0].message.content)
    return {k: v/5.0 for k, v in scores.items()}

def calculate_metrics(results: List[Dict]) -> Dict:
    """メトリクス集計"""
    if not results:
        return {"coherence_avg": 0.0, "relevance_avg": 0.0, "groundedness_avg": 0.0, "num_samples": 0}
    
    coherence_scores = [r["scores"]["coherence"] for r in results]
    relevance_scores = [r["scores"]["relevance"] for r in results]
    groundedness_scores = [r["scores"]["groundedness"] for r in results]
    
    return {
        "coherence_avg": sum(coherence_scores) / len(coherence_scores),
        "relevance_avg": sum(relevance_scores) / len(relevance_scores),
        "groundedness_avg": sum(groundedness_scores) / len(groundedness_scores),
        "num_samples": len(results)
    }

def save_results(results: Dict):
    """結果保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_file = OUTPUT_DIR / f"d22_2_evaluation_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 詳細結果保存: {output_file}")
    
    summary_file = OUTPUT_DIR / f"d22_2_summary_{timestamp}.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("D22-2 Query Expansion評価サマリー\n")
        f.write("="*70 + "\n\n")
        
        for name, data in results.items():
            f.write(f"【{name}】\n")
            f.write(f"  Coherence:    {data['metrics']['coherence_avg']:.3f}\n")
            f.write(f"  Relevance:    {data['metrics']['relevance_avg']:.3f}\n")
            f.write(f"  Groundedness: {data['metrics']['groundedness_avg']:.3f}\n\n")
        
        if "baseline" in results and "query_expansion" in results:
            baseline = results["baseline"]["metrics"]
            expansion = results["query_expansion"]["metrics"]
            
            f.write("【Query Expansion効果】\n")
            f.write(f"  Coherence変化:    {(expansion['coherence_avg'] - baseline['coherence_avg'])*100:+.1f}%\n")
            f.write(f"  Relevance改善:    {(expansion['relevance_avg'] - baseline['relevance_avg'])*100:+.1f}%\n")
            f.write(f"  Groundedness変化: {(expansion['groundedness_avg'] - baseline['groundedness_avg'])*100:+.1f}%\n")
    
    print(f"✅ サマリー保存: {summary_file}")
    return output_file, summary_file

if __name__ == "__main__":
    print("="*70)
    print("D22-2 Query Expansion評価開始")
    print("="*70)
    print(f"データセット: {DATASET_PATH}")
    print(f"出力先: {OUTPUT_DIR}")
    
    if not check_api_health():
        print("\n⚠️  FastAPI接続警告（評価を続行します）")
    
    results = evaluate_conditions()
    
    if not results:
        print("\n❌ 評価失敗")
        exit(1)
    
    output_file, summary_file = save_results(results)
    
    print("\n" + "="*70)
    print("評価完了")
    print("="*70)
