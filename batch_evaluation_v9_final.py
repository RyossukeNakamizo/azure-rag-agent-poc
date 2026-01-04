#!/usr/bin/env python3
"""
D22-2: Query Expansion効果の評価スクリプト（フィールド名修正版）
データセット: question → API: query
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
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/health"
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
    """FastAPI健全性チェック"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print(f"✅ FastAPI接続成功: {API_BASE_URL}")
            return True
    except:
        pass
    return False

def evaluate_conditions():
    """2条件での評価実行"""
    conditions = [
        {"name": "baseline", "use_query_expansion": False},
        {"name": "query_expansion", "use_query_expansion": True}
    ]
    
    results = {}
    for condition in conditions:
        print(f"\n{'='*70}")
        print(f"評価条件: {condition['name']}")
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
    
    return results

def run_evaluation(condition: Dict) -> List[Dict]:
    """評価実行"""
    with open(DATASET_PATH, encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]
    
    print(f"データセット読込: {len(dataset)}項目")
    
    results = []
    for i, item in enumerate(dataset, 1):
        # データセットから question フィールドを取得
        query = item.get("question", "")
        
        if not query or not query.strip():
            print(f"[{i}/{len(dataset)}] ⚠️  Queryが空 - スキップ")
            continue
        
        print(f"\n[{i}/{len(dataset)}] Query: {query[:60]}...")
        
        try:
            # APIには query フィールドで送信
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "query": query,  # ← ここを修正
                    "use_query_expansion": condition["use_query_expansion"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ API Error: {response.status_code}")
                print(f"     {response.text[:200]}")
                continue
            
            rag_output = response.json()
            
        except Exception as e:
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
        
        print(f"  ✅ C:{scores['coherence']:.3f} R:{scores['relevance']:.3f} G:{scores['groundedness']:.3f}")
        
        if condition["use_query_expansion"] and rag_output.get("expanded_queries"):
            print(f"     展開: {len(rag_output['expanded_queries'])}クエリ")
        
        time.sleep(1.5)
    
    return results

def judge_response(query: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    """LLM-as-Judge評価"""
    context_text = "\n".join([f"[{i+1}] {c}" for i, c in enumerate(contexts)])
    
    judge_prompt = f"""以下を評価してください。

質問: {query}
回答: {answer}
コンテキスト:\n{context_text}

1-5で評価（JSON形式）:
- Coherence（論理性）
- Relevance（関連性）  
- Groundedness（事実性）

{{"coherence": 5, "relevance": 4, "groundedness": 5}}
"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "公平な評価者として採点してください。"},
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
    
    return {
        "coherence_avg": sum(r["scores"]["coherence"] for r in results) / len(results),
        "relevance_avg": sum(r["scores"]["relevance"] for r in results) / len(results),
        "groundedness_avg": sum(r["scores"]["groundedness"] for r in results) / len(results),
        "num_samples": len(results)
    }

def save_results(results: Dict):
    """結果保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"d22_2_evaluation_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果保存: {output_file}")
    return output_file

if __name__ == "__main__":
    print("="*70)
    print("D22-2 Query Expansion評価")
    print("="*70)
    
    if not check_api_health():
        print("⚠️  FastAPI接続警告")
    
    results = evaluate_conditions()
    
    if not results:
        print("\n❌ 評価失敗")
        exit(1)
    
    save_results(results)
    
    # サマリー
    print("\n" + "="*70)
    print("評価完了")
    print("="*70)
    
    for name, data in results.items():
        m = data['metrics']
        print(f"\n【{name}】")
        print(f"  Coherence:    {m['coherence_avg']:.3f}")
        print(f"  Relevance:    {m['relevance_avg']:.3f}")
        print(f"  Groundedness: {m['groundedness_avg']:.3f}")
    
    if "baseline" in results and "query_expansion" in results:
        b = results["baseline"]["metrics"]
        e = results["query_expansion"]["metrics"]
        
        print("\n" + "="*70)
        print("【Query Expansion効果】")
        print("="*70)
        print(f"  Coherence:    {(e['coherence_avg']-b['coherence_avg'])*100:+.1f}%")
        print(f"  Relevance:    {(e['relevance_avg']-b['relevance_avg'])*100:+.1f}%")
        print(f"  Groundedness: {(e['groundedness_avg']-b['groundedness_avg'])*100:+.1f}%")
        
        print("\n【判定】")
        if e['relevance_avg'] >= 0.850 and e['groundedness_avg'] >= 0.800:
            print("  ✅ 成功: Query Expansion採用推奨")
        elif e['relevance_avg'] >= 0.850:
            print("  ⚠️  Relevance改善だがGroundedness要改善")
        else:
            print("  ❌ 目標未達: 追加施策検討")
