#!/usr/bin/env python3
"""
微博热搜爬虫 - weibo_scraper.py
用法:
  python3 weibo_scraper.py              # 热榜
  python3 weibo_scraper.py --hot        # 热搜榜
  python3 weibo_scraper.py --realtime   # 实时上升
  python3 weibo_scraper.py --comments MID  # 评论(需cookie)
  python3 weibo_scraper.py --search "关键词"  # 搜索
  python3 weibo_scraper.py --all        # 全量
"""

import argparse
import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)


# ── 配置 ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://weibo.com/",
    "X-Requested-With": "XMLHttpRequest",
}
COOKIE_FILE = Path.home() / ".hermes" / "weibo_cookie.txt"
SESSION_FILE = Path.home() / ".hermes" / "weibo_session.json"


def get_session():
    """创建带 cookie 的 session"""
    s = requests.Session()
    s.headers.update(HEADERS)

    # 尝试加载保存的 cookie
    if COOKIE_FILE.exists():
        cookie_str = COOKIE_FILE.read_text().strip()
        if cookie_str:
            for line in cookie_str.split(";"):
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    s.cookies.set(k.strip(), v.strip(), domain=".weibo.com")

    # 尝试加载保存的 session storage
    if SESSION_FILE.exists():
        try:
            session_data = json.loads(SESSION_FILE.read_text())
            # 部分微博接口支持 header 中带Authorization
            if session_data.get("Authorization"):
                s.headers["Authorization"] = session_data["Authorization"]
        except Exception:
            pass

    return s


def load_cookie_from_env():
    """从环境变量加载 cookie"""
    env_cookie = os.environ.get("WEIBO_COOKIE", "")
    if env_cookie:
        print(f"📝 检测到 WEIBO_COOKIE 环境变量")
        COOKIE_FILE.write_text(env_cookie)


def clean_html(text: str) -> str:
    """去除 HTML 标签"""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&#39;", "'").replace("&quot;", '"')
    return text.strip()


def save_results(data: dict, name: str):
    """保存结果到文件"""
    out_dir = Path.home() / ".hermes" / "weibo_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{name}_{ts}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"💾 保存到: {path}")
    return path


# ── API 接口 ──────────────────────────────────────────

def fetch_hot_search(session) -> dict:
    """获取热搜榜单"""
    url = "https://weibo.com/ajax/side/hotSearch"
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("ok") != 1:
        print(f"❌ API 错误: {data.get('error', data)}")
        return {}

    result = data.get("data", {})

    # 格式化输出
    print("\n" + "=" * 60)
    print("🔥 微博热搜榜")
    print("=" * 60)

    # 政府热搜
    hotgov = result.get("hotgov", {})
    if hotgov:
        print(f"\n🏛️  置顶: {hotgov.get('word', '')}")

    # 实时热搜
    realtime = result.get("realtime", [])
    print(f"\n📊 实时上升 ({len(realtime)}条)\n")
    for i, item in enumerate(realtime[:20], 1):
        label = item.get("label_name", "")
        icon_desc = item.get("icon_desc", "")
        word = item.get("word", "")
        num = item.get("num", 0)
        flag = item.get("flag", 0)
        flag_desc = item.get("flag_desc", "")

        # 热度格式化
        if num >= 1000000:
            num_str = f"{num/1000000:.1f}亿"
        elif num >= 10000:
            num_str = f"{num/10000:.1f}万"
        else:
            num_str = str(num)

        # 图标
        icon_map = {"新": "🆕", "热": "🔥", "沸": "♨️", "荐": "⭐", "爆": "💥", "商": "💰"}
        icon = icon_map.get(icon_desc, "  ")

        type_icon = ""
        if flag_desc:
            type_icon = f"[{flag_desc}]"

        print(f"  {i:>2}. {icon} {num_str:>8} {type_icon}{word}")

    # 热搜版
    band_list = result.get("band_list", [])
    print(f"\n📋 热搜榜单 ({len(band_list)}条)\n")
    for i, item in enumerate(band_list[:20], 1):
        word = item.get("word", "")
        num = item.get("num", 0)
        label = item.get("label_name", "")

        if num >= 10000:
            num_str = f"{num/10000:.0f}万"
        else:
            num_str = str(num)

        print(f"  {i:>2}. {num_str:>6} {word}")

    # 娱乐版
    film = result.get("film", [])
    if film:
        print(f"\n🎬 娱乐榜 ({len(film)}条)\n")
        for i, item in enumerate(film[:10], 1):
            word = item.get("word", "")
            num = item.get("num", 0)
            if num >= 10000:
                num_str = f"{num/10000:.0f}万"
            else:
                num_str = str(num)
            print(f"  {i:>2}. {num_str:>6} {word}")

    return result


