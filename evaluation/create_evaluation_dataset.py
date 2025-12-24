# === create_evaluation_dataset.py (完全版 100問) ===
import json
from typing import List, Dict

def create_evaluation_dataset() -> List[Dict]:
    """評価データセット100問を生成（完全版）"""
    
    dataset = []
    
    # ===================================
    # カテゴリ1: Azure AI Search基礎（30問）
    # ===================================
    
    # サブカテゴリ1.1: インデックス作成・管理（10問）
    dataset.extend([
        {
            "id": "ais_idx_001",
            "category": "Azure AI Search - Index Management",
            "difficulty": "basic",
            "question": "Azure AI Searchでベクトル検索可能なインデックスを作成する際、フィールド定義で必須の設定は何ですか？",
            "ground_truth": "ベクトルフィールドには以下が必須です：(1) type: Collection(Single)、(2) searchable: true、(3) vector_search_dimensions（例: 1536）、(4) vector_search_profile_name（HNSWプロファイル参照）。",
            "context_keywords": ["SearchField", "vector_search_dimensions", "HNSW"],
            "expected_sources": ["Azure AI Search公式ドキュメント"]
        },
        {
            "id": "ais_idx_002",
            "category": "Azure AI Search - Index Management",
            "difficulty": "intermediate",
            "question": "既存のインデックスにフィールドを追加する場合、どのような制約がありますか？",
            "ground_truth": "既存インデックスへのフィールド追加には以下の制約があります：(1) キーフィールド（key=True）は変更不可、(2) 既存フィールドのデータ型変更は不可、(3) ベクトルフィールドの次元数変更は不可、(4) フィールド追加後は既存ドキュメントで新フィールドはnull。",
            "context_keywords": ["updateIndex", "フィールド追加", "制約"],
            "expected_sources": ["Azure AI Search REST API"]
        },
        {
            "id": "ais_idx_003",
            "category": "Azure AI Search - Index Management",
            "difficulty": "basic",
            "question": "Azure AI SearchのインデックスでSimpleFieldとSearchableFieldの違いは何ですか？",
            "ground_truth": "SimpleFieldはフィルタリング・ソート用で全文検索不可。SearchableFieldは全文検索可能でアナライザー適用。例: IDやカテゴリはSimpleField、本文はSearchableField。",
            "context_keywords": ["SimpleField", "SearchableField", "searchable"],
            "expected_sources": ["SearchField API reference"]
        },
        {
            "id": "ais_idx_004",
            "category": "Azure AI Search - Index Management",
            "difficulty": "intermediate",
            "question": "インデックスのスキーマ変更でダウンタイムを最小化する方法は？",
            "ground_truth": "Blue-Greenデプロイメント手法：(1) 新スキーマで別インデックス作成、(2) データを並行インジェスト、(3) アプリケーションのエイリアスを切り替え、(4) 旧インデックス削除。",
            "context_keywords": ["Blue-Green", "ダウンタイム", "スキーマ変更"],
            "expected_sources": ["Azure Architecture patterns"]
        },
        {
            "id": "ais_idx_005",
            "category": "Azure AI Search - Index Management",
            "difficulty": "advanced",
            "question": "10万ドキュメントのインデックス再構築でパフォーマンスを最大化する設定は？",
            "ground_truth": "以下の最適化：(1) Indexerのバッチサイズ増加（maxBatchSize: 1000）、(2) 並列度上昇（maxDegreeOfParallelism: 10）、(3) インデックス作成中はreplicaCount=1に削減。",
            "context_keywords": ["Indexer", "maxBatchSize", "パフォーマンス最適化"],
            "expected_sources": ["Indexer performance tuning"]
        },
        {
            "id": "ais_idx_006",
            "category": "Azure AI Search - Index Management",
            "difficulty": "basic",
            "question": "インデックスの削除コマンド（Python SDK）を教えてください。",
            "ground_truth": "index_client.delete_index(index_name)。削除は即座に実行され復元不可。",
            "context_keywords": ["delete_index", "SearchIndexClient"],
            "expected_sources": ["Python SDK reference"]
        },
        {
            "id": "ais_idx_007",
            "category": "Azure AI Search - Index Management",
            "difficulty": "intermediate",
            "question": "インデックスのバックアップとリストア方法を教えてください。",
            "ground_truth": "Azure AI Searchには組み込みバックアップ機能なし。代替策：(1) ドキュメント全件Export、(2) JSON保存、(3) 新インデックスに再インジェスト。",
            "context_keywords": ["バックアップ", "Export", "Indexer"],
            "expected_sources": ["Disaster recovery patterns"]
        },
        {
            "id": "ais_idx_008",
            "category": "Azure AI Search - Index Management",
            "difficulty": "advanced",
            "question": "マルチテナントアプリケーションでインデックス分離戦略を設計してください。",
            "ground_truth": "3つのパターン：(1) テナント毎に個別インデックス（隔離性高）、(2) 単一インデックス+tenantIdフィルタ（コスト最適）、(3) ハイブリッド（大口テナントは個別）。",
            "context_keywords": ["マルチテナント", "データ分離", "tenantId"],
            "expected_sources": ["Multi-tenant architecture"]
        },
        {
            "id": "ais_idx_009",
            "category": "Azure AI Search - Index Management",
            "difficulty": "basic",
            "question": "インデックスの統計情報（ドキュメント数、ストレージサイズ）を取得する方法は？",
            "ground_truth": "index_client.get_index_statistics(index_name)。返り値: {'document_count': 12345, 'storage_size': 5242880}。",
            "context_keywords": ["get_index_statistics", "document_count"],
            "expected_sources": ["SearchIndexClient API"]
        },
        {
            "id": "ais_idx_010",
            "category": "Azure AI Search - Index Management",
            "difficulty": "intermediate",
            "question": "インデックスのアナライザー設定でカスタム日本語形態素解析を実装する方法は？",
            "ground_truth": "customAnalyzerを定義：{'name': 'ja_analyzer', 'tokenizer': 'microsoft_language_tokenizer'}。フィールド定義でanalyzer='ja_analyzer'指定。",
            "context_keywords": ["CustomAnalyzer", "日本語", "tokenizer"],
            "expected_sources": ["Analyzer configuration"]
        }
    ])
    
    # サブカテゴリ1.2: ベクトル検索設定（10問）
    dataset.extend([
        {
            "id": "ais_vec_001",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "basic",
            "question": "HNSWアルゴリズムのパラメータm、efConstruction、efSearchの推奨値は？",
            "ground_truth": "推奨デフォルト値：m=4（グラフ接続数）、efConstruction=400（構築品質）、efSearch=500（検索品質）。精度優先ならm=16、速度優先ならm=4。",
            "context_keywords": ["HNSW", "m", "efConstruction"],
            "expected_sources": ["Vector search configuration"]
        },
        {
            "id": "ais_vec_002",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "intermediate",
            "question": "ベクトル検索でコサイン類似度とユークリッド距離の使い分けは？",
            "ground_truth": "Azure AI Searchはコサイン類似度がデフォルト（正規化済みベクトル前提）。埋め込みモデル（ada-002等）は正規化済みなのでコサイン類似度が適切。",
            "context_keywords": ["cosine", "euclidean", "similarityFunction"],
            "expected_sources": ["Vector similarity metrics"]
        },
        {
            "id": "ais_vec_003",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "advanced",
            "question": "100万ドキュメントでHNSWのメモリ消費を見積もる計算式は？",
            "ground_truth": "概算式：memory(GB) ≈ (dimensions × 4bytes × document_count × (m + 1)) / 1GB。例: 1536次元、100万件、m=4の場合 ≈ 28GB。",
            "context_keywords": ["HNSW", "メモリ消費", "スケーリング"],
            "expected_sources": ["Memory optimization"]
        },
        {
            "id": "ais_vec_004",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "basic",
            "question": "VectorizedQueryとVectorizableTextQueryの違いは？",
            "ground_truth": "VectorizedQuery: 事前計算済みベクトルを渡す。VectorizableTextQuery: テキストをAzure側で自動ベクトル化。後者はIntegrated Vectorization機能。",
            "context_keywords": ["VectorizedQuery", "VectorizableTextQuery"],
            "expected_sources": ["Query types documentation"]
        },
        {
            "id": "ais_vec_005",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "intermediate",
            "question": "ベクトル検索のk_nearest_neighbors（k値）の最適化方法は？",
            "ground_truth": "k値は用途に応じて調整：RAG用途はk=3-10（LLMコンテキスト制約）、レコメンデーションはk=20-50。評価指標はRecall@k。",
            "context_keywords": ["k_nearest_neighbors", "Recall@k", "最適化"],
            "expected_sources": ["Vector search best practices"]
        },
        {
            "id": "ais_vec_006",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "advanced",
            "question": "Exhaustive KNNとHNSWの精度とレイテンシのトレードオフを数値で比較してください。",
            "ground_truth": "10万件での実測例：Exhaustive KNN（精度100%、レイテンシ2500ms）、HNSW m=4（精度99.2%、レイテンシ150ms）。HNSWは約90%のレイテンシ削減。",
            "context_keywords": ["Exhaustive KNN", "HNSW", "トレードオフ"],
            "expected_sources": ["Algorithm comparison"]
        },
        {
            "id": "ais_vec_007",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "basic",
            "question": "ベクトル検索のフィルタリング（filter句）はどのタイミングで適用されますか？",
            "ground_truth": "Azure AI Searchはpost-filteringを採用：(1) ベクトル検索でk件取得、(2) filter条件適用、(3) 条件一致のみ返却。対策: k値を大きく設定。",
            "context_keywords": ["filter", "post-filtering", "k値"],
            "expected_sources": ["Vector search with filters"]
        },
        {
            "id": "ais_vec_008",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "intermediate",
            "question": "複数ベクトルフィールド（multi-vector）の検索シナリオを教えてください。",
            "ground_truth": "例: titleVectorとcontentVectorを別管理。クエリで両方検索し重み付け統合：VectorizedQuery(fields='titleVector', weight=2.0)。",
            "context_keywords": ["multi-vector", "weight", "重み付け"],
            "expected_sources": ["Advanced vector scenarios"]
        },
        {
            "id": "ais_vec_009",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "advanced",
            "question": "ベクトルインデックスの再構築なしで埋め込みモデルを変更する方法はありますか？",
            "ground_truth": "不可能。埋め込み次元数が異なる場合、インデックス再作成必須。移行はBlue-Greenデプロイ推奨。",
            "context_keywords": ["埋め込みモデル変更", "インデックス再構築"],
            "expected_sources": ["Model migration guide"]
        },
        {
            "id": "ais_vec_010",
            "category": "Azure AI Search - Vector Search",
            "difficulty": "intermediate",
            "question": "ベクトル検索のデバッグで@search.scoreの値をどう解釈しますか？",
            "ground_truth": "@search.scoreはコサイン類似度ベース（0-1）。デバッグ: score > 0.8（高関連）、0.6-0.8（中関連）、< 0.6（低関連）。",
            "context_keywords": ["@search.score", "コサイン類似度"],
            "expected_sources": ["Scoring profiles"]
        }
    ])
    
    # サブカテゴリ1.3: ハイブリッド検索（10問）
    dataset.extend([
        {
            "id": "ais_hyb_001",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "basic",
            "question": "ハイブリッド検索の実装で必須のパラメータは何ですか？",
            "ground_truth": "search_text（キーワード）とvector_queries（ベクトル）の両方指定。片方のみでも動作するが両方で精度向上。",
            "context_keywords": ["search_text", "vector_queries"],
            "expected_sources": ["Hybrid search tutorial"]
        },
        {
            "id": "ais_hyb_002",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "intermediate",
            "question": "RRF（Reciprocal Rank Fusion）のk値の役割を教えてください。",
            "ground_truth": "RRFスコア計算式: score = Σ(1 / (k + rank_i))。k値（デフォルト60）は順位の影響度調整。Azure AI SearchはRRFを自動適用。",
            "context_keywords": ["RRF", "k値", "スコアリング"],
            "expected_sources": ["RRF algorithm"]
        },
        {
            "id": "ais_hyb_003",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "advanced",
            "question": "ハイブリッド検索でキーワードとベクトルの重み調整は可能ですか？",
            "ground_truth": "2024年時点では不可。RRFスコアは固定アルゴリズム。回避策: セマンティックランキング適用、またはアプリ層で再ランキング。",
            "context_keywords": ["重み調整", "RRF", "再ランキング"],
            "expected_sources": ["Scoring customization"]
        },
        {
            "id": "ais_hyb_004",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "basic",
            "question": "ハイブリッド検索でベクトルのみヒットしキーワードが0件の場合の動作は？",
            "ground_truth": "ベクトル検索結果のみ返却（キーワード0件でもエラーにならない）。RRFはベクトルスコアのみで計算。",
            "context_keywords": ["ハイブリッド検索", "ベクトルのみ"],
            "expected_sources": ["Hybrid search behavior"]
        },
        {
            "id": "ais_hyb_005",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "intermediate",
            "question": "日本語クエリでのハイブリッド検索の精度最適化方法は？",
            "ground_truth": "最適化：(1) アナライザーにja.microsoft指定、(2) 日本語特化埋め込みモデル使用、(3) 表記ゆれ対策（synonymMap）。",
            "context_keywords": ["日本語", "アナライザー", "表記ゆれ"],
            "expected_sources": ["Japanese language support"]
        },
        {
            "id": "ais_hyb_006",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "advanced",
            "question": "ハイブリッド検索のベンチマークで評価すべき指標を3つ挙げてください。",
            "ground_truth": "(1) MRR（Mean Reciprocal Rank）、(2) NDCG@k（ランキング品質）、(3) Recall@k（正解含有率）。実装はRAGASライブラリで自動計算可能。",
            "context_keywords": ["MRR", "NDCG", "Recall"],
            "expected_sources": ["Information retrieval metrics"]
        },
        {
            "id": "ais_hyb_007",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "basic",
            "question": "ハイブリッド検索でtop=5を指定した場合、キーワード5件+ベクトル5件の計10件返りますか？",
            "ground_truth": "いいえ、合計5件のみ。RRFでキーワードとベクトル結果を統合しtop件に絞り込む。",
            "context_keywords": ["top", "ハイブリッド検索", "マージ"],
            "expected_sources": ["Hybrid search results"]
        },
        {
            "id": "ais_hyb_008",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "intermediate",
            "question": "クエリ拡張（Query Expansion）をハイブリッド検索に組み込む方法は？",
            "ground_truth": "LLM経由でクエリを拡張：元クエリ → LLMで関連語生成 → 拡張クエリで検索実行。Prompt FlowのPre-processing Nodeで実装可能。",
            "context_keywords": ["Query Expansion", "LLM", "関連語"],
            "expected_sources": ["Query enhancement"]
        },
        {
            "id": "ais_hyb_009",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "advanced",
            "question": "ハイブリッド検索のキャッシュ戦略を設計してください。",
            "ground_truth": "2層キャッシュ：(1) クエリキャッシュ（Redis）で結果を30分保存、(2) 埋め込みキャッシュでベクトルを1日保存。ヒット率目標70%。",
            "context_keywords": ["キャッシュ", "Redis", "埋め込みキャッシュ"],
            "expected_sources": ["Caching strategies"]
        },
        {
            "id": "ais_hyb_010",
            "category": "Azure AI Search - Hybrid Search",
            "difficulty": "intermediate",
            "question": "セマンティックランキングをハイブリッド検索に追加する設定方法は？",
            "ground_truth": "query_type='semantic'とsemantic_configuration_name指定。Standard以上のSKU必要、無料枠1000クエリ/月。精度+5-10%向上。",
            "context_keywords": ["semantic", "query_type"],
            "expected_sources": ["Semantic search"]
        }
    ])
    
    # ===================================
    # カテゴリ2: Azure OpenAI統合（25問）
    # ===================================
    
    # サブカテゴリ2.1: Embedding生成（8問）
    dataset.extend([
        {
            "id": "aoai_emb_001",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "basic",
            "question": "text-embedding-ada-002で1000文字のテキストを埋め込む際のトークン数概算は？",
            "ground_truth": "日本語は平均2-3文字/トークン。1000文字≒350トークン。",
            "context_keywords": ["text-embedding-ada-002", "トークン数"],
            "expected_sources": ["Tokenization"]
        },
        {
            "id": "aoai_emb_002",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "intermediate",
            "question": "埋め込みAPIのレート制限に達した場合のエラーハンドリングを実装してください。",
            "ground_truth": "HTTPステータス429検出時にExponential Backoffでリトライ。@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=60))。",
            "context_keywords": ["429", "rate limit", "Exponential Backoff"],
            "expected_sources": ["Error handling"]
        },
        {
            "id": "aoai_emb_003",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "basic",
            "question": "複数テキストをバッチで埋め込む際の最大入力数は？",
            "ground_truth": "text-embedding-ada-002は最大2048トークン/リクエスト、inputは配列で最大16要素。バッチ化でスループット向上。",
            "context_keywords": ["バッチ", "2048トークン"],
            "expected_sources": ["Embeddings API reference"]
        },
        {
            "id": "aoai_emb_004",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "intermediate",
            "question": "text-embedding-3-largeの次元削減（dimensions指定）のユースケースは？",
            "ground_truth": "3-largeはデフォルト3072次元だが、dimensions=1536に削減可能。メリット：ストレージ50%削減、検索速度向上、精度は2-3%低下。",
            "context_keywords": ["text-embedding-3-large", "次元削減"],
            "expected_sources": ["Embedding models"]
        },
        {
            "id": "aoai_emb_005",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "advanced",
            "question": "埋め込みの正規化（normalization）がスキップされた場合の影響は？",
            "ground_truth": "OpenAI埋め込みは自動正規化済み（L2ノルム=1）。未正規化の場合、コサイン類似度計算でベクトル長の影響受け精度低下。",
            "context_keywords": ["正規化", "L2ノルム", "cosine similarity"],
            "expected_sources": ["Vector mathematics"]
        },
        {
            "id": "aoai_emb_006",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "intermediate",
            "question": "埋め込み生成時のエンコーディングエラー（UnicodeDecodeError）の対処法は？",
            "ground_truth": "UTF-8エンコーディング強制: text.encode('utf-8', errors='ignore').decode('utf-8')。または特殊文字除去。",
            "context_keywords": ["UnicodeDecodeError", "UTF-8"],
            "expected_sources": ["Text preprocessing"]
        },
        {
            "id": "aoai_emb_007",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "basic",
            "question": "埋め込みモデルのバージョン固定方法は？",
            "ground_truth": "デプロイメント名でバージョン管理。例: 'text-embedding-ada-002-v1'（v1固定）。本番はデプロイメント名必須。",
            "context_keywords": ["デプロイメント名", "バージョン"],
            "expected_sources": ["Model versioning"]
        },
        {
            "id": "aoai_emb_008",
            "category": "Azure OpenAI - Embeddings",
            "difficulty": "advanced",
            "question": "埋め込みのドリフト（drift）を検出する監視方法は？",
            "ground_truth": "定期的にリファレンスクエリセット（10-20問）で埋め込み生成し、過去との類似度を比較。cosine_similarity < 0.95でアラート。",
            "context_keywords": ["drift", "ドリフト検出", "監視"],
            "expected_sources": ["ML monitoring"]
        }
    ])
    
    # サブカテゴリ2.2: Chat Completion（8問）
    dataset.extend([
        {
            "id": "aoai_chat_001",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "basic",
            "question": "GPT-4oのコンテキストウィンドウサイズと出力トークン上限は？",
            "ground_truth": "コンテキストウィンドウ: 128Kトークン（入力+出力合計）、max_tokens（出力）: 16K推奨。超過時はTokenTooLongエラー。",
            "context_keywords": ["GPT-4o", "128K", "max_tokens"],
            "expected_sources": ["Model specifications"]
        },
        {
            "id": "aoai_chat_002",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "intermediate",
            "question": "temperature=0.0とtop_p=1.0の組み合わせの意味は？",
            "ground_truth": "temperature=0.0は決定的出力（最高確率トークン選択）、top_p=1.0は全トークン候補考慮。この組み合わせで完全決定的生成。",
            "context_keywords": ["temperature", "top_p", "決定的"],
            "expected_sources": ["Sampling parameters"]
        },
        {
            "id": "aoai_chat_003",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "advanced",
            "question": "ストリーミング応答（stream=True）のエラーハンドリング実装例を示してください。",
            "ground_truth": "try: for chunk in response: yield chunk.choices[0].delta.content; except (APIError, Timeout): logging.error('Stream interrupted'); raise。",
            "context_keywords": ["stream", "ストリーミング", "APIError"],
            "expected_sources": ["Streaming best practices"]
        },
        {
            "id": "aoai_chat_004",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "basic",
            "question": "RAGシステムでsystem promptに含めるべき必須指示は？",
            "ground_truth": "必須要素：(1) 役割定義、(2) コンテキスト優先指示、(3) 不明時の対応、(4) 出力形式（引用・ソース明記）。",
            "context_keywords": ["system prompt", "RAG", "コンテキスト"],
            "expected_sources": ["Prompt engineering for RAG"]
        },
        {
            "id": "aoai_chat_005",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "intermediate",
            "question": "logprobs=Trueで取得できる情報と活用方法は？",
            "ground_truth": "各トークンの対数確率（log probability）と上位5候補を取得。活用：不確実性評価、幻覚検出、デバッグ。",
            "context_keywords": ["logprobs", "対数確率", "幻覚検出"],
            "expected_sources": ["Logprobs documentation"]
        },
        {
            "id": "aoai_chat_006",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "advanced",
            "question": "PTU（Provisioned Throughput Units）とPayGoの切り替えタイミングを定量的に示してください。",
            "ground_truth": "損益分岐点: 日次トークン数 > 2.5M（月75M）でPTU有利。例: PayGo $2,250/月、PTU 100単位 = $1,500/月。",
            "context_keywords": ["PTU", "PayGo", "コスト比較"],
            "expected_sources": ["Pricing optimization"]
        },
        {
            "id": "aoai_chat_007",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "basic",
            "question": "stop引数の使用例と効果を教えてください。",
            "ground_truth": "特定文字列で生成停止。例: stop=['###', 'END']で生成終了マーカー検出時停止。用途: JSON生成で}検出後停止、トークン節約。",
            "context_keywords": ["stop", "生成停止", "マーカー"],
            "expected_sources": ["Completion parameters"]
        },
        {
            "id": "aoai_chat_008",
            "category": "Azure OpenAI - Chat Completion",
            "difficulty": "intermediate",
            "question": "Managed Identityでの認証コード実装例を示してください。",
            "ground_truth": "credential = DefaultAzureCredential(); client = AzureOpenAI(azure_ad_token_provider=lambda: credential.get_token('https://cognitiveservices.azure.com/.default').token)。",
            "context_keywords": ["Managed Identity", "DefaultAzureCredential"],
            "expected_sources": ["Authentication patterns"]
        }
    ])
    
    # サブカテゴリ2.3: Function Calling（9問）
    dataset.extend([
        {
            "id": "aoai_func_001",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "basic",
            "question": "Function Callingの基本フロー（4ステップ）を説明してください。",
            "ground_truth": "ステップ: (1) tools定義とクエリ送信、(2) LLMがtool_calls返却、(3) アプリで実関数実行、(4) 結果をrole='tool'でLLMに返却し最終回答生成。",
            "context_keywords": ["Function Calling", "tool_calls", "role tool"],
            "expected_sources": ["Function calling guide"]
        },
        {
            "id": "aoai_func_002",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "intermediate",
            "question": "tool_choice='required'とtool_choice='auto'の使い分けは？",
            "ground_truth": "'required': 必ず関数呼び出し、'auto': LLMが必要性判断。RAG検索は'required'、チャットボットは'auto'推奨。",
            "context_keywords": ["tool_choice", "required", "auto"],
            "expected_sources": ["Tool choice strategies"]
        },
        {
            "id": "aoai_func_003",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "advanced",
            "question": "複数関数呼び出し（parallel function calling）のエラーハンドリング戦略は？",
            "ground_truth": "各tool_callを独立実行しエラーをtool_result毎に記録。LLMが部分成功で代替案提示。",
            "context_keywords": ["parallel function calling", "エラーハンドリング"],
            "expected_sources": ["Advanced function calling"]
        },
        {
            "id": "aoai_func_004",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "basic",
            "question": "関数定義（tools）のparameters.requiredフィールドの役割は？",
            "ground_truth": "必須引数を指定。例: 'required': ['city']でcityは必須、省略時LLMがユーザーに追加質問。",
            "context_keywords": ["required", "必須引数", "parameters"],
            "expected_sources": ["Function schema"]
        },
        {
            "id": "aoai_func_005",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "intermediate",
            "question": "Function Callingで構造化データ抽出（Structured Output）を実装する方法は？",
            "ground_truth": "extract_info関数定義でparametersにスキーマ指定。LLMがテキストから抽出しJSON返却。Pydanticでvalidation推奨。",
            "context_keywords": ["Structured Output", "データ抽出", "Pydantic"],
            "expected_sources": ["Data extraction patterns"]
        },
        {
            "id": "aoai_func_006",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "advanced",
            "question": "関数呼び出しループの無限ループを防ぐ実装例を示してください。",
            "ground_truth": "最大反復回数制限: max_turns = 5; for turn in range(max_turns): ... ; else: logging.warning('Max turns reached')。",
            "context_keywords": ["無限ループ", "max_turns", "反復制限"],
            "expected_sources": ["Agentic loop patterns"]
        },
        {
            "id": "aoai_func_007",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "intermediate",
            "question": "Function CallingのトークンコストをChat Completionと比較してください。",
            "ground_truth": "Function Calling追加コスト: (1) tools定義（100-500トークン/関数）、(2) tool_calls応答（50-200トークン）。3関数定義で通常の2-3倍。",
            "context_keywords": ["トークンコスト", "オーバーヘッド"],
            "expected_sources": ["Cost optimization"]
        },
        {
            "id": "aoai_func_008",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "basic",
            "question": "tool_call_idの役割と重要性を教えてください。",
            "ground_truth": "各関数呼び出しの一意ID。tool_result返却時に必須。複数関数並行実行時の結果マッピングに使用。",
            "context_keywords": ["tool_call_id", "一意ID", "マッピング"],
            "expected_sources": ["Function calling API"]
        },
        {
            "id": "aoai_func_009",
            "category": "Azure OpenAI - Function Calling",
            "difficulty": "advanced",
            "question": "Guardrails（入力検証・出力フィルタリング）をFunction Callingに統合する実装例を示してください。",
            "ground_truth": "入力検証: def validate_input(args): if 'sql_injection' in str(args): raise ValueError。出力フィルタ: 各関数実行前後にフック追加。",
            "context_keywords": ["Guardrails", "入力検証", "セキュリティ"],
            "expected_sources": ["Security best practices"]
        }
    ])
    
    # ===================================
    # カテゴリ3: Azure AI Foundry（20問）
    # ===================================
    
    dataset.extend([
        {
            "id": "aif_hub_001",
            "category": "Azure AI Foundry - Hub & Project",
            "difficulty": "basic",
            "question": "Azure AI Foundry HubとProjectの関係性を説明してください。",
            "ground_truth": "Hubは組織レベルのリソースコンテナ（共有接続・セキュリティ設定）、Projectはチーム/アプリ単位のワークスペース。1 Hub配下に複数Project作成可能。",
            "context_keywords": ["Hub", "Project", "階層構造"],
            "expected_sources": ["AI Foundry architecture"]
        },
        {
            "id": "aif_hub_002",
            "category": "Azure AI Foundry - Hub & Project",
            "difficulty": "intermediate",
            "question": "AI Foundry HubのManaged Identity設定で必要なRBACロールは？",
            "ground_truth": "必要なロール：(1) Azure OpenAI への Cognitive Services OpenAI User、(2) Azure AI Search への Search Index Data Contributor、(3) Storage への Storage Blob Data Contributor。",
            "context_keywords": ["Managed Identity", "RBAC", "Hub"],
            "expected_sources": ["Security configuration"]
        },
        {
            "id": "aif_hub_003",
            "category": "Azure AI Foundry - Hub & Project",
            "difficulty": "basic",
            "question": "AI Foundry ProjectでAzure OpenAI接続を追加する手順は？",
            "ground_truth": "Project → Settings → Connections → Add connection → Azure OpenAI → エンドポイントとキー入力（またはManaged Identity選択）。",
            "context_keywords": ["Connection", "Azure OpenAI", "Project"],
            "expected_sources": ["Connection management"]
        },
        {
            "id": "aif_hub_004",
            "category": "Azure AI Foundry - Hub & Project",
            "difficulty": "intermediate",
            "question": "複数Projectで同じAzure OpenAIリソースを共有する設定方法は？",
            "ground_truth": "Hub Level Connectionを作成。Hub → Connections → Azure OpenAI追加。配下の全Projectで自動利用可能。",
            "context_keywords": ["Hub Connection", "共有リソース"],
            "expected_sources": ["Resource sharing"]
        },
        {
            "id": "aif_hub_005",
            "category": "Azure AI Foundry - Hub & Project",
            "difficulty": "advanced",
            "question": "AI Foundry HubのネットワークセキュリティでPrivate Endpoint設定時の考慮点は？",
            "ground_truth": "考慮点：(1) VNet統合で全接続リソース（OpenAI、Search）もPrivate化必須、(2) DNS設定（Private DNS Zone）、(3) Playground動作には追加設定必要。",
            "context_keywords": ["Private Endpoint", "VNet", "DNS"],
            "expected_sources": ["Network security"]
        },
        {
            "id": "aif_pf_001",
            "category": "Azure AI Foundry - Prompt Flow",
            "difficulty": "basic",
            "question": "Prompt FlowのDAG（有向非巡回グラフ）構造の利点は何ですか？",
            "ground_truth": "利点：(1) ノード間の依存関係を可視化、(2) 並列実行でパフォーマンス向上、(3) デバッグが容易、(4) 再利用性。循環参照は禁止。",
            "context_keywords": ["DAG", "Prompt Flow", "並列実行"],
            "expected_sources": ["Prompt Flow concepts"]
        },
        {
            "id": "aif_pf_002",
            "category": "Azure AI Foundry - Prompt Flow",
            "difficulty": "intermediate",
            "question": "Prompt Flowで外部APIを呼び出すカスタムPythonノードの実装例を示してください。",
            "ground_truth": "from promptflow import tool; @tool; def call_api(endpoint: str, query: str) -> dict: response = requests.post(endpoint, json={'query': query}); return response.json()。",
            "context_keywords": ["カスタムノード", "Python", "@tool"],
            "expected_sources": ["Custom tools guide"]
        },
        {
            "id": "aif_pf_003",
            "category": "Azure AI Foundry - Prompt Flow",
            "difficulty": "basic",
            "question": "Prompt FlowのLLMノードでtemperatureパラメータを設定する方法は？",
            "ground_truth": "LLMノード設定で Parameters → temperature: 0.7 設定。または YAML定義: parameters: {temperature: 0.7}。",
            "context_keywords": ["LLMノード", "temperature", "パラメータ"],
            "expected_sources": ["LLM node configuration"]
        },
        {
            "id": "aif_pf_004",
            "category": "Azure AI Foundry - Prompt Flow",
            "difficulty": "intermediate",
            "question": "Prompt Flowでループ処理（リスト処理）を実装する方法は？",
            "ground_truth": "Pythonノードでforループ実装。または複数ノードをBatch Runで並列実行。DAGの制約上、ノード内ループが推奨。",
            "context_keywords": ["ループ", "リスト処理", "Batch Run"],
            "expected_sources": ["Advanced flow patterns"]
        },
        {
            "id": "aif_pf_005",
            "category": "Azure AI Foundry - Prompt Flow",
            "difficulty": "advanced",
            "question": "Prompt FlowのVariant機能でA/Bテストを実装する方法は？",
            "ground_truth": "同一ノードに複数Variant（プロンプト変更版）作成。Evaluation RunでVariant毎にメトリクス比較。最良Variantを本番採用。",
            "context_keywords": ["Variant", "A/Bテスト", "プロンプト最適化"],
            "expected_sources": ["Variant management"]
        },
        {
            "id": "aif_eval_001",
            "category": "Azure AI Foundry - Evaluation",
            "difficulty": "basic",
            "question": "Azure AI FoundryのPlaygroundでの評価とPrompt Flowでの評価の違いは？",
            "ground_truth": "Playground: 単発クエリの手動評価、UI上で即時フィードバック。Prompt Flow: バッチ評価、自動メトリクス計算、CI/CD統合可能。",
            "context_keywords": ["Playground", "Prompt Flow", "評価"],
            "expected_sources": ["Evaluation methods"]
        },
        {
            "id": "aif_eval_002",
            "category": "Azure AI Foundry - Evaluation",
            "difficulty": "intermediate",
            "question": "Groundedness評価ノードの実装で必要なinputsは？",
            "ground_truth": "必須inputs: (1) answer（LLM生成回答）、(2) context（検索コンテキスト）。オプション: ground_truth（正解）。outputはgroundedness_score（0-1）。",
            "context_keywords": ["Groundedness", "inputs", "context"],
            "expected_sources": ["Evaluation nodes"]
        },
        {
            "id": "aif_eval_003",
            "category": "Azure AI Foundry - Evaluation",
            "difficulty": "advanced",
            "question": "Groundedness評価をLLM-as-a-Judgeで実装する際の注意点は？",
            "ground_truth": "注意点：(1) 評価用LLMはGPT-4o推奨、(2) システムプロンプトで評価基準明示、(3) 0-5スケール数値化、(4) コスト: 評価クエリ毎に追加トークン消費。",
            "context_keywords": ["LLM-as-a-Judge", "評価基準", "コスト"],
            "expected_sources": ["LLM evaluation"]
        },
        {
            "id": "aif_eval_004",
            "category": "Azure AI Foundry - Evaluation",
            "difficulty": "basic",
            "question": "Evaluation Runの結果をCSVでエクスポートする方法は？",
            "ground_truth": "Evaluation Run完了後 → Results タブ → Export → CSV選択。各行に質問・回答・メトリクススコアが含まれる。",
            "context_keywords": ["Export", "CSV", "Evaluation Run"],
            "expected_sources": ["Results export"]
        },
        {
            "id": "aif_eval_005",
            "category": "Azure AI Foundry - Evaluation",
            "difficulty": "intermediate",
            "question": "複数メトリクス（Groundedness、Relevance、Fluency）を同時評価する設定方法は？",
            "ground_truth": "Evaluation Run設定で複数評価ノード追加。各ノード並列実行、結果を統合表示。または1つの評価ノードで複数メトリクス計算。",
            "context_keywords": ["複数メトリクス", "並列評価"],
            "expected_sources": ["Multi-metric evaluation"]
        },
        {
            "id": "aif_deploy_001",
            "category": "Azure AI Foundry - Deployment",
            "difficulty": "basic",
            "question": "Prompt FlowをREST APIとしてデプロイする手順は？",
            "ground_truth": "Flow完成 → Deploy → Managed Online Endpoint選択 → インスタンス設定（SKU、レプリカ数） → Deploy。エンドポイントURL発行。",
            "context_keywords": ["Deploy", "REST API", "Endpoint"],
            "expected_sources": ["Deployment guide"]
        },
        {
            "id": "aif_deploy_002",
            "category": "Azure AI Foundry - Deployment",
            "difficulty": "intermediate",
            "question": "デプロイ後のエンドポイントのスケーリング設定方法は？",
            "ground_truth": "Endpoint → Settings → Scaling → Manual（固定レプリカ数）またはAuto（CPU/メモリベース自動スケール）選択。Min/Max Replicasを設定。",
            "context_keywords": ["Scaling", "Auto Scale", "Replicas"],
            "expected_sources": ["Scaling configuration"]
        },
        {
            "id": "aif_deploy_003",
            "category": "Azure AI Foundry - Deployment",
            "difficulty": "advanced",
            "question": "Blue-Greenデプロイメントを実装してダウンタイムゼロで更新する方法は？",
            "ground_truth": "新FlowをGreen Endpoint作成 → トラフィック0%でデプロイ → テスト完了後トラフィック徐々に移行（Blue 50% / Green 50%） → 全量Green移行 → Blue削除。",
            "context_keywords": ["Blue-Green", "トラフィック分割", "ゼロダウンタイム"],
            "expected_sources": ["Deployment strategies"]
        },
        {
            "id": "aif_monitor_001",
            "category": "Azure AI Foundry - Monitoring",
            "difficulty": "basic",
            "question": "デプロイ済みエンドポイントのメトリクス監視項目は？",
            "ground_truth": "監視項目：(1) Request Rate（リクエスト数/秒）、(2) Latency P50/P95、(3) Error Rate、(4) Token Consumption。Application Insights統合で詳細分析可能。",
            "context_keywords": ["メトリクス", "Latency", "Error Rate"],
            "expected_sources": ["Monitoring guide"]
        },
        {
            "id": "aif_monitor_002",
            "category": "Azure AI Foundry - Monitoring",
            "difficulty": "intermediate",
            "question": "エンドポイントのログをApplication Insightsで分析する設定方法は？",
            "ground_truth": "Endpoint作成時に Application Insights接続を有効化。ログクエリ例: traces | where operation_Name == 'predict' | summarize avg(duration) by bin(timestamp, 1h)。",
            "context_keywords": ["Application Insights", "ログ分析", "Kusto"],
            "expected_sources": ["Logging integration"]
        }
    ])
    
    # ===================================
    # カテゴリ4: 統合シナリオ（25問）
    # ===================================
    
    dataset.extend([
        {
            "id": "int_e2e_001",
            "category": "Integration - E2E RAG Pipeline",
            "difficulty": "intermediate",
            "question": "RAGパイプラインのE2Eレイテンシが5秒を超える場合の原因分析と対策は？",
            "ground_truth": "原因分析：(1) 検索レイテンシ → k値削減、(2) 埋め込み生成 → キャッシュ、(3) LLM生成 → max_tokens削減、(4) ネットワーク → リージョン統一。",
            "context_keywords": ["レイテンシ", "パフォーマンス最適化"],
            "expected_sources": ["Performance troubleshooting"]
        },
        {
            "id": "int_e2e_002",
            "category": "Integration - E2E RAG Pipeline",
            "difficulty": "basic",
            "question": "RAGシステムで検索結果が0件の場合のフォールバック処理を実装してください。",
            "ground_truth": "if not search_results: return '関連情報が見つかりませんでした。質問を変えて再度お試しください。'; else: # 通常のRAG処理。",
            "context_keywords": ["フォールバック", "検索結果0件"],
            "expected_sources": ["Error handling"]
        },
        {
            "id": "int_e2e_003",
            "category": "Integration - E2E RAG Pipeline",
            "difficulty": "advanced",
            "question": "RAGシステムでコンテキストウィンドウ超過を防ぐ動的チャンク選択アルゴリズムを設計してください。",
            "ground_truth": "アルゴリズム：(1) 検索上位k件取得、(2) 各チャンクをトークン化、(3) 累積トークン数がmax_tokens未満まで追加、(4) 超過時は最低関連度チャンク削除。",
            "context_keywords": ["コンテキストウィンドウ", "動的選択", "トークン"],
            "expected_sources": ["Context management"]
        },
        {
            "id": "int_e2e_004",
            "category": "Integration - E2E RAG Pipeline",
            "difficulty": "intermediate",
            "question": "RAG回答にソース引用を自動追加する実装方法は？",
            "ground_truth": "回答生成後: sources = [doc['source'] for doc in context]; answer += '\\n\\n【参照元】\\n' + '\\n'.join(f'- {s}' for s in set(sources))。",
            "context_keywords": ["ソース引用", "出典明示"],
            "expected_sources": ["Citation formatting"]
        },
        {
            "id": "int_e2e_005",
            "category": "Integration - E2E RAG Pipeline",
            "difficulty": "basic",
            "question": "RAGシステムでユーザークエリの前処理（クリーニング）を実装してください。",
            "ground_truth": "def clean_query(q): q = q.strip(); q = re.sub(r'\\s+', ' ', q); q = q[:500]; return q。空白正規化、長さ制限適用。",
            "context_keywords": ["前処理", "クリーニング", "正規化"],
            "expected_sources": ["Query preprocessing"]
        },
        {
            "id": "int_err_001",
            "category": "Integration - Error Handling",
            "difficulty": "intermediate",
            "question": "Azure OpenAI APIの429エラー（レート制限）を検出してフォールバック処理を実装してください。",
            "ground_truth": "try: response = client.create(...); except RateLimitError: logging.warning('Rate limit'); time.sleep(exponential_backoff); または cached_response返却。",
            "context_keywords": ["429", "RateLimitError", "フォールバック"],
            "expected_sources": ["Error handling patterns"]
        },
        {
            "id": "int_err_002",
            "category": "Integration - Error Handling",
            "difficulty": "basic",
            "question": "Azure AI Search接続エラー時のリトライロジックを実装してください。",
            "ground_truth": "@retry(stop=stop_after_attempt(3), wait=wait_fixed(2)); def search_with_retry(): return search_client.search(...)。3回まで2秒間隔でリトライ。",
            "context_keywords": ["リトライ", "接続エラー", "@retry"],
            "expected_sources": ["Retry patterns"]
        },
        {
            "id": "int_err_003",
            "category": "Integration - Error Handling",
            "difficulty": "advanced",
            "question": "複数Azureサービスの障害時に部分機能提供（Graceful Degradation）を実装する戦略は？",
            "ground_truth": "戦略：(1) Search障害時はキャッシュ検索、(2) OpenAI障害時はテンプレート回答、(3) 全障害時は静的FAQ返却。サービス優先度定義し段階的フォールバック。",
            "context_keywords": ["Graceful Degradation", "部分機能提供", "障害対応"],
            "expected_sources": ["Resilience patterns"]
        },
        {
            "id": "int_err_004",
            "category": "Integration - Error Handling",
            "difficulty": "intermediate",
            "question": "RAGシステムでLLM幻覚（Hallucination）を検出する実装方法は？",
            "ground_truth": "検出方法：(1) logprobsで低確率トークン検出、(2) コンテキストに存在しない固有名詞検出、(3) Groundedness評価ノードでスコア < 0.7を幻覚判定。",
            "context_keywords": ["幻覚", "Hallucination", "検出"],
            "expected_sources": ["Hallucination detection"]
        },
        {
            "id": "int_err_005",
            "category": "Integration - Error Handling",
            "difficulty": "basic",
            "question": "ユーザー入力のインジェクション攻撃を防ぐバリデーションを実装してください。",
            "ground_truth": "def validate_input(query): if len(query) > 1000: raise ValueError('長すぎ'); if re.search(r'<script|DROP TABLE', query, re.I): raise ValueError('不正入力')。",
            "context_keywords": ["インジェクション", "バリデーション", "セキュリティ"],
            "expected_sources": ["Input validation"]
        },
        {
            "id": "int_perf_001",
            "category": "Integration - Performance Optimization",
            "difficulty": "advanced",
            "question": "RAGシステムのスループットを2倍にする最適化戦略を3つ提案してください。",
            "ground_truth": "(1) 埋め込みキャッシュ（Redis）でヒット率70%達成、(2) 検索結果先読みキャッシュ、(3) Azure OpenAI PTUで固定スループット+負荷分散。",
            "context_keywords": ["スループット", "最適化", "キャッシュ"],
            "expected_sources": ["Scalability patterns"]
        },
        {
            "id": "int_perf_002",
            "category": "Integration - Performance Optimization",
            "difficulty": "intermediate",
            "question": "RAGシステムで並列リクエスト処理（asyncio）を実装する方法は？",
            "ground_truth": "async def rag_pipeline(q): embed = await async_get_embedding(q); results = await async_search(embed); response = await async_llm(results); return response。",
            "context_keywords": ["asyncio", "並列処理", "async/await"],
            "expected_sources": ["Async programming"]
        },
        {
            "id": "int_perf_003",
            "category": "Integration - Performance Optimization",
            "difficulty": "basic",
            "question": "検索結果のキャッシュをRedisで実装する基本コードを示してください。",
            "ground_truth": "import redis; r = redis.Redis(); cache_key = hashlib.md5(query.encode()).hexdigest(); cached = r.get(cache_key); if cached: return json.loads(cached); # 検索実行; r.setex(cache_key, 1800, json.dumps(results))。",
            "context_keywords": ["Redis", "キャッシュ", "MD5"],
            "expected_sources": ["Caching implementation"]
        },
        {
            "id": "int_perf_004",
            "category": "Integration - Performance Optimization",
            "difficulty": "intermediate",
            "question": "Azure AI Searchのインデックスパーティション数増加でパフォーマンス向上する条件は？",
            "ground_truth": "条件：(1) データ量10GB超、(2) 高クエリ負荷（1000 QPS超）、(3) 複雑クエリ（複数フィルタ・ファセット）。パーティション追加でストレージとクエリ並列化。",
            "context_keywords": ["パーティション", "スケーリング", "QPS"],
            "expected_sources": ["Partitioning strategy"]
        },
        {
            "id": "int_perf_005",
            "category": "Integration - Performance Optimization",
            "difficulty": "advanced",
            "question": "RAGシステムのP95レイテンシを3秒から1秒に削減する実装ロードマップを示してください。",
            "ground_truth": "ロードマップ：Week1: 埋め込みキャッシュ導入(-1s)、Week2: ストリーミング応答実装(-0.5s)、Week3: 検索並列化+k値最適化(-0.5s)。各週で計測・検証。",
            "context_keywords": ["P95レイテンシ", "削減ロードマップ"],
            "expected_sources": ["Performance roadmap"]
        },
        {
            "id": "int_cost_001",
            "category": "Integration - Cost Optimization",
            "difficulty": "intermediate",
            "question": "RAGシステムの月次コストを30%削減する戦略を3つ提案してください。",
            "ground_truth": "(1) 埋め込みキャッシュでOpenAI APIコール70%削減、(2) 検索k値削減（10→5）で処理時間短縮、(3) GPT-4o → GPT-4o-miniで単価50%削減（精度許容範囲）。",
            "context_keywords": ["コスト削減", "最適化戦略"],
            "expected_sources": ["Cost optimization"]
        },
        {
            "id": "int_cost_002",
            "category": "Integration - Cost Optimization",
            "difficulty": "basic",
            "question": "Azure OpenAIのトークン使用量を監視するコードを実装してください。",
            "ground_truth": "response = client.create(...); usage = response.usage; logging.info(f'Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})')。",
            "context_keywords": ["トークン監視", "usage", "logging"],
            "expected_sources": ["Usage monitoring"]
        },
        {
            "id": "int_cost_003",
            "category": "Integration - Cost Optimization",
            "difficulty": "advanced",
            "question": "RAGシステムのコスト配分（Cost Breakdown）を計算し、最適化優先度を決定する方法は？",
            "ground_truth": "配分計算：(1) OpenAI API: 60%、(2) AI Search: 30%、(3) Storage: 10%。最適化優先度: OpenAI（埋め込みキャッシュ、モデル変更）が最大効果。",
            "context_keywords": ["Cost Breakdown", "優先度決定"],
            "expected_sources": ["Cost analysis"]
        },
        {
            "id": "int_cost_004",
            "category": "Integration - Cost Optimization",
            "difficulty": "intermediate",
            "question": "Azure AI SearchのBasic SKUとStandard SKUの切り替えタイミングを定量的に示してください。",
            "ground_truth": "切り替えタイミング：(1) ドキュメント数10万件超、(2) クエリ負荷100 QPS超、(3) セマンティックランキング必要時。Basic: ~¥8,000/月、Standard: ~¥25,000/月。",
            "context_keywords": ["SKU切り替え", "Basic", "Standard"],
            "expected_sources": ["SKU selection"]
        },
        {
            "id": "int_cost_005",
            "category": "Integration - Cost Optimization",
            "difficulty": "basic",
            "question": "未使用のAzureリソースを定期的に検出してコスト削減する方法は？",
            "ground_truth": "Azure Cost Management + Budgets → Advisor recommendations確認。未使用リソース例：削除忘れインデックス、停止していないVM、古いストレージ。",
            "context_keywords": ["未使用リソース", "Cost Management"],
            "expected_sources": ["Resource cleanup"]
        },
        {
            "id": "int_sec_001",
            "category": "Integration - Security",
            "difficulty": "intermediate",
            "question": "RAGシステムでPII（個人情報）を検出してマスキングする実装方法は？",
            "ground_truth": "import re; def mask_pii(text): text = re.sub(r'\\b\\d{3}-\\d{4}-\\d{4}\\b', '***-****-****', text); # 電話番号; text = re.sub(r'\\b[\\w.-]+@[\\w.-]+\\.\\w+\\b', '***@***.***', text); # Email; return text。",
            "context_keywords": ["PII", "マスキング", "個人情報"],
            "expected_sources": ["Data privacy"]
        },
        {
            "id": "int_sec_002",
            "category": "Integration - Security",
            "difficulty": "basic",
            "question": "Azure Key VaultにOpenAI APIキーを保存して取得するコードを実装してください。",
            "ground_truth": "from azure.keyvault.secrets import SecretClient; from azure.identity import DefaultAzureCredential; client = SecretClient(vault_url=VAULT_URL, credential=DefaultAzureCredential()); api_key = client.get_secret('openai-api-key').value。",
            "context_keywords": ["Key Vault", "APIキー", "シークレット管理"],
            "expected_sources": ["Secret management"]
        },
        {
            "id": "int_sec_003",
            "category": "Integration - Security",
            "difficulty": "advanced",
            "question": "RAGシステムでRow-Level Security（RLS）を実装してマルチテナント対応する方法は？",
            "ground_truth": "実装：(1) インデックスに tenantId フィールド追加、(2) 検索時にfilter='tenantId eq \\'tenant123\\''強制適用、(3) JWT検証でtenantId抽出、(4) アプリ層で強制フィルタ。",
            "context_keywords": ["Row-Level Security", "RLS", "マルチテナント"],
            "expected_sources": ["Multi-tenant security"]
        },
        {
            "id": "int_sec_004",
            "category": "Integration - Security",
            "difficulty": "intermediate",
            "question": "Azure AI SearchのManaged Identity認証をBicepで設定するコードを示してください。",
            "ground_truth": "resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {name: guid(searchService.id, principalId, 'SearchIndexDataContributor'); properties: {principalId: principalId; roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'}}。",
            "context_keywords": ["Managed Identity", "Bicep", "RBAC"],
            "expected_sources": ["IAC security"]
        },
        {
            "id": "int_sec_005",
            "category": "Integration - Security",
            "difficulty": "basic",
            "question": "RAGシステムへのDDoS攻撃を防ぐレート制限を実装してください。",
            "ground_truth": "from flask_limiter import Limiter; limiter = Limiter(app, key_func=lambda: request.remote_addr); @app.route('/query'); @limiter.limit('10 per minute'); def query(): ...。",
            "context_keywords": ["レート制限", "DDoS", "Flask"],
            "expected_sources": ["API security"]
        }
    ])
    
    return dataset


def save_dataset(dataset: List[Dict], output_path: str = "evaluation_dataset.jsonl"):
    """データセットをJSONL形式で保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"✅ Dataset saved: {output_path} ({len(dataset)} questions)")


if __name__ == "__main__":
    dataset = create_evaluation_dataset()
    save_dataset(dataset)
    
    # 統計情報表示
    categories = {}
    difficulties = {}
    for item in dataset:
        cat = item['category']
        diff = item['difficulty']
        categories[cat] = categories.get(cat, 0) + 1
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print("\n📊 Dataset Statistics:")
    print("\n【カテゴリ別】")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}問")
    
    print("\n【難易度別】")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff}: {count}問")
    
    print(f"\n【合計】{len(dataset)}問")