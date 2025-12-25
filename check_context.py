import json

with open('reports/evaluation_test/evaluation_results.json', 'r') as f:
    data = json.load(f)

for i, result in enumerate(data['results'], 1):
    print(f"\n{'='*70}")
    print(f"Q{i}: {result['question'][:80]}...")
    print(f"\nGenerated Answer (最初の150文字):")
    # Unicode エスケープをデコード
    answer = result['generated_answer'].encode().decode('unicode_escape')
    print(answer[:150])
    
    print(f"\nGroundedness: {result['groundedness']}")
    print(f"Context count: {result['context_count']}")
    
    # 実際に検索で何が取得されたかは、resultsには含まれていない
    # → これが問題の本質