def fetch_realtime(session, page: int = 1) -> dict:
    """获取实时上升"""
    url = f"https://weibo.com/ajax/side/hotSearch?page={page}"
    resp = session.get(url, timeout=10)
    data = resp.json()
    result = data.get("data", {})
    realtime = result.get("realtime", [])

    print(f"\n📈 实时上升 (第{page}页, {len(realtime)}条)\n")
    for i, item in enumerate(realtime, 1):
        word = item.get("word", "")
        num = item.get("num", 0)
        icon = item.get("icon_desc", "")
        flag = item.get("flag_desc", "")

        if num >= 1000000:
            num_str = f"{num/1000000:.1f}亿"
        elif num >= 10000:
            num_str = f"{num/10000:.1f}万"
        else:
            num_str = str(num)

        print(f"  {i:>2}. [{icon}] {num_str:>8} {flag} {word}")

    return {"realtime": realtime}


def fetch_topic_detail(session, topic: str) -> dict:
    """获取话题详情"""
    import urllib.parse
    encoded = urllib.parse.quote(topic)
    url = f"https://weibo.com/ajax/side/hotSearch?containerid=100103type%3D1%26q%3D{encoded}"
    resp = session.get(url, timeout=10)
    data = resp.json()
    return data.get("data", {})


def search_weibo(session, keyword: str, page: int = 1) -> dict:
    """搜索微博"""
    import urllib.parse
    encoded = urllib.parse.quote(keyword)
    url = f"https://weibo.com/ajax/search?q={encoded}&page={page}"
    resp = session.get(url, timeout=10)
    data = resp.json()

    if data.get("ok") == 1:
        statuses = data.get("data", {}).get("statuses", [])
        print(f"\n🔍 搜索「{keyword}」共 {len(statuses)} 条\n")
        for s in statuses[:10]:
            user = s.get("user", {})
            text = clean_html(s.get("text", ""))
            created = s.get("created_at", "")
            attitudes = s.get("attitudes_count", 0)
            comments = s.get("comments_count", 0)
            reposts = s.get("reposts_count", 0)
            print(f"  👤 {user.get('screen_name', 'unknown')}  {created}")
            print(f"     {text[:120]}")
            print(f"     👍{attitudes} 💬{comments} 🔁{reposts}\n")
        return {"statuses": statuses}
    return {}


def fetch_comments(session, mid: str, page: int = 1) -> dict:
    """获取微博评论 (需要登录)"""
    url = f"https://weibo.com/ajax/comments?id={mid}&page={page}&count=20"
    resp = session.get(url, timeout=10)
    data = resp.json()

    if data.get("ok") == 1:
        comments = data.get("data", [])
        print(f"\n💬 评论 (第{page}页, {len(comments)}条)\n")
        for c in comments[:20]:
            user = c.get("user", {})
            text = clean_html(c.get("text", ""))
            like_count = c.get("like_count", 0)
            created = c.get("created_at", "")
            print(f"  👤 {user.get('screen_name','?')}  👍{like_count}  {created}")
            print(f"     {text[:120]}\n")
        return {"comments": comments, "total": data.get("total_number", 0)}
    else:
        print(f"❌ 获取评论失败: {data.get('msg', data)}")
        print("💡 需要设置 WEIBO_COOKIE 环境变量")
        return {}


