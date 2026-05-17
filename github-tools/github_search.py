#!/usr/bin/env python3
"""
GitHub Search for Business Website Templates with Admin Panel
"""
import json
import urllib.request
import urllib.parse

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
        with urllib.request.urlopen(req, timeout=10) as response:
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

# Search queries relevant to business website with admin panel
searches = [
    "admin dashboard template Bootstrap",
    "admin panel HTML template",
    "business website template free",
    "company website admin template",
    "dashboard admin template with frontend"
]

print("=" * 60)
print("GITHUB SEARCH: Business Website Templates with Admin Panel")
print("=" * 60)

all_results = {}

for query in searches:
    print(f"\nSearching: '{query}'")
    result = search_github(query)
    if 'items' in result:
        print(f"  Found {len(result['items'])} results")
        for item in result['items'][:5]:
            name = item['full_name']
            stars = item['stargazers_count']
            desc = item.get('description', 'N/A')
            url = item.get('html_url', '')
            lang = item.get('language', 'N/A')
            
            if name not in all_results:
                all_results[name] = {'stars': stars, 'description': desc, 'url': url, 'language': lang}
    else:
        print(f"  Error: {result.get('error', 'Unknown')}")

# Sort by stars
sorted_results = sorted(all_results.items(), key=lambda x: x[1]['stars'], reverse=True)

print("\n" + "=" * 60)
print("TOP 10 RESULTS (Sorted by Stars)")
print("=" * 60)

for i, (name, info) in enumerate(sorted_results[:10], 1):
    print(f"\n{i}. {name}")
    print(f"   ⭐ Stars: {info['stars']:,}")
    print(f"   📝 {info['description']}")
    print(f"   🔗 {info['url']}")
    print(f"   💻 Language: {info['language']}")

print("\n" + "=" * 60)
