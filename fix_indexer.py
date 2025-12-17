import os
import re

with open('src/indexer.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.strip() == 'from azure.search.documents import SearchClient':
        new_lines.append('import os\n')
        new_lines.append('from azure.core.credentials import AzureKeyCredential\n')
    if 'credential = get_azure_credential()' in line and 'self.index_client' not in line:
        new_lines.append('        api_key = os.getenv("AZURE_SEARCH_API_KEY")\n')
        new_lines.append('        if api_key:\n')
        new_lines.append('            credential = AzureKeyCredential(api_key)\n')
        new_lines.append('        else:\n')
        new_lines.append('            credential = get_azure_credential()\n')
        continue
    new_lines.append(line)

with open('src/indexer.py', 'w') as f:
    f.writelines(new_lines)

print("indexer.py updated!")