def fetch_user_posts(session, uid: str = "1195230310", page: int = 1) -> dict:
    """获取用户微博"""
    url = f"https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0"
    resp = session.get(url, timeout=10)
    data = resp.json()

    if data.get("ok") == 1:
        posts = data.get("data", {}).get("list", [])
        print(f"\n📱 用户微博 (第{page}页, {len(posts)}条)\n")
        for p in posts[:10]:
            text = clean_html(p.get("text", ""))
            created = p.get("created_at", "")
            attitudes = p.get("attitudes_count", 0)
            comments = p.get("comments_count", 0)
            reposts = p.get("reposts_count", 0)
            mid = p.get("id", "")
            print(f"  🕐 {created}")
            print(f"     {text[:150]}")
            print(f"     👍{attitudes} 💬{comments} 🔁{reposts}  MID:{mid}\n")
        return {"posts": posts}
    return {}


def fetch_trending_topics(session) -> dict:
    """获取超话/超新星等分类榜单"""
    url = "https://weibo.com/ajax/side/hotSearch"
    resp = session.get(url, timeout=10)
    data = resp.json()
    result = data.get("data", {})

    categories = {}
    for key in ["realtime", "hotgov", "band_list", "film", "novel", "cartoon",
                "movie", "tv", "game", "sports", "music", "finance"]:
        if key in result:
            categories[key] = result[key]

    print("\n📁 全部分类榜单\n")
    for cat, items in categories.items():
        if items:
            print(f"  📂 {cat}: {len(items)}条")

    return categories


# ── 主入口 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="微博热搜爬虫", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hot", action="store_true", help="热搜榜")
    parser.add_argument("--realtime", action="store_true", help="实时上升")
    parser.add_argument("--realtime-page", type=int, default=1, help="实时上升页码")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--comments", type=str, help="获取微博评论 (提供MID)")
    parser.add_argument("--comments-page", type=int, default=1, help="评论页码")
    parser.add_argument("--user", type=str, default="1195230310", help="用户UID")
    parser.add_argument("--user-page", type=int, default=1, help="用户微博页码")
    parser.add_argument("--trending", action="store_true", help="全部分类榜单")
    parser.add_argument("--all", action="store_true", help="完整热搜+分类")
    parser.add_argument("--save", action="store_true", help="保存到文件")
    parser.add_argument("--cookie", type=str, help="微博cookie (或设置 WEIBO_COOKIE 环境变量)")

    args = parser.parse_args()

    # 环境变量 cookie 优先
    load_cookie_from_env()

    # 命令行 cookie
    if args.cookie:
        COOKIE_FILE.write_text(args.cookie)
        print("📝 已保存 cookie 到文件")

    session = get_session()

    # 如果没有任何参数，默认拉热搜
    if len(sys.argv) == 1:
        result = fetch_hot_search(session)
        if args.save and result:
            save_results(result, "hot_search")
        return

    if args.hot:
        result = fetch_hot_search(session)
        if args.save and result:
            save_results(result, "hot_search")

    if args.realtime:
        result = fetch_realtime(session, args.realtime_page)
        if args.save and result:
            save_results(result, "realtime")

    if args.search:
        result = search_weibo(session, args.search)
        if args.save and result:
            save_results(result, f"search_{args.search}")

    if args.comments:
        result = fetch_comments(session, args.comments, args.comments_page)
        if args.save and result:
            save_results(result, f"comments_{args.comments}")

    if args.user:
        result = fetch_user_posts(session, args.user, args.user_page)
        if args.save and result:
            save_results(result, f"user_{args.user}")

    if args.trending:
        result = fetch_trending_topics(session)
        if args.save and result:
            save_results(result, "trending_all")

    if args.all:
        result = fetch_hot_search(session)
        trending = fetch_trending_topics(session)
        if args.save and result:
            save_results({"hot_search": result, "trending": trending}, "complete")


if __name__ == "__main__":
    main()
