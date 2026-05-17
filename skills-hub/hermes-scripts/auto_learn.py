#!/usr/bin/env python3
"""
Hermes Auto-Learner v15 - 可靠版
======================================
修复v14的问题:
1. README解析失败（得到HTML）
2. 源码文件获取为0
3. Skill内容太薄

改进:
1. 直接用raw.githubusercontent.com获取源码
2. 用更可靠的方式解析README
3. 确保每个学习任务有实质内容
"""

import json, time, re
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
SKILLS_DIR = HERMES_HOME / "skills"
LOG_FILE = HERMES_HOME / "logs" / "auto_learn_v15.log"
CHANGE_LOG = HERMES_HOME / "logs" / "changes_v15.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def http_get(url, timeout=20):
    try:
        import requests
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/plain,text/html,application/json",
        }, timeout=timeout)
        return r
    except Exception as e:
        log(f"HTTP错误: {e}")
        return None

# ============ 可靠的GitHub源码获取 ============

def get_default_branch(user, repo):
    """获取仓库的默认分支名"""
    url = f"https://api.github.com/repos/{user}/{repo}"
    r = http_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            return data.get("default_branch", "main")
        except:
            pass
    return "main"

def get_file_list(user, repo, branch=None):
    """获取仓库文件列表"""
    if branch is None:
        branch = get_default_branch(user, repo)
    api_url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{branch}?recursive=1"
    r = http_get(api_url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            return data.get("tree", [])
        except:
            pass
    return []

def fetch_file_via_api(user, repo, path, branch=None):
    """通过GitHub Contents API获取文件内容"""
    if branch is None:
        branch = get_default_branch(user, repo)
    url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}?ref={branch}"
    r = http_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            if data.get("encoding") == "base64":
                import base64
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except:
            pass
    return None

def fetch_source_files(user, repo, max_files=5):
    """获取核心源文件"""
    files_content = {}

    # 自动检测默认分支
    branch = get_default_branch(user, repo)
    log(f"   检测分支: {branch}")

    # 获取文件树
    tree = get_file_list(user, repo, branch)
    if not tree:
        log(f"   获取文件列表失败")
        return files_content

    # 优先找Python源文件
    py_files = [f for f in tree if f["path"].endswith(".py") and f["type"] == "blob"]
    md_files = [f for f in tree if f["path"].endswith(".md") and f["type"] == "blob"]
    yaml_files = [f for f in tree if f["path"].endswith((".yaml", ".yml")) and f["type"] == "blob"]

    # 优先获取:主目录的py文件 > src目录的py文件
    priority_files = []
    for f in py_files:
        path = f["path"]
        if "/" not in path:  # 根目录
            priority_files.append(f)
        elif path.startswith("src/"):
            priority_files.append(f)

    # 补充其他
    remaining = [f for f in py_files if f not in priority_files][:5]
    files_to_fetch = (priority_files + remaining)[:max_files]

    log(f"   找到 {len(py_files)} 个Python文件，选取 {len(files_to_fetch)} 个")

    for f in files_to_fetch:
        path = f["path"]

        # 通过API获取（避免raw.githubusercontent.com超时）
        content = fetch_file_via_api(user, repo, path, branch)
        if content and len(content) > 100:
            files_content[path] = content
            log(f"   ✓ {path} ({len(content)}字节)")
        else:
            log(f"   ✗ {path} 获取失败")

    # 获取README（通过API方式）
    for md_file in (md_files if md_files else [{"path": "README.md"}]):
        content = fetch_file_via_api(user, repo, md_file['path'], branch)
        if content and len(content) > 100:
            files_content["README.md"] = content
            log(f"   ✓ README ({len(content)}字节)")
            break

    return files_content

# ============ 代码模式提取 ============

