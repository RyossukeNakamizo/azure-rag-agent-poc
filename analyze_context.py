import json

with open('reports/evaluation_with_context/evaluation_results.json', 'r') as f:
    data = json.load(f)

for i, result in enumerate(data['results'], 1):
    print(f"\n{'='*70}")
    print(f"Q{i}: {result['question']}")
    print(f"\nGroundedness: {result['groundedness']:.3f}")
    
    if 'retrieved_context' in result:
        print(f"\n取得コンテキスト ({len(result['retrieved_context'])}件):")
        for j, ctx in enumerate(result['retrieved_context'], 1):
            print(f"\n  [{j}] {ctx.get('title', 'No title')}")
            print(f"      Category: {ctx.get('category', 'N/A')}")
            content = ctx.get('content', '')
            print(f"      Content length: {len(content)} chars")
            print(f"      Content preview: {content[:200]}...")
    else:
        print("  ⚠️ retrieved_context がありません")
    
    print(f"\n生成された回答 (最初の300文字):")
    answer = result['generated_answer']
    print(f"  {answer[:300]}...")
