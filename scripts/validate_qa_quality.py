"""
Q&Aデータ品質バリデータ

Usage:
    python scripts/validate_qa_quality.py data/test_qa_generated.json
"""

import json
import sys
from typing import List, Dict, Tuple
from datetime import datetime
import os


class QAValidator:
    """Q&Aデータ品質検証"""
    
    def __init__(self):
        self.required_fields = [
            "id", "category", "question", "ground_truth", 
            "context", "difficulty", "verified", "created_at"
        ]
        
        self.valid_categories = [
            "Azure AI Search",
            "Security & Identity",
            "Infrastructure",
            "Python SDK",
            "Architecture Patterns"
        ]
        
        self.valid_difficulties = ["beginner", "intermediate", "advanced"]
    
    def validate_structure(self, qa: Dict) -> Tuple[bool, List[str]]:
        """構造チェック"""
        errors = []
        
        for field in self.required_fields:
            if field not in qa:
                errors.append(f"Missing field: {field}")
        
        if qa.get("category") not in self.valid_categories:
            errors.append(f"Invalid category: {qa.get('category')}")
        
        if qa.get("difficulty") not in self.valid_difficulties:
            errors.append(f"Invalid difficulty: {qa.get('difficulty')}")
        
        return len(errors) == 0, errors
    
    def validate_length(self, qa: Dict) -> Tuple[bool, List[str]]:
        """長さチェック"""
        errors = []
        
        q_len = len(qa.get("question", ""))
        if not (20 <= q_len <= 200):
            errors.append(f"Question length {q_len} not in range [20, 200]")
        
        gt_len = len(qa.get("ground_truth", ""))
        if not (50 <= gt_len <= 500):
            errors.append(f"Ground truth length {gt_len} not in range [50, 500]")
        
        ctx_count = len(qa.get("context", []))
        if ctx_count < 1:
            errors.append("Context must have at least 1 item")
        
        return len(errors) == 0, errors
    
    def validate_content(self, qa: Dict) -> Tuple[bool, List[str]]:
        """内容チェック"""
        errors = []
        
        question = qa.get("question", "")
        ground_truth = qa.get("ground_truth", "")
        
        forbidden_question_phrases = [
            "どうやって", "方法を教えて", "とは何ですか",
            "について教えて", "使い方"
        ]
        
        for phrase in forbidden_question_phrases:
            if phrase in question:
                errors.append(f"Question contains forbidden phrase: '{phrase}'")
        
        subjective_phrases = [
            "一般的に", "通常", "場合によります", "と言われています"
        ]
        
        for phrase in subjective_phrases:
            if phrase in ground_truth:
                errors.append(f"Ground truth contains subjective phrase: '{phrase}'")
        
        return len(errors) == 0, errors
    
    def validate_all(self, qa_list: List[Dict]) -> Dict:
        """全データ検証"""
        results = {
            "total": len(qa_list),
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, qa in enumerate(qa_list):
            qa_errors = []
            
            struct_ok, struct_errors = self.validate_structure(qa)
            if not struct_ok:
                qa_errors.extend(struct_errors)
            
            length_ok, length_errors = self.validate_length(qa)
            if not length_ok:
                qa_errors.extend(length_errors)
            
            content_ok, content_errors = self.validate_content(qa)
            if not content_ok:
                qa_errors.extend(content_errors)
            
            if qa_errors:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "id": qa.get("id", "unknown"),
                    "errors": qa_errors
                })
            else:
                results["passed"] += 1
        
        results["pass_rate"] = results["passed"] / results["total"] if results["total"] > 0 else 0
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_qa_quality.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    print(f"🔍 Validating: {json_file}")
    print("=" * 60)
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            qa_list = json.load(f)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        sys.exit(1)
    
    validator = QAValidator()
    results = validator.validate_all(qa_list)
    
    print(f"\n📊 Validation Results")
    print("=" * 60)
    print(f"Total Q&As:    {results['total']}")
    print(f"✅ Passed:      {results['passed']}")
    print(f"❌ Failed:      {results['failed']}")
    print(f"📈 Pass Rate:   {results['pass_rate']:.1%}")
    print("=" * 60)
    
    if results["errors"]:
        print(f"\n⚠️  Failed Q&As:")
        for error in results["errors"]:
            print(f"\n  [{error['index']}] {error['id']}")
            for err in error["errors"]:
                print(f"    - {err}")
    else:
        print("\n🎉 All Q&As passed validation!")
    
    report_file = "reports/validation_report.txt"
    os.makedirs("reports", exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Validation Report - {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n")
        f.write(f"File: {json_file}\n")
        f.write(f"Total: {results['total']}\n")
        f.write(f"Passed: {results['passed']}\n")
        f.write(f"Failed: {results['failed']}\n")
        f.write(f"Pass Rate: {results['pass_rate']:.1%}\n")
        
        if results["errors"]:
            f.write("\nErrors:\n")
            for error in results["errors"]:
                f.write(f"\n[{error['index']}] {error['id']}\n")
                for err in error["errors"]:
                    f.write(f"  - {err}\n")
    
    print(f"\n💾 Report saved to: {report_file}")
    
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()