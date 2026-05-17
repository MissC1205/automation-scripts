#!/usr/bin/env python3
"""
AI新闻简报生成器 - 2026年5月12日
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

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

def fetch_36kr_ai():
    """获取36kr AI相关新闻"""
    news = []
    try:
        # 36kr RSS feed
        url = "https://36kr.com/feed"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            # 解析RSS
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            channel = root.find('channel')
            if channel:
                items = channel.findall('item')
                for item in items[:5]:
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')
                    pubdate = item.find('pubDate')
                    if title is not None and title.text:
                        news.append({
                            "title": title.text.strip(),
                            "link": link.text if link is not None and link.text else "",
                            "source": "36kr",
                            "pubdate": pubdate.text[:16] if pubdate is not None and pubdate.text else ""
                        })
    except Exception as e:
        print(f"36kr获取失败: {e}")
    return news

def fetch_ai_qbitai():
    """获取量子位AI新闻"""
    news = []
    try:
        url = "https://www.qbitai.com/feed"
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
                    if title is not None and title.text:
                        news.append({
                            "title": title.text.strip(),
                            "link": link.text if link is not None and link.text else "",
                            "source": "量子位",
                            "pubdate": ""
                        })
    except Exception as e:
        print(f"量子位获取失败: {e}")
    return news

def fetch_weibo_ai_hot():
    """获取微博AI相关热搜"""
    news = []
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get("ok") == 1:
            realtime = data.get("data", {}).get("realtime", [])
            for item in realtime[:10]:
                word = item.get("word", "")
                num = item.get("num", 0)
                # 筛选AI相关关键词
                ai_keywords = ["AI", "人工智能", "大模型", "ChatGPT", "OpenAI", "DeepSeek", "豆包", "Kimi", "文心", "通义", "智谱", "大模型", "AI发布", "AI更新", "AI芯片", "AI助手"]
                if any(kw in word for kw in ai_keywords):
                    news.append({
                        "title": word,
                        "link": "",
                        "source": "微博热搜",
                        "pubdate": f"热度: {num}"
                    })
    except Exception as e:
        print(f"微博热搜获取失败: {e}")
    return news

def fetch_jiqizhixin():
    """获取机器之心新闻"""
    news = []
    try:
        url = "https://www.jiqizhixin.com/feed"
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
                    if title is not None and title.text:
                        news.append({
                            "title": title.text.strip(),
                            "link": link.text if link is not None and link.text else "",
                            "source": "机器之心",
                            "pubdate": ""
                        })
    except Exception as e:
        print(f"机器之心获取失败: {e}")
    return news

def search_twitter_ai():
    """搜索Twitter/X AI热门话题"""
    news = []
    try:
        # 使用Nitter镜像获取 trending topics
        url = "https://nitter.privacydev.net/search?f=tweets&q=AI+OR+%23AI+OR+%23ArtificialIntelligence&since=&until=&near="
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            # 简单解析
            pattern = r'<a href="/i/status/\d+"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, resp.text)
            for match in matches[:5]:
                if match and len(match) > 10:
                    news.append({
                        "title": match.strip(),
                        "link": "https://twitter.com",
                        "source": "Twitter/X",
                        "pubdate": ""
                    })
    except Exception as e:
        print(f"Twitter搜索失败: {e}")
    return news

def get_ai_news_summary():
    """汇总所有AI新闻"""
    all_news = []
    
    print("正在获取36kr AI新闻...")
    all_news.extend(fetch_36kr_ai())
    
    print("正在获取量子位AI新闻...")
    all_news.extend(fetch_ai_qbitai())
    
    print("正在获取微博AI热搜...")
    all_news.extend(fetch_weibo_ai_hot())
    
    print("正在获取机器之心新闻...")
    all_news.extend(fetch_jiqizhixin())
    
    print("正在获取Twitter AI动态...")
    all_news.extend(search_twitter_ai())
    
    return all_news

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI新闻简报 - 2026年5月12日")
    print("=" * 60)
    
    news = get_ai_news_summary()
    
    print(f"\n📊 共获取 {len(news)} 条AI相关资讯\n")
    
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item['source']}] {item['title']}")
        if item.get('link'):
            print(f"   🔗 {item['link'][:80]}...")
        if item.get('pubdate'):
            print(f"   🕐 {item['pubdate']}")
        print()
    
    # 保存结果
    out_dir = Path.home() / ".hermes" / "ai_news"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ai_news_20260512.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(news, ensure_ascii=False, indent=2, fp=f)
    print(f"💾 已保存到: {path}")