"""
Q&Aデータ生成スクリプト

Requirements:
- openai>=1.12.0
- azure-identity>=1.19.0
"""

import os
import json
from typing import List, Dict
from datetime import datetime
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential


class QADataGenerator:
    """高品質Q&Aデータ生成器"""
    
    def __init__(self):
        """初期化"""
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=self._get_token,
            api_version="2024-10-01-preview"
        )
        
        # Few-shot examples（カテゴリ別）
        self.examples = self._load_examples()
    
    def _get_token(self) -> str:
        """Azure AD トークン取得"""
        credential = DefaultAzureCredential()
        token = credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        return token.token
    
    def _load_examples(self) -> Dict[str, List[Dict]]:
        """Few-shot examples読み込み"""
        return {
            "Azure AI Search": [
                {
                    "question": "Azure AI SearchでHNSWのm=4とm=16では、どちらが検索速度が速いですか？",
                    "ground_truth": "m=4の方が検索速度が速いです。パラメータmはグラフの接続数を表し、値が小さいほど探索時の計算量が減少します。ただし、m=16の方が検索精度は向上します。",
                    "context": [
                        "Azure AI Search公式: HNSW Configuration",
                        "推奨パラメータ範囲: m=4-16"
                    ]
                }
            ],
            "Security & Identity": [
                {
                    "question": "Managed IdentityのSystem-assignedとUser-assignedの主な違いは何ですか？",
                    "ground_truth": "System-assignedはリソースのライフサイクルに紐付き、リソース削除時に自動削除されます。User-assignedは独立したIDとして複数リソースで共有可能です。",
                    "context": [
                        "Managed Identity Types",
                        "System-assigned: 1リソース1ID",
                        "User-assigned: 1ID複数リソース共有可能"
                    ]
                }
            ]
        }
    
    def generate_qa(
        self,
        category: str,
        num_samples: int,
        difficulty: str = "intermediate"
    ) -> List[Dict]:
        """カテゴリ別Q&A生成"""
        
        # Few-shot examples取得
        examples = self.examples.get(category, [])
        examples_text = "\n\n".join([
            f"質問: {ex['question']}\n"
            f"回答: {ex['ground_truth']}\n"
            f"コンテキスト: {', '.join(ex['context'])}"
            for ex in examples
        ])
        
        system_prompt = f"""あなたはAzure技術の専門家です。
以下の条件で技術Q&Aデータを生成してください：

【カテゴリ】: {category}
【難易度】: {difficulty}
【生成件数】: {num_samples}件

【品質基準】:
1. 質問は具体的シナリオベース
2. Ground Truthは検証可能な事実のみ
3. コンテキストは具体的
4. 質問長: 50-200文字、Ground Truth長: 100-500文字

【参考例】:
{examples_text}

【出力形式】: JSON配列
{{
  "qa_list": [
    {{
      "question": "...",
      "ground_truth": "...",
      "context": ["...", "..."],
      "tags": ["tag1", "tag2"]
    }}
  ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{category}に関するQ&Aを{num_samples}件生成してください"}
                ],
                temperature=0.8,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # JSONが配列でない場合の対応
            if isinstance(result, dict) and "qa_list" in result:
                qa_list = result["qa_list"]
            elif isinstance(result, dict) and "questions" in result:
                qa_list = result["questions"]
            elif isinstance(result, list):
                qa_list = result
            else:
                qa_list = []
            
            # メタデータ追加
            for i, qa in enumerate(qa_list):
                qa["id"] = f"qa_{category.replace(' ', '_').lower()}_{i+1:03d}"
                qa["category"] = category
                qa["difficulty"] = difficulty
                qa["verified"] = False
                qa["created_at"] = datetime.utcnow().isoformat() + "Z"
            
            return qa_list
            
        except Exception as e:
            print(f"❌ Error generating Q&A for {category}: {e}")
            return []


if __name__ == "__main__":
    # テスト実行
    print("🚀 Q&A生成テスト開始...")
    generator = QADataGenerator()
    
    # Azure AI Search カテゴリで3件生成
    print("\n📊 Azure AI Search カテゴリで3件生成中...")
    qa_data = generator.generate_qa("Azure AI Search", 3)
    
    print(f"\n✅ Generated {len(qa_data)} Q&As\n")
    print("=" * 60)
    print(json.dumps(qa_data, ensure_ascii=False, indent=2))
    print("=" * 60)
    
    # ファイル保存
    output_path = "data/test_qa_generated.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {output_path}")
