import os

project_docs = [
    "/mnt/project/01_azure_ai_search.md",
    "/mnt/project/02_bicep_iac.md",
    "/mnt/project/03_yaml_pipeline.md",
    "/mnt/project/04_python_sdk.md",
    "/mnt/project/05_security.md",
]

print("=== プロジェクトドキュメント確認 ===\n")
total_chars = 0

for doc_path in project_docs:
    if os.path.exists(doc_path):
        with open(doc_path, 'r') as f:
            content = f.read()
            chars = len(content)
            total_chars += chars
            print(f"{os.path.basename(doc_path)}: {chars:,} chars")
    else:
        print(f"{doc_path}: ❌ 見つかりません")

print(f"\n合計: {total_chars:,} chars")
print(f"平均: {total_chars // len(project_docs):,} chars/doc")
