#!/usr/bin/env python3
"""
今日AI新闻简报抓取器 - 2026年5月12日
目标来源：量子位、机器之心、36kr AI、爱范儿
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("安装依赖...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "-q"])
    import requests
    from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def clean_html(text):
    """清理HTML标签和特殊字符"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&#39;', "'").replace('&quot;', '"')
    text = text.replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def fetch_ithome_ai():
    """获取IT之家AI频道"""
    news = []
    try:
        url = "https://www.ithome.com/ai/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 尝试多种选择器
        articles = soup.select('ul.list li, .item, .news-item, article')
        if not articles:
            articles = soup.find_all('li')
        
        for art in articles[:10]:
            title_elem = art.select_one('h3, h2, .title, a') or art
            title = clean_html(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            if title and len(title) > 10 and ('AI' in title or '人工智能' in title or '大模型' in title or 'GPT' in title):
                link = art.find('a')
                link = link.get('href', '') if link else ''
                if link and not link.startswith('http'):
                    link = 'https://www.ithome.com' + link
                news.append({
                    "title": title[:80],
                    "link": link,
                    "source": "量子位/IT之家"
                })
    except Exception as e:
        print(f"IT之家获取失败: {e}")
    return news

def fetch_jiqizhixin():
    """获取机器之心"""
    news = []
    try:
        url = "https://www.jiqizhixin.com/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = soup.select('article, .article-item, .news-item, .card')
        
        for art in articles[:10]:
            title_elem = art.select_one('h3, h2, h4, .title, a') or art
            title = clean_html(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            if title and len(title) > 10:
                link = art.find('a')
                link = link.get('href', '') if link else ''
                if link and not link.startswith('http'):
                    link = 'https://www.jiqizhixin.com' + link
                news.append({
                    "title": title[:80],
                    "link": link,
                    "source": "机器之心"
                })
    except Exception as e:
        print(f"机器之心获取失败: {e}")
    return news

def fetch_36kr_ai():
    """获取36kr AI频道"""
    news = []
    try:
        url = "https://36kr.com/information/AI/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = soup.select('article, .article-item, .kr-news-item, .news-item')
        
        for art in articles[:10]:
            title_elem = art.select_one('h3, h2, .title, a') or art
            title = clean_html(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            if title and len(title) > 10:
                link = art.find('a')
                link = link.get('href', '') if link else ''
                if link and not link.startswith('http'):
                    link = 'https://36kr.com' + link
                news.append({
                    "title": title[:80],
                    "link": link,
                    "source": "36kr"
                })
    except Exception as e:
        print(f"36kr获取失败: {e}")
    return news

def fetch_ifeng_ai():
    """获取爱范儿AI频道"""
    news = []
    try:
        url = "https://www.ifanr.com/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = soup.select('article, .post, .item, .article')
        
        for art in articles[:10]:
            title_elem = art.select_one('h3, h2, h4, .title, a') or art
            title = clean_html(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            if title and len(title) > 10 and ('AI' in title or '人工智能' in title):
                link = art.find('a')
                link = link.get('href', '') if link else ''
                if link and not link.startswith('http'):
                    link = 'https://www.ifanr.com' + link
                news.append({
                    "title": title[:80],
                    "link": link,
                    "source": "爱范儿"
                })
    except Exception as e:
        print(f"爱范儿获取失败: {e}")
    return news

def fetch_zhidx_ai():
    """获取中关村在线AI频道"""
    news = []
    try:
        url = "https://ai.zol.com.cn/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = soup.select('li, .item, .news-item, article')
        
        for art in articles[:10]:
            title_elem = art.select_one('a, h3, h2, .t') or art
            title = clean_html(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            if title and len(title) > 10:
                link = art.find('a')
                link = link.get('href', '') if link else ''
                if link and not link.startswith('http'):
                    link = 'https://ai.zol.com.cn' + link
                news.append({
                    "title": title[:80],
                    "link": link,
                    "source": "中关村在线AI"
                })
    except Exception as e:
        print(f"中关村在线获取失败: {e}")
    return news

def get_article_content(url, source_name):
    """抓取文章详细内容"""
    if not url or len(url) < 10:
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # 尝试获取正文
        content = soup.select_one('article, .article-content, .post-content, .content, #article, .text')
        if content:
            text = clean_html(content.get_text())
            return text[:500] if text else ""
    except Exception as e:
        print(f"内容抓取失败 ({source_name}): {e}")
    return ""

def main():
    print("=" * 60)
    print("🤖 今日AI新闻简报 - 2026年5月12日")
    print("=" * 60)
    
    all_news = []
    
    print("\n📡 正在获取量子位/IT之家 AI资讯...")
    news = fetch_ithome_ai()
    print(f"   获取到 {len(news)} 条")
    all_news.extend(news)
    
    print("📡 正在获取机器之心...")
    news = fetch_jiqizhixin()
    print(f"   获取到 {len(news)} 条")
    all_news.extend(news)
    
    print("📡 正在获取36kr AI频道...")
    news = fetch_36kr_ai()
    print(f"   获取到 {len(news)} 条")
    all_news.extend(news)
    
    print("📡 正在获取爱范儿...")
    news = fetch_ifeng_ai()
    print(f"   获取到 {len(news)} 条")
    all_news.extend(news)
    
    print("📡 正在获取中关村在线AI...")
    news = fetch_zhidx_ai()
    print(f"   获取到 {len(news)} 条")
    all_news.extend(news)
    
    print(f"\n✅ 共获取 {len(all_news)} 条原始资讯")
    
    # 去重
    seen = set()
    unique_news = []
    for item in all_news:
        if item['title'] not in seen:
            seen.add(item['title'])
            unique_news.append(item)
    
    print(f"📰 去重后 {len(unique_news)} 条")
    
    # 保存原始数据
    out_dir = Path("/home/ubuntu/.hermes/ai_news")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    raw_path = out_dir / f"raw_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(unique_news, ensure_ascii=False, indent=2, fp=f)
    print(f"\n💾 原始数据已保存: {raw_path}")
    
    # 打印新闻列表
    print("\n" + "=" * 60)
    print("📋 获取到的新闻标题:")
    print("=" * 60)
    for i, item in enumerate(unique_news[:15], 1):
        print(f"{i}. [{item['source']}] {item['title'][:60]}")
        if item['link']:
            print(f"   🔗 {item['link'][:80]}")
    
    return unique_news

if __name__ == "__main__":
    news = main()