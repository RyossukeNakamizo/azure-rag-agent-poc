# RAG Evaluation Flow

## 概要
Azure AI Foundry Prompt Flowを使用したRAG評価パイプライン

## 構成
- **flow.dag.yaml**: Prompt Flow定義
- **nodes/**: 評価ノード実装
  - retrieve.py: コンテキスト検索
  - generate_prompt.jinja2: LLMプロンプト
  - evaluate_groundedness.py: Groundedness評価
  - evaluate_relevance.py: Relevance評価
  - evaluate_coherence.py: Coherence評価

## 使用方法

### 1. 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集
```

### 2. 依存パッケージインストール
```bash
pip install -r requirements.txt
```

### 3. ローカルテスト
```bash
pf flow test --flow . --inputs question="Azure AI Searchのベクトル検索設定方法は？"
```

### 4. バッチ評価
```bash
pf run create --flow . --data ../evaluation_dataset.jsonl --stream
```

## 評価指標
- **Groundedness**: 回答がコンテキストに基づいているか（0.0-1.0）
- **Relevance**: 回答が質問に適切か（0.0-1.0）
- **Coherence**: 回答の論理的一貫性（0.0-1.0）

## 目標値
- Groundedness > 0.85
- Relevance > 0.80
- Coherence > 0.75
