"""RAG API E2E テスト"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    print("\n=== GET /api/v1/rag/health ===")
    r = requests.get(f"{BASE_URL}/rag/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


def test_search():
    print("\n=== POST /api/v1/rag/search ===")
    r = requests.post(f"{BASE_URL}/rag/search", json={"query": "Azure AI Search", "top_k": 3})
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Total: {data.get('total_count', 0)} results")
    for res in data.get("results", [])[:2]:
        print(f"  - {res['title']}: {res['content'][:50]}...")


def test_chat():
    print("\n=== POST /api/v1/rag/chat ===")
    r = requests.post(
        f"{BASE_URL}/rag/chat",
        json={"message": "Azure AI Searchとは何ですか？", "top_k": 3, "max_tokens": 300}
    )
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Answer: {data.get('answer', '')[:200]}...")
    print(f"Sources: {len(data.get('sources', []))}")


if __name__ == "__main__":
    try:
        test_health()
        test_search()
        test_chat()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")