#!/usr/bin/env python3
"""
Quick E2E Test Script for RAG API

D25-2: 手動実行用の簡易E2Eテスト
サーバー起動後、このスクリプトを実行して全機能を確認

Usage:
    python scripts/quick_e2e_test.py
    
    # 詳細出力
    python scripts/quick_e2e_test.py --verbose
"""
import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime

# Configuration
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1/rag"
TIMEOUT = 30

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    """セクションヘッダー出力"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_result(name: str, success: bool, message: str = "", elapsed: float = 0):
    """テスト結果出力"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    timing = f" ({elapsed:.2f}s)" if elapsed > 0 else ""
    print(f"  {status} {name}{timing}")
    if message and not success:
        print(f"       {Colors.YELLOW}{message}{Colors.RESET}")


def test_health_check(verbose: bool = False) -> tuple[bool, dict]:
    """ヘルスチェックテスト"""
    print_header("1. Health Check")
    
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=TIMEOUT)
        elapsed = time.time() - start
        
        data = response.json()
        
        if verbose:
            print(f"\n  Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 検証
        tests = [
            ("HTTP 200", response.status_code == 200, f"Got {response.status_code}"),
            ("Search healthy", data.get("search_service") == "healthy", data.get("search_service", "N/A")),
            ("OpenAI healthy", data.get("openai_service") == "healthy", data.get("openai_service", "N/A")),
            ("Cosmos DB status", "cosmos_db" in data, "Field missing"),
            ("Response time < 5s", elapsed < 5.0, f"{elapsed:.2f}s"),
        ]
        
        all_passed = True
        for name, success, msg in tests:
            print_result(name, success, msg if not success else "", elapsed if name == "Response time < 5s" else 0)
            if not success:
                all_passed = False
        
        return all_passed, data
        
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False, {}


def test_hybrid_search(verbose: bool = False) -> tuple[bool, dict]:
    """ハイブリッド検索テスト"""
    print_header("2. Hybrid Search")
    
    try:
        payload = {
            "query": "Azure AI Searchでベクトル検索を設定する方法",
            "top_k": 5
        }
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/search",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start
        
        data = response.json()
        
        if verbose:
            print(f"\n  Query: {payload['query']}")
            print(f"  Results: {data.get('total_count', 0)} documents")
            if data.get("results"):
                for i, r in enumerate(data["results"][:3], 1):
                    print(f"    {i}. {r.get('title', 'N/A')[:50]}... (score: {r.get('score', 0):.4f})")
        
        # 検証
        tests = [
            ("HTTP 200", response.status_code == 200, f"Got {response.status_code}"),
            ("Has results", data.get("total_count", 0) > 0, "No results"),
            ("Results have scores", all("score" in r for r in data.get("results", [])), "Missing scores"),
            ("Response time < 10s", elapsed < 10.0, f"{elapsed:.2f}s"),
        ]
        
        all_passed = True
        for name, success, msg in tests:
            print_result(name, success, msg if not success else "", elapsed if "time" in name else 0)
            if not success:
                all_passed = False
        
        return all_passed, data
        
    except Exception as e:
        print_result("Hybrid Search", False, str(e))
        return False, {}


def test_rag_chat(verbose: bool = False) -> tuple[bool, dict]:
    """RAG Chatテスト"""
    print_header("3. RAG Chat")
    
    try:
        payload = {
            "message": "Azure AI Searchでハイブリッド検索を実装する方法を教えてください",
            "top_k": 5,
            "temperature": 0.7,
            "use_query_expansion": False
        }
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start
        
        data = response.json()
        
        if verbose:
            print(f"\n  Question: {payload['message'][:60]}...")
            print(f"  Answer: {data.get('answer', 'N/A')[:200]}...")
            print(f"  Sources: {len(data.get('sources', []))} references")
            print(f"  Model: {data.get('model', 'N/A')}")
        
        # 検証
        tests = [
            ("HTTP 200", response.status_code == 200, f"Got {response.status_code}"),
            ("Has answer", len(data.get("answer", "")) > 0, "Empty answer"),
            ("Has sources", "sources" in data, "Missing sources"),
            ("Has model info", "model" in data, "Missing model"),
            ("Response time < 15s", elapsed < 15.0, f"{elapsed:.2f}s"),
        ]
        
        all_passed = True
        for name, success, msg in tests:
            print_result(name, success, msg if not success else "", elapsed if "time" in name else 0)
            if not success:
                all_passed = False
        
        return all_passed, data
        
    except Exception as e:
        print_result("RAG Chat", False, str(e))
        return False, {}


def test_query_expansion(verbose: bool = False) -> tuple[bool, dict]:
    """Query Expansionテスト"""
    print_header("4. Query Expansion")
    
    try:
        payload = {
            "message": "RAGシステムの構築方法",
            "top_k": 5,
            "use_query_expansion": True
        }
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start
        
        data = response.json()
        
        if verbose:
            print(f"\n  Original: {payload['message']}")
            if data.get("expanded_queries"):
                print(f"  Expanded queries:")
                for i, q in enumerate(data["expanded_queries"], 1):
                    print(f"    {i}. {q}")
        
        # 検証
        tests = [
            ("HTTP 200", response.status_code == 200, f"Got {response.status_code}"),
            ("Has expanded_queries", data.get("expanded_queries") is not None, "Missing field"),
            ("Multiple queries", len(data.get("expanded_queries", [])) >= 1, "No expansion"),
            ("Response time < 20s", elapsed < 20.0, f"{elapsed:.2f}s"),
        ]
        
        all_passed = True
        for name, success, msg in tests:
            print_result(name, success, msg if not success else "", elapsed if "time" in name else 0)
            if not success:
                all_passed = False
        
        return all_passed, data
        
    except Exception as e:
        print_result("Query Expansion", False, str(e))
        return False, {}


def test_multi_turn_conversation(verbose: bool = False) -> tuple[bool, dict]:
    """マルチターン会話テスト"""
    print_header("5. Multi-turn Conversation (Cosmos DB)")
    
    try:
        # Turn 1
        payload1 = {
            "message": "Managed Identityとは何ですか？",
            "top_k": 3,
            "include_history": True
        }
        
        start = time.time()
        response1 = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat/with-history",
            json=payload1,
            timeout=TIMEOUT
        )
        elapsed1 = time.time() - start
        
        data1 = response1.json()
        session_id = data1.get("session_id")
        
        if verbose:
            print(f"\n  Turn 1: {payload1['message']}")
            print(f"  Session: {session_id}")
            print(f"  Turn #: {data1.get('turn_number')}")
            print(f"  History used: {data1.get('history_used')}")
        
        # 検証 Turn 1
        turn1_passed = all([
            response1.status_code == 200,
            session_id is not None,
            data1.get("turn_number") == 1,
            data1.get("history_used") == 0
        ])
        print_result("Turn 1 - Session created", turn1_passed, "", elapsed1)
        
        # 少し待機
        time.sleep(1)
        
        # Turn 2
        payload2 = {
            "message": "それをAzure AI Searchで使う方法は？",
            "session_id": session_id,
            "top_k": 3,
            "include_history": True,
            "max_history_turns": 5
        }
        
        start = time.time()
        response2 = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat/with-history",
            json=payload2,
            timeout=TIMEOUT
        )
        elapsed2 = time.time() - start
        
        data2 = response2.json()
        
        if verbose:
            print(f"\n  Turn 2: {payload2['message']}")
            print(f"  Turn #: {data2.get('turn_number')}")
            print(f"  History used: {data2.get('history_used')}")
        
        # 検証 Turn 2
        turn2_passed = all([
            response2.status_code == 200,
            data2.get("session_id") == session_id,
            data2.get("turn_number") == 2,
            data2.get("history_used", 0) >= 1
        ])
        print_result("Turn 2 - History used", turn2_passed, 
                    f"history_used={data2.get('history_used')}" if not turn2_passed else "", elapsed2)
        
        return turn1_passed and turn2_passed, {"turn1": data1, "turn2": data2}
        
    except Exception as e:
        print_result("Multi-turn Conversation", False, str(e))
        return False, {}


def main():
    parser = argparse.ArgumentParser(description="Quick E2E Test for RAG API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}RAG API E2E Test Suite{Colors.RESET}")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # サーバー接続確認
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}Error: Server not running at {BASE_URL}{Colors.RESET}")
        print("Start the server with: uvicorn app.main:app --port 8000")
        sys.exit(1)
    
    # テスト実行
    results.append(("Health Check", test_health_check(args.verbose)[0]))
    results.append(("Hybrid Search", test_hybrid_search(args.verbose)[0]))
    results.append(("RAG Chat", test_rag_chat(args.verbose)[0]))
    results.append(("Query Expansion", test_query_expansion(args.verbose)[0]))
    results.append(("Multi-turn Conversation", test_multi_turn_conversation(args.verbose)[0]))
    
    # サマリー
    print_header("Summary")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, success in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if success else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} {name}")
    
    print(f"\n  {Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed! ✓{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed! ✗{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
