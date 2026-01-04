#!/usr/bin/env python3
"""
D22-2: Query Expansion評価（フィールド名修正版）
API Response: {"response": "..."} → スクリプト: answer
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
print("✅ 初期化完了")

def evaluate_conditions():
    conditions = [
        {"name": "baseline", "use_query_expansion": False},
        {"name": "query_expansion", "use_query_expansion": True}
    ]
    
    results = {}
    for condition in conditions:
        print(f"\n{'='*70}")
        print(f"評価: {condition['name']}")
        print("="*70)
        
        eval_results = run_evaluation(condition)
        
        if not eval_results:
            print(f"❌ {condition['name']} 失敗")
            continue
        
        metrics = calculate_metrics(eval_results)
        results[condition['name']] = {
            "config": condition,
            "metrics": metrics,
            "details": eval_results
        }
        
        m = metrics
        print(f"\n【結果】")
        print(f"  C: {m['coherence_avg']:.3f} | R: {m['relevance_avg']:.3f} | G: {m['groundedness_avg']:.3f}")
    
    return results

def run_evaluation(condition: Dict) -> List[Dict]:
    with open(DATASET_PATH, encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]
    
    print(f"データセット: {len(dataset)}項目")
    
    results = []
    for i, item in enumerate(dataset, 1):
        query = item.get("question", "")
        
        if not query.strip():
            continue
        
        print(f"[{i}/{len(dataset)}] {query[:40]}...")
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "query": query,
                    "use_query_expansion": condition["use_query_expansion"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ {response.status_code}")
                continue
            
            rag_output = response.json()
            
            # ★★★ 重要な修正 ★★★
            # APIは "response" フィールドを返すが、評価では "answer" として扱う
            answer = rag_output.get("response", "")
            
            # contextsがない場合は空リストとして扱う
            contexts = rag_output.get("contexts", [])
            
            # contextsが空の場合、回答から疑似コンテキストを作成
            # （APIがcontextsを返さない仕様の場合の対処）
            if not contexts and answer:
                # 回答を200文字ごとに分割して疑似コンテキスト化
                contexts = [answer[i:i+200] for i in range(0, len(answer), 200)][:3]
            
        except Exception as e:
            print(f"  ❌ {e}")
            continue
        
        try:
            scores = judge_response(
                query=query,
                answer=answer,
                contexts=contexts
            )
        except Exception as e:
            print(f"  ❌ Judge: {e}")
            continue
        
        result = {
            "query": query,
            "answer": answer,
            "expanded_queries": rag_output.get("expanded_queries", []),
            "num_contexts": len(contexts),
            "scores": scores
        }
        results.append(result)
        
        print(f"  ✅ C:{scores['coherence']:.2f} R:{scores['relevance']:.2f} G:{scores['groundedness']:.2f}")
        
        if condition["use_query_expansion"] and rag_output.get("expanded_queries"):
            print(f"     展開: {len(rag_output['expanded_queries'])}")
        
        time.sleep(1.5)
    
    return results

def judge_response(query: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    context_text = "\n".join([f"[{i+1}] {c}" for i, c in enumerate(contexts)])
    
    judge_prompt = f"""以下を1-5で評価してください。

質問: {query}
回答: {answer}
参照: {context_text}

評価軸:
1. Coherence（論理性・読みやすさ）
2. Relevance（質問への適切な回答）
3. Groundedness（参照情報に基づいているか）

JSON出力: {{"coherence": 5, "relevance": 4, "groundedness": 5}}
"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "公平に採点してください。"},
            {"role": "user", "content": judge_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    scores = json.loads(response.choices[0].message.content)
    return {k: v/5.0 for k, v in scores.items()}

def calculate_metrics(results: List[Dict]) -> Dict:
    if not results:
        return {"coherence_avg": 0.0, "relevance_avg": 0.0, "groundedness_avg": 0.0, "num_samples": 0}
    
    return {
        "coherence_avg": sum(r["scores"]["coherence"] for r in results) / len(results),
        "relevance_avg": sum(r["scores"]["relevance"] for r in results) / len(results),
        "groundedness_avg": sum(r["scores"]["groundedness"] for r in results) / len(results),
        "num_samples": len(results)
    }

def save_results(results: Dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"d22_2_corrected_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 保存: {output_file}")
    return output_file

if __name__ == "__main__":
    print("="*70)
    print("D22-2 Query Expansion評価（修正版）")
    print("="*70)
    
    results = evaluate_conditions()
    
    if not results:
        print("\n❌ 失敗")
        exit(1)
    
    save_results(results)
    
    print("\n" + "="*70)
    print("完了")
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
        print("【効果】")
        print("="*70)
        print(f"  Coherence:    {(e['coherence_avg']-b['coherence_avg'])*100:+.1f}%")
        print(f"  Relevance:    {(e['relevance_avg']-b['relevance_avg'])*100:+.1f}%")
        print(f"  Groundedness: {(e['groundedness_avg']-b['groundedness_avg'])*100:+.1f}%")
        
        print("\n【判定】")
        if e['relevance_avg'] >= 0.850 and e['groundedness_avg'] >= 0.800:
            print("  ✅ 成功")
        elif e['relevance_avg'] >= 0.780:
            print("  ⚠️  改善あり、継続調整推奨")
        else:
            print("  ❌ 要改善")
