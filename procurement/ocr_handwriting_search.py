#!/usr/bin/env python3
"""
GitHub Search for Handwriting OCR, Receipt/Form Recognition
"""
import json
import urllib.request
import urllib.parse
import time

def search_github(query, per_page=10):
    """Search GitHub API"""
    params = urllib.parse.urlencode({
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': per_page
    })
    url = f"https://api.github.com/search/repositories?{params}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {'items': [], 'error': str(e)}

def get_repo_info(full_name):
    """Get detailed repo info"""
    url = f"https://api.github.com/repos/{full_name}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {'error': str(e)}

# Search queries for handwriting OCR, receipt/form recognition
searches = [
    "handwriting OCR deep learning",
    "receipt OCR text recognition",
    "form table recognition",
    "handwritten printed overlapped text separation",
    "handwriting printed separation OCR",
    "handwritten digits recognition",
    "table structure recognition",
    "invoice receipt parsing",
]

print("=" * 70)
print("GITHUB搜索: 手写OCR、票据识别、表格识别开源项目")
print("=" * 70)

all_results = {}

for query in searches:
    print(f"\n搜索: '{query}'")
    result = search_github(query)
    if 'items' in result:
        print(f"  找到 {len(result['items'])} 个结果")
        for item in result['items'][:8]:
            name = item['full_name']
            stars = item['stargazers_count']
            desc = item.get('description', 'N/A')
            url = item.get('html_url', '')
            lang = item.get('language', 'N/A')
            topics = item.get('topics', [])
            
            if name not in all_results:
                all_results[name] = {
                    'stars': stars, 
                    'description': desc, 
                    'url': url, 
                    'language': lang,
                    'topics': topics
                }
    else:
        print(f"  错误: {result.get('error', '未知')}")
    time.sleep(1)  # Be nice to API

# Sort by stars
sorted_results = sorted(all_results.items(), key=lambda x: x[1]['stars'], reverse=True)

print("\n" + "=" * 70)
print("搜索结果汇总 (按Stars排序)")
print("=" * 70)

for i, (name, info) in enumerate(sorted_results[:20], 1):
    print(f"\n{i}. {name}")
    print(f"   ⭐ Stars: {info['stars']:,}")
    print(f"   📝 {info['description']}")
    print(f"   🔗 {info['url']}")
    print(f"   💻 语言: {info['language']}")
    if info['topics']:
        print(f"   🏷️  Topics: {', '.join(info['topics'][:5])}")

# Save results
with open('/home/ubuntu/ocr_search_results.json', 'w', encoding='utf-8') as f:
    json.dump(sorted_results[:20], f, ensure_ascii=False, indent=2)
print("\n\n结果已保存到 /home/ubuntu/ocr_search_results.json")
