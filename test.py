import re

def extract_urls_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Regex tìm các đường dẫn bắt đầu bằng http hoặc https
    urls = re.findall(r'https?://[^\s)]+', content)
    return urls

import re

def extract_urls_from_text(text):
    # Regex tìm các đường dẫn bắt đầu bằng http hoặc https
    urls = re.findall(r'https?://[^\s)]+', text)
    return urls

# Ví dụ sử dụng:
text = """
Mission Text:
https://discord.com/invite/EXAMPLE1   (Example 1)
join --> nhấn "verify"  --> you have been verified là ok
https://discord.gg/EXAMPLE2   (Example 2)
join --> chọn bất kì --> finish
div
"""

urls = extract_urls_from_text(text)
print(urls)