"""
データ拡充パイプライン

Usage:
    python scripts/data_augmentation_pipeline.py --target 100
"""

import json
import argparse
from typing import List, Dict
from datetime import datetime
from generate_qa_data import QADataGenerator
from validate_qa_quality import QAValidator


class DataAugmentationPipeline:
    """データ拡充パイプライン"""
    
    def __init__(self):
        self.generator = QADataGenerator()
        self.validator = QAValidator()
        
        self.target_distribution = {
            "Azure AI Search": 25,
            "Security & Identity": 25,
            "Infrastructure": 20,
            "Python SDK": 15,
            "Architecture Patterns": 15
        }
    
    def load_existing_data(self, filepath: str) -> List[Dict]:
        """既存データ読み込み"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  File not found: {filepath}")
            return []
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return []
    
    def analyze_existing_data(self, existing_data: List[Dict]) -> Dict[str, int]:
        """既存データのカテゴリ分析"""
        category_counts = {cat: 0 for cat in self.target_distribution.keys()}
        
        for qa in existing_data:
            cat = qa.get("category", "Unknown")
            if cat in category_counts:
                category_counts[cat] += 1
        
        return category_counts
    
    def calculate_needed_counts(self, existing_counts: Dict[str, int]) -> Dict[str, int]:
        """カテゴリ別不足数計算"""
        needed = {}
        
        for cat, target in self.target_distribution.items():
            current = existing_counts.get(cat, 0)
            needed[cat] = max(0, target - current)
        
        return needed
    
    def remove_duplicates(
        self,
        new_qa_list: List[Dict],
        existing_qa_list: List[Dict],
        threshold: float = 0.8
    ) -> List[Dict]:
        """重複除去（簡易版：質問文の完全一致のみ）"""
        existing_questions = {qa["question"] for qa in existing_qa_list}
        
        unique_qa_list = []
        duplicates = 0
        
        for qa in new_qa_list:
            if qa["question"] not in existing_questions:
                unique_qa_list.append(qa)
                existing_questions.add(qa["question"])
            else:
                duplicates += 1
        
        if duplicates > 0:
            print(f"  🔄 Removed {duplicates} duplicates")
        
        return unique_qa_list
    
    def generate_and_validate_batch(
        self,
        category: str,
        count: int,
        existing_data: List[Dict]
    ) -> List[Dict]:
        """カテゴリ別バッチ生成＆バリデーション"""
        
        print(f"\n🔨 Generating {count} Q&As for: {category}")
        
        valid_qa_list = []
        attempts = 0
        max_attempts = count * 2
        
        while len(valid_qa_list) < count and attempts < max_attempts:
            remaining = count - len(valid_qa_list)
            batch_size = min(5, remaining)
            
            print(f"  Attempt {attempts + 1}: Generating {batch_size} Q&As...")
            
            batch = self.generator.generate_qa(category, batch_size)
            
            if not batch:
                print(f"  ⚠️  Generation failed")
                attempts += 1
                continue
            
            validation_results = self.validator.validate_all(batch)
            
            for i, qa in enumerate(batch):
                is_failed = any(
                    err["index"] == i 
                    for err in validation_results["errors"]
                )
                
                if not is_failed:
                    valid_qa_list.append(qa)
            
            print(f"  ✅ Validated: {validation_results['passed']}/{validation_results['total']} passed")
            
            attempts += 1
        
        valid_qa_list = self.remove_duplicates(valid_qa_list, existing_data)
        
        print(f"  🎉 Final count: {len(valid_qa_list)}/{count}")
        
        return valid_qa_list[:count]
    
    def run(self, existing_file: str, output_file: str, target_total: int = 100):
        """パイプライン実行"""
        
        print("=" * 60)
        print("🚀 Data Augmentation Pipeline")
        print("=" * 60)
        
        print("\n📊 Step 1: Analyzing existing data...")
        existing_data = self.load_existing_data(existing_file)
        print(f"  Existing Q&As: {len(existing_data)}")
        
        existing_counts = self.analyze_existing_data(existing_data)
        print("\n  Category breakdown:")
        for cat, count in existing_counts.items():
            print(f"    - {cat}: {count}")
        
        print("\n📈 Step 2: Calculating needed counts...")
        needed_counts = self.calculate_needed_counts(existing_counts)
        total_needed = sum(needed_counts.values())
        print(f"  Total needed: {total_needed}")
        print("\n  Needed by category:")
        for cat, count in needed_counts.items():
            if count > 0:
                print(f"    - {cat}: +{count}")
        
        print("\n🔨 Step 3: Generating new Q&As...")
        all_new_qa = []
        
        for category, count in needed_counts.items():
            if count > 0:
                new_qa_list = self.generate_and_validate_batch(
                    category,
                    count,
                    existing_data + all_new_qa
                )
                all_new_qa.extend(new_qa_list)
        
        print("\n🔗 Step 4: Merging datasets...")
        combined_data = existing_data + all_new_qa
        
        for i, qa in enumerate(combined_data):
            qa["id"] = f"qa_{i+1:03d}"
        
        print(f"  Total Q&As: {len(combined_data)}")
        
        print(f"\n💾 Step 5: Saving to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ Pipeline Complete!")
        print("=" * 60)
        
        final_counts = self.analyze_existing_data(combined_data)
        print("\n📊 Final distribution:")
        for cat, count in final_counts.items():
            target = self.target_distribution[cat]
            status = "✅" if count >= target else "⚠️"
            print(f"  {status} {cat}: {count}/{target}")
        
        print(f"\n💾 Output: {output_file}")
        print(f"📁 Total Q&As: {len(combined_data)}")
        
        stats = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "existing_count": len(existing_data),
            "new_count": len(all_new_qa),
            "total_count": len(combined_data),
            "category_distribution": final_counts,
            "target_distribution": self.target_distribution
        }
        
        import os
        os.makedirs("reports", exist_ok=True)
        stats_file = "reports/augmentation_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"📊 Stats: {stats_file}")


def main():
    parser = argparse.ArgumentParser(description="Data Augmentation Pipeline")
    parser.add_argument(
        "--existing",
        default="data/test_qa_generated.json",
        help="Existing Q&A data file"
    )
    parser.add_argument(
        "--output",
        default="data/test_qa_v2.json",
        help="Output file path"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=100,
        help="Target total Q&A count"
    )
    
    args = parser.parse_args()
    
    pipeline = DataAugmentationPipeline()
    pipeline.run(args.existing, args.output, args.target)


if __name__ == "__main__":
    main()