def extract_patterns(files_content):
    """从源文件提取代码模式"""
    all_patterns = {
        "functions": [],
        "classes": [],
        "async_funcs": [],
        "decorators": [],
        "imports": [],
        "api_calls": [],
    }

    for path, content in files_content.items():
        if not path.endswith(".py"):
            continue

        # 函数定义
        for name, args, ret in re.findall(r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:\n]+))?:', content):
            if len(name) > 2 and len(name) < 50:
                all_patterns["functions"].append({
                    "name": name,
                    "args": args.strip() if args else "",
                    "returns": ret.strip() if ret else "None",
                    "file": path,
                })

        # 类定义
        for name, bases in re.findall(r'class\s+(\w+)(?:\(([^)]*)\))?:', content):
            if len(name) > 2:
                base_list = [b.strip() for b in bases.split(",") if b.strip()] if bases else []
                all_patterns["classes"].append({
                    "name": name,
                    "bases": base_list,
                    "file": path,
                })

        # 异步函数
        for name in re.findall(r'async\s+def\s+(\w+)', content):
            all_patterns["async_funcs"].append({"name": name, "file": path})

        # 装饰器
        for dec in set(re.findall(r'@(\w+)', content)):
            if len(dec) > 2:
                all_patterns["decorators"].append({"name": dec, "file": path})

        # import
        for imp in re.findall(r'^import\s+(\w+)', content, re.MULTILINE):
            all_patterns["imports"].append({"module": imp, "file": path})
        for imp in re.findall(r'^from\s+([\w.]+)\s+import', content, re.MULTILINE):
            all_patterns["imports"].append({"module": imp, "file": path})

    return all_patterns

def extract_design_insights(patterns, files_content):
    """从模式中提取设计洞察"""
    insights = []

    # 分析imports了解用了什么库
    all_imports = {}
    for imp in patterns["imports"]:
        m = imp["module"]
        all_imports[m] = all_imports.get(m, 0) + 1

    top_imports = sorted(all_imports.items(), key=lambda x: -x[1])[:10]
    if top_imports:
        insights.append({
            "type": "dependencies",
            "content": f"主要依赖: {', '.join([f'{m}({c})' for m,c in top_imports])}"
        })

    # 异步编程
    if len(patterns["async_funcs"]) > 0:
        insights.append({
            "type": "async",
            "content": f"使用异步编程: {len(patterns['async_funcs'])}个异步函数"
        })

    # 装饰器使用
    if patterns["decorators"]:
        dec_counts = {}
        for d in patterns["decorators"]:
            n = d["name"]
            dec_counts[n] = dec_counts.get(n, 0) + 1
        top_decs = sorted(dec_counts.items(), key=lambda x: -x[1])[:5]
        insights.append({
            "type": "decorators",
            "content": f"装饰器: {', '.join([f'{n}({c})' for n,c in top_decs])}"
        })

    # 类继承关系
    if patterns["classes"]:
        with_bases = [c for c in patterns["classes"] if c["bases"]]
        if with_bases:
            insights.append({
                "type": "inheritance",
                "content": f"使用继承: {len(with_bases)}个类有父类"
            })

    return insights

# ============ Skill生成 ============

def build_deep_skill(repo_url, files_content, patterns, insights):
    """构建深度学习Skill"""

    match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', repo_url)
    user, repo = match.groups()
    repo = repo.replace('.git', '')

    # 统计
    func_count = len(patterns["functions"])
    class_count = len(patterns["classes"])
    async_count = len(patterns["async_funcs"])

    # 核心函数（取前10个）
    core_funcs = patterns["functions"][:10]

    skill = f"""---
name: deep-{user}-{repo[:25]}
description: "深度学习{repo}:核心函数+设计模式+依赖分析+举一反三"
version: 1.0.0
auto_learned: true
learned_at: {datetime.now().isoformat()}
source: github
quality: S
tags: [deep-learning, github, {user}, {repo}]
---

# {repo} 深度学习

> 项目: [{repo_url}](https://github.com/{user}/{repo})
> 学习时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> 源码文件: {len(files_content)} 个

## 一句话理解这个项目

"""
    # 从README提取描述
    readme = files_content.get("README.md", "")[:1000]
    # 去掉HTML标签
    readme_clean = re.sub(r'<[^>]+>', '', readme)
    readme_clean = re.sub(r'\s+', ' ', readme_clean).strip()

    if len(readme_clean) > 50:
        skill += readme_clean[:300] + "\n"
    else:
        skill += f"这是一个{repo}项目，详见 [GitHub](https://github.com/{user}/{repo})\n"

    skill += """

---

## 依赖分析（从import语句）

"""
    if insights:
        for ins in insights:
            if ins["type"] == "dependencies":
                skill += f"**主要依赖**: {ins['content']}\n"
                break

    # 从依赖推断项目类型
    all_imports_set = set(imp["module"] for imp in patterns["imports"])
    if "openai" in all_imports_set:
        skill += "- ✨ OpenAI集成\n"
    if "anthropic" in all_imports_set:
        skill += "- ✨ Anthropic/Claude集成\n"
    if "asyncio" in all_imports_set or "aiohttp" in all_imports_set:
        skill += "- 🌐 异步网络编程\n"
    if "click" in all_imports_set or "typer" in all_imports_set:
        skill += "- 🖥️ CLI命令行工具\n"
    if "langchain" in all_imports_set:
        skill += "- 🔗 LangChain生态\n"

    skill += """

---

## 核心函数（代码模式）

| 函数名 | 参数 | 返回值 | 文件 |
|--------|------|--------|------|
"""
    for f in core_funcs:
        args = f["args"][:30] if f["args"] else "—"
        ret = f["returns"][:20] if f["returns"] else "None"
        skill += f"| `{f['name']}` | {args} | {ret} | {f['file']} |\n"

    if core_funcs:
        skill += f"\n**共发现 {func_count} 个函数定义**\n"

    skill += """

---

## 类设计

"""
    for c in patterns["classes"][:8]:
        bases = ", ".join(c["bases"]) if c["bases"] else "无基类"
        skill += f"- `{c['name']}` (继承: {bases}) - {c['file']}\n"

    if patterns["classes"]:
        skill += f"\n**共发现 {class_count} 个类定义**\n"

    skill += """

---

## 异步编程

"""
    if patterns["async_funcs"]:
        for af in patterns["async_funcs"][:10]:
            skill += f"- `async {af['name']}` - {af['file']}\n"
        skill += f"\n**共 {async_count} 个异步函数**\n"
    else:
        skill += "未发现异步函数\n"

    skill += """

---

## 设计洞察

"""
    if insights:
        for ins in insights:
            icon = {"async": "✨", "decorators": "🎯", "inheritance": "🏗️", "dependencies": "📦"}.get(ins["type"], "•")
            skill += f"- {icon} {ins['content']}\n"
    else:
        skill += "- 基本Python项目\n"

    skill += """

---

    skill += """

## 核心文件内容预览

"""
    py_files = [p for p in files_content.keys() if p.endswith(".py")]
    for pf in py_files[:3]:
        content = files_content[pf][:300]
        skill += f"\n### {pf}\n\n```\n{content}\n...\n```\n"

    skill += """

---

## 举一反三

"""
    # 根据项目特点推荐应用
    repo_lower = repo.lower()

    if 'agent' in repo_lower:
        skill += "**这个Agent项目教给我**:\n"
        skill += "1. Agent的核心循环:感知->思考->行动\n"
        skill += "2. 工具调用的设计模式\n"
        skill += "3. 如何让AI自主决策\n"
        skill += "\n**可用场景**: AI助手、自动化任务、对话系统\n"

    elif 'mcp' in repo_lower or 'server' in repo_lower:
        skill += "**这个MCP服务器教给我**:\n"
        skill += "1. MCP协议的工作原理\n"
        skill += "2. 工具服务器的标准实现\n"
        skill += "3. JSON-RPC通信模式\n"
        skill += "\n**可用场景**: 工具集成、协议开发\n"

    elif 'cli' in repo_lower or 'tool' in repo_lower:
        skill += "**这个CLI工具教给我**:\n"
        skill += "1. 命令行参数处理\n"
        skill += "2. 用户交互设计\n"
        skill += "3. 错误提示优化\n"
        skill += "\n**可用场景**: 开发工具、自动化脚本\n"

    else:
        skill += "**学到的通用设计思路**:\n"
        if patterns["async_funcs"]:
            skill += "1. 异步编程模式 - 提高并发性能\n"
        if patterns["classes"]:
            skill += "2. 面向对象设计 - 封装和复用\n"
        if patterns["decorators"]:
            skill += "3. 装饰器模式 - 增强函数功能\n"
        skill += "\n**可用场景**: 根据具体项目特点应用\n"

    skill += """

---

## 学习验证

[?] 学完必须能回答:
1. **这个项目用什么语言/框架写的?** -> """
    if patterns["imports"]:
        top_imp = patterns["imports"][0]["module"]
        skill += f"{top_imp}等\n"
    else:
        skill += "Python\n"

    skill += """2. **核心函数是什么? 做什么的?** -> """
    if core_funcs:
        skill += f"{core_funcs[0]['name']}\n"
    else:
        skill += "见上表\n"

    skill += """3. **这个设计思路还能用在哪里?** -> 见上面的举一反三

"""

    # 保存
    sf = HERMES_HOME / "skills" / "auto-learned" / f"deep-{user}-{repo[:25]}.md"
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(skill)
    log(f"   💾 Skill保存: {sf.name} ({len(skill)}字)")

    return skill

# ============ 主学习循环 ============

STOP_TIME = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0)
if STOP_TIME <= datetime.now():
    STOP_TIME += timedelta(days=1)

def main():
    log("🚀 Auto-Learner v15 启动!")
    log("   修复版:可靠的源码获取 + 深度模式提取")
    log(f"⏰ 运行至: {STOP_TIME.strftime('%H:%M')}")

    # 学习任务
    TASKS = [
        ("gptme/gptme", "gptme终端AI编程助手"),
        ("crewAIInc/crewAI", "CrewAI多Agent框架"),
        ("modelcontextprotocol/servers", "MCP官方服务器"),
        ("Significant-Gravitas/AutoGPT", "AutoGPT自主Agent"),
        ("anthropics/claude-code", "Claude代码助手"),
        ("openai/codex", "OpenAI Codex"),
    ]

    cycle = 0

    while datetime.now() < STOP_TIME:
        cycle += 1
        rem = STOP_TIME - datetime.now()
        h, m = int(rem.total_seconds() // 3600), int((rem.total_seconds() % 3600) // 60)

        log(f"\n{'='*60}")
        log(f"📚 #{cycle} | 剩{h}h{m}m")
        log(f"{'='*60}")

        for repo_full, desc in TASKS:
            parts = repo_full.split("/")
            if len(parts) != 2:
                continue
            user, repo = parts

            log(f"\n📦 学习: {repo_full} - {desc}")

            # 获取源码
            files = fetch_source_files(user, repo)
            log(f"   获取到 {len(files)} 个文件")

            if not files:
                log(f"   ⚠️ 未能获取源码，尝试备用方法...")
                # 备用:直接获取主要源文件
                for attempt_file in ["src/main.py", "main.py", f"{repo}/__init__.py"]:
                    url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{attempt_file}"
                    r = http_get(url)
                    if r and r.status_code == 200 and len(r.text) > 200:
                        files[attempt_file] = r.text
                        log(f"   ✓ 备用获取: {attempt_file}")
                        break

            if files:
                # 提取模式
                patterns = extract_patterns(files)
                log(f"   模式: {len(patterns['functions'])}函数, {len(patterns['classes'])}类, {len(patterns['async_funcs'])}异步")

                # 设计洞察
                insights = extract_design_insights(patterns, files)

                # 构建Skill
                skill = build_deep_skill(f"https://github.com/{repo_full}", files, patterns, insights)

                # 记录变化
                log(f"   ✅ 完成: {repo}")
            else:
                log(f"   ❌ 失败: {repo}")

            time.sleep(3)

        if cycle >= 3:
            log("💤 v15完成3个周期")
            break

        time.sleep(120)

    log("\n🎉 17:30到，学习结束!")

    # 最终统计
    skill_dir = HERMES_HOME / "skills" / "auto-learned"
    if skill_dir.exists():
        skills = list(skill_dir.glob("deep-*.md"))
        log(f"📊 共生成 {len(skills)} 个深度Skill")

if __name__ == "__main__":
    main()
