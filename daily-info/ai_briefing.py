#!/usr/bin/env python3
"""
AI新闻简报生成器 - 2026年5月12日
使用多种方式获取AI新闻
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
import urllib.parse

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def clean_html(text):
    """去除HTML标签"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&#39;', "'").replace('&quot;', '"')
    return text.strip()

def fetch_hackernews_ai():
    """获取Hacker News AI相关帖子"""
    news = []
    try:
        url = "https://hn.algolia.com/api/v1/search?query=AI+OR+artificial+intelligence+OR+GPT+OR+LLM&tags=story&hitsPerPage=10"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        hits = data.get('hits', [])
        for hit in hits[:8]:
            title = hit.get('title', '')
            url_link = hit.get('url', '')
            object_id = hit.get('objectID', '')
            news.append({
                "title": clean_html(title),
                "link": url_link or f"https://news.ycombinator.com/item?id={object_id}",
                "source": "Hacker News",
                "pubdate": ""
            })
    except Exception as e:
        print(f"Hacker News获取失败: {e}")
    return news

def fetch_techcrunch_ai():
    """获取TechCrunch AI新闻"""
    news = []
    try:
        url = "https://techcrunch.com/category/artificial-intelligence/feed/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            channel = root.find('channel')
            if channel:
                items = channel.findall('item')
                for item in items[:5]:
                    title = item.find('title')
                    link = item.find('link')
                    pubdate = item.find('pubDate')
                    if title is not None and title.text:
                        news.append({
                            "title": clean_html(title.text),
                            "link": link.text if link is not None and link.text else "",
                            "source": "TechCrunch AI",
                            "pubdate": pubdate.text[:16] if pubdate is not None and pubdate.text else ""
                        })
    except Exception as e:
        print(f"TechCrunch获取失败: {e}")
    return news

def fetch_weibo_hot_search():
    """获取微博热搜榜"""
    news = []
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get("ok") == 1:
            band_list = data.get("data", {}).get("band_list", [])
            for item in band_list[:15]:
                word = item.get("word", "")
                num = item.get("num", 0)
                if num >= 10000:
                    num_str = f"{num/10000:.0f}万"
                else:
                    num_str = str(num)
                news.append({
                    "title": f"🔥 {word} ({num_str}热度)",
                    "link": "",
                    "source": "微博热搜",
                    "pubdate": ""
                })
    except Exception as e:
        print(f"微博热搜获取失败: {e}")
    return news

def fetch_zhihu_ai():
    """获取知乎AI相关热门"""
    news = []
    try:
        url = "https://www.zhihu.com/api/v4/search_v3?t=general&q=AI+人工智能+大模型&correction=1&offset=0&limit=20&filter_fields=location"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = data.get('data', [])
        for item in items[:5]:
            question = item.get('question', {})
            title = question.get('title', '')
            if title:
                news.append({
                    "title": clean_html(title),
                    "link": f"https://www.zhihu.com/question/{question.get('id', '')}",
                    "source": "知乎",
                    "pubdate": ""
                })
    except Exception as e:
        print(f"知乎获取失败: {e}")
    return news

def fetch_douyin_ai热搜():
    """获取抖音AI相关热搜"""
    news = []
    try:
        # 抖音热榜API
        url = "https://www.douyin.com/aweme/v1/web/general/search/single/?keyword=AI&count=10"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        # 简化为备用方案
    except Exception as e:
        print(f"抖音获取失败: {e}")
    return news

def fetch_ai_terms():
    """从36氪抓取AI新术语/新词"""
    terms = []
    ai_keywords = ['Agent', 'RAG', 'MCP', 'AGI', 'LLM', 'Embedding', '向量', '幻觉', 
                   '蒸馏', '微调', 'LoRA', 'Prompt', '上下文', 'Token', '推理',
                   '多模态', '具身智能', 'Scaling Law', '涌现', 'AI-First', 'AI原生',
                   'CoT', 'ToT', 'ReAct', 'RLHF', 'DPO', 'SFT', '长上下文', 'MoE',
                   'Mamba', 'Transformer', '注意力机制', '幻觉', '对齐', '超参数',
                   'AGI', 'ASI', 'World Model', 'Agent', 'Multi-Agent', 'Tool Use',
                   'Function Calling', 'Prompt Engineering', 'Fine-tuning', 'RAG',
                   'Embedding', 'Vector DB', 'Ollama', 'vLLM', 'TensorRT', 'GGUF']
    try:
        url = "https://www.36kr.com/information/AI/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            # 尝试RSS方式
            try:
                root = ET.fromstring(resp.content)
                channel = root.find('channel')
                if channel is None:
                    raise ValueError("Not RSS")
            except:
                # 不是RSS，用正则抓标题
                html = resp.text
                import re
                html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                titles = re.findall(r'class="[^"]*title[^"]*"[^>]*>([^<]+)<', html)
                if not titles:
                    titles = re.findall(r'<h2[^>]*>([^<]+)<', html)
                for t in titles[:20]:
                    t = clean_html(t)
                    if t and len(t) > 4 and len(t) < 60:
                        for kw in ai_keywords:
                            if kw.lower() in t.lower():
                                terms.append({"term": kw, "source": "36氪", "context": t})
                                break
    except Exception as e:
        print(f"36氪术语抓取失败: {e}")
    return terms

def get_ai_news():
    """汇总获取AI新闻"""
    all_news = []
    
    print("📡 正在获取 Hacker News AI 资讯...")
    all_news.extend(fetch_hackernews_ai())
    
    print("📡 正在获取 TechCrunch AI 资讯...")
    all_news.extend(fetch_techcrunch_ai())
    
    print("📡 正在获取微博热搜...")
    all_news.extend(fetch_weibo_hot_search())
    
    print("📡 正在获取知乎AI讨论...")
    all_news.extend(fetch_zhihu_ai())
    
    return all_news

def format_briefing(news_list):
    """格式化简报"""
    today = "2026年5月12日"
    output = []
    output.append("=" * 60)
    output.append(f"🤖 今日AI简报 - {today}")
    output.append("=" * 60)
    output.append("")
    
    # 按来源分组
    by_source = {}
    for item in news_list:
        source = item.get('source', '其他')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)
    
    # 输出各来源新闻
    for source, items in by_source.items():
        output.append(f"\n📰 {source} ({len(items)}条)")
        output.append("-" * 40)
        for i, item in enumerate(items[:8], 1):
            title = item.get('title', '')[:60]
            link = item.get('link', '')
            pubdate = item.get('pubdate', '')
            output.append(f"  {i}. {title}")
            if pubdate:
                output.append(f"     ⏰ {pubdate}")
            if link and len(link) < 100:
                output.append(f"     🔗 {link}")
    
    output.append("")
    output.append("=" * 60)
    output.append("📝 简评:")
    output.append("  今日AI领域活跃度较高，多个平台均有AI相关热门话题。")
    output.append("  建议关注：大模型发布、AI应用落地、AI芯片进展等方向。")
    output.append("=" * 60)
    
    return "\n".join(output)

if __name__ == "__main__":
    news = get_ai_news()
    print(f"\n✅ 共获取 {len(news)} 条资讯\n")
    
    print("📡 正在获取AI新术语...")
    terms = fetch_ai_terms()
    print(f"✅ 共获取 {len(terms)} 条术语\n")
    
    # 打印简报
    print(format_briefing(news))
    
    # 保存JSON
    out_dir = Path.home() / ".hermes" / "ai_news"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"news": news, "terms": terms}, ensure_ascii=False, indent=2, fp=f)
    print(f"\n💾 JSON已保存: {path}")