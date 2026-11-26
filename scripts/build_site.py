# 构建 public-reading 静态站点：读取 tab-thursday/、handbook/ 与 resource-grocery/zyscj/ 的 Markdown，输出到 docs/。
# 用法：python scripts/build_site.py
# 依赖：Python-Markdown（python -m pip install markdown）

from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
LINKS_FILE = ROOT / "links.json"

REPO_URL = "https://github.com/73mtq/public-reading"
SITE_URL = "https://73mtq.github.io/public-reading/"
BLOB = REPO_URL + "/blob/main/"

ISSUES = [
    {
        "key": "001",
        "src": "tab-thursday/第一期-18位分享者内容精读.md",
        "label": "第一期",
        "date": "2026-10-29",
        "place": "706 上海（迎龙大厦）",
        "count": "18 位分享者",
        "theme": "一个人能做出什么东西",
        "title": "第一期 · 18 位分享者内容精读",
        "desc": "3D 场景、浏览器、播客集邮册、像素宠物、Kindle 插件、独立游戏——18 个互不相干的方向，收敛出 5 条可操作的判断。",
        "bullets": [
            "先盘活存量，再考虑新增",
            "「可编辑」比「能生成」值钱",
            "合规与授权成为技术方案的一部分",
            "护城河是细节密度，不是功能数量",
            "瓶颈从执行转移到判断",
        ],
    },
    {
        "key": "002",
        "src": "tab-thursday/第二期-21位分享者内容精读.md",
        "label": "第二期",
        "date": "2026-11-05",
        "place": "上海幸福里",
        "count": "21 位分享者 + 线上补充",
        "theme": "怎么组织工作、怎么决定看什么",
        "title": "第二期 · 21 位分享者内容精读",
        "desc": "从「做得出」转向「怎么组织工作、怎么决定看什么」：Agent 的任务化、筛选权回流、被 AI 选中、判断的结构化。含与第一期判断的逐条对照和更严格的事实核查。",
        "bullets": [
            "组织单位从会话 / 产品变成任务 / skill / MCP",
            "筛选权回流个人，同时争取被 AI 选中",
            "把隐性判断写成显式结构",
            "把最终决定权留在人这一侧",
            "门槛从实现侧移到评估侧",
        ],
    },
    {
        "key": "003",
        "src": "tab-thursday/第三期-22位分享者内容精读.md",
        "label": "第三期",
        "date": "2026-11-12",
        "place": "上海幸福里",
        "count": "22 位分享者",
        "theme": "把信息入口、交付形式与本地工具重新组织",
        "title": "第三期 · 22 位分享者内容精读",
        "desc": "ChatGPT Live 陪玩、mymind、MarkText、RSSWise、Pebble、Dispatch、Trancy、Starland、tldraw office、hmod、Chatlog、Shapr3D、力生物学——22 个方向收敛出 5 条判断，并补上与前两期的重复分享者对照。",
        "bullets": [
            "信息入口先过机器：AI 先读、先判断",
            "苦劳与价值分离，交付形式决定内容的位置",
            "一个人的项目靠边界与规则维持",
            "老设备、旧文档与本地文件仍有再开发空间",
            "身体与注意力是自动化覆盖最慢的部分",
        ],
    },
    {
        "key": "004",
        "src": "tab-thursday/第四期-21位分享者内容精读.md",
        "label": "第四期",
        "date": "2026-11-19",
        "place": "上海幸福里",
        "count": "21 位分享者",
        "theme": "上下文、验证与门槛：AI 之下的新分工",
        "title": "第四期 · 21 位分享者内容精读",
        "desc": "Ulysses、Pinky、ARTEX、《精益创业》重读、开源掌机、iPhone 本地沙盒、AI 短片《该》、AirBuild、TOI-7930、NX2Apple、WatchWithU、VoHive、Supernote——21 个方向收敛出 5 条判断，并与前三期逐条对照。",
        "bullets": [
            "上下文正在变成可以托管、复用与共享的资产",
            "一次证伪比十次证明更省成本",
            "门槛移到上架、被看见与被信任",
            "设备与本地环境重新提供差异",
            "智能可以租用，记忆与判断需要自己持有",
        ],
    },
]

GUIDES = [
    {
        "key": "starter",
        "src": "handbook/起步路线.md",
        "label": "起步路线",
        "title": "起步路线 · 研究生第一学期怎么排",
        "desc": "把账号、第一篇论文、第一次汇报与十个项目排进 20 周，每一步都带判据。",
        "stamp": "2026-09-28",
    },
    {
        "key": "free-resources",
        "src": "handbook/免费资源清单.md",
        "label": "免费资源清单",
        "title": "免费资源与算力清单",
        "desc": "算力、学生认证、数据集、标注工具、模型平台、作品集托管与学生权益，每条额度都带来源等级与复核日期。",
        "stamp": "2026-09-28",
    },
    {
        "key": "projects",
        "src": "handbook/实战项目路线.md",
        "label": "实战项目路线",
        "title": "实战项目路线 · 从零基础到能碰论文",
        "desc": "十个项目分三档，从 MNIST 到论文复现，每个项目给出数据集、完成判据与容易出错的地方。",
        "stamp": "2026-09-28",
    },
    {
        "key": "paper-reading",
        "src": "handbook/论文精读方法.md",
        "label": "论文精读方法",
        "title": "论文精读方法 · 三遍阅读与组会汇报",
        "desc": "三遍阅读法、CV 经典论文地图、精读笔记模板、组会汇报结构与文献调研五步法。",
        "stamp": "2026-09-27",
    },
    {
        "key": "ai-boundaries",
        "src": "handbook/AI-使用边界.md",
        "label": "AI 使用边界",
        "title": "AI 使用边界 · 哪些环节可以交出去",
        "desc": "认知负债的实验证据、国内高校的 AI 规范盘点、红黄绿灯清单与依赖预警自查表。",
        "stamp": "2026-09-27",
    },
]

TEMPLATES = [
    {
        "key": "notes",
        "src": "handbook/templates/论文精读笔记模板.md",
        "label": "精读笔记模板",
        "title": "论文精读笔记模板 · 三遍阅读的记录表",
        "desc": "按三遍阅读的顺序列出要填的栏目，复制一份就能逐篇填写。",
        "stamp": "2026-09-27",
    },
    {
        "key": "disclosure",
        "src": "handbook/templates/AI使用披露清单模板.md",
        "label": "AI 披露清单模板",
        "title": "AI 使用披露清单模板 · 逐次记录",
        "desc": "逐条记录工具、环节、生成内容位置与校验方式，供课程与答辩查验。",
        "stamp": "2026-09-27",
    },
]

STAMP = "2026-11-26"
NEXT_EVENT = {
    "label": "#005",
    "date": "2026-11-26",
    "time": "19:00–21:30",
    "place": "上海·长宁幸福里",
    "url": "https://luma.com/pmb99b5m",
}
NAME_ALIASES = {
    "yytyyf": "杨云童",
    "草原张": "草原张（Naren）",
    "LingXinxia": "Xinxia Ling",
}
SRC_TO_PAGE = {Path(issue["src"]).name: "./issue-%s.html" % issue["key"] for issue in ISSUES}
GUIDE_TO_PAGE = {Path(guide["src"]).name: "./guide-%s.html" % guide["key"] for guide in GUIDES}
TEMPLATE_TO_PAGE = {
    "templates/" + Path(template["src"]).name: "./template-%s.html" % template["key"]
    for template in TEMPLATES
}
HREF_MAP = {"./" + name: page for name, page in SRC_TO_PAGE.items()}
HREF_MAP.update({"./" + name: page for name, page in GUIDE_TO_PAGE.items()})
HREF_MAP.update({"./" + name: page for name, page in TEMPLATE_TO_PAGE.items()})
HREF_MAP.update({"../" + name: page for name, page in GUIDE_TO_PAGE.items()})

RESOURCE_DIR = ROOT / "resource-grocery" / "zyscj"
RESOURCE_DOC_ROOT = RESOURCE_DIR / "docs"
RESOURCE_DOCS = sorted(RESOURCE_DOC_ROOT.rglob("*.md"))


def sanitize_body(body: str) -> str:
    """Drop links that cannot work on the site: bookmarklets, odd schemes, dead in-page anchors."""
    ids = set(re.findall(r'id="([^"]+)"', body))

    def repl(match: "re.Match[str]") -> str:
        attrs, text = match.group(1), match.group(2)
        href_match = re.search(r'href="([^"]*)"', attrs)
        if not href_match:
            return match.group(0)
        href = href_match.group(1)
        if re.match(r"^(javascript|whimsical|data|vbscript|about|ftp):", href, flags=re.I):
            return text
        if href.startswith("#") and href[1:] not in ids:
            return text
        return match.group(0)

    return re.sub(r"<a\b([^>]*)>(.*?)</a>", repl, body, flags=re.S)


def strip_self_anchors(text: str) -> str:
    """Drop in-page anchor links kept from the source site; the sidebar replaces them."""
    return re.sub(r"\[([^\]]+)\]\(#[^)]*\)", r"\1", text)


def resource_slug(path: Path) -> str:
    rel = path.relative_to(RESOURCE_DOC_ROOT).with_suffix("")
    return "zyscj-doc-" + "-".join(rel.parts)


RESOURCE_SLUGS = {path: resource_slug(path) for path in RESOURCE_DOCS}
HREF_MAP.update({"LINKS.md": "./zyscj-links.html", "INDEX.md": "./zyscj.html"})
HREF_MAP.update(
    {
        "docs/" + path.relative_to(RESOURCE_DOC_ROOT).as_posix(): "./%s.html" % slug
        for path, slug in RESOURCE_SLUGS.items()
    }
)


def resource_heading(path: Path) -> str:
    """取页面的一级标题，用作分组标题与面包屑文字。"""
    match = re.search(r"^#\s+(.+?)\s*$", path.read_text(encoding="utf-8"), flags=re.M)
    return match.group(1) if match else path.stem


def resource_link_count(path: Path) -> int:
    """页面开头的抓取信息里记着外链数；取不到时按正文里的链接统计。"""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"外链\s*(\d+)\s*个", text)
    return int(match.group(1)) if match else len(re.findall(r"\]\(https?://", text))


def resource_parent(path: Path) -> "Path | None":
    """上一级页面：同目录的 index.md，没有就逐级向上找。"""
    rel = path.relative_to(RESOURCE_DOC_ROOT)
    if rel.name == "index.md":
        if rel.parent == Path("."):
            return None
        current = rel.parent.parent
    else:
        current = rel.parent
    while True:
        candidate = RESOURCE_DOC_ROOT / current / "index.md"
        if candidate.exists() and candidate != path:
            return candidate
        if current == Path("."):
            return None
        current = current.parent


def resource_breadcrumb(path: Path) -> str:
    chain = []
    parent = resource_parent(path)
    while parent is not None:
        chain.append(parent)
        parent = resource_parent(parent)
    steps = ['<a href="./zyscj-all.html">全部资源页</a>']
    for node in reversed(chain):
        steps.append(
            '<a href="./%s.html">%s</a>'
            % (RESOURCE_SLUGS[node], html.escape(resource_heading(node)))
        )
    steps.append(html.escape(resource_heading(path)))
    return '<nav class="breadcrumb" aria-label="所在位置">%s</nav>' % " <span>›</span> ".join(steps)


def resource_entry_sidebar_html(active: str) -> str:
    """资源索引三个入口页的侧栏：列出另外两个入口与资源站首页。"""
    entries = [
        ("zyscj", "需求速查"),
        ("zyscj-all", "全部 %d 页" % len(RESOURCE_SLUGS)),
        ("zyscj-links", "外链总表"),
    ]
    rows = ['      <div class="sidebar-sub">资源索引</div>']
    for key, label in entries:
        if key == active:
            continue
        rows.append('      <a class="sidebar-guide" href="./%s.html">%s</a>' % (key, label))
    rows.append('      <a class="sidebar-guide" href="./zyscj-doc-index.html">资源站首页</a>')
    return "\n".join(rows)


def resource_doc_sidebar_html(path: Path) -> str:
    rows = [
        '      <div class="sidebar-sub">资源索引</div>',
        '      <a class="sidebar-guide" href="./zyscj-all.html">全部 %d 页</a>' % len(RESOURCE_SLUGS),
    ]
    parent = resource_parent(path)
    if parent is not None:
        rows.append(
            '      <a class="sidebar-guide" href="./%s.html">↑ %s</a>'
            % (RESOURCE_SLUGS[parent], html.escape(resource_heading(parent)))
        )
    rows.append('      <a class="sidebar-guide" href="./zyscj.html">需求速查</a>')
    return "\n".join(rows)


def resource_groups() -> list:
    """按目录把资源页分组，组内章节索引排在最前。"""
    groups: dict = {}
    for path in RESOURCE_DOCS:
        groups.setdefault(path.parent, []).append(path)
    ordered = []
    for parent in sorted(groups, key=lambda p: p.relative_to(RESOURCE_DOC_ROOT).as_posix().lower()):
        pages = sorted(groups[parent], key=lambda p: (p.name != "index.md", p.name.lower()))
        ordered.append((parent, pages))
    return ordered


def resource_all_markdown() -> str:
    lines = ["# 全部资源页", ""]
    lines.append(
        "资源站的 %d 个页面全在这里，按目录分组；标题取自各页一级标题，末尾的数字是该页抓取时收录的外链数。"
        % len(RESOURCE_DOCS)
    )
    lines.append("")
    lines.append(
        "按用途查找用 [需求速查](./zyscj.html)，要看每页的链接明细用 [外链总表](./zyscj-links.html)。"
    )
    lines.append("")
    for parent, pages in resource_groups():
        relative = parent.relative_to(RESOURCE_DOC_ROOT).as_posix()
        index_page = next((page for page in pages if page.name == "index.md"), None)
        if relative == ".":
            title = "资源站首页"
        elif relative == "zy":
            title = "总索引"
        elif index_page is not None:
            title = resource_heading(index_page)
        else:
            title = parent.name
        lines.append("## %s" % title)
        lines.append("")
        for page in pages:
            marker = "章节索引 · " if page.name == "index.md" else ""
            lines.append(
                "- [%s](./%s.html) — %s外链 %d 个"
                % (
                    resource_heading(page),
                    RESOURCE_SLUGS[page],
                    marker,
                    resource_link_count(page),
                )
            )
        lines.append("")
    return "\n".join(lines)


CN_NUM = {1: "一", 2: "两", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}

CSS = r"""
:root{
  --bg:#faf9f6;--surface:#ffffff;--ink:#2c2c2a;--muted:#5f5e5a;--faint:#888780;
  --line:#e5e3dd;--line2:#d3d1c7;--blue:#185fa5;--blue50:#e6f1fb;--blue100:#b5d4f4;
  --teal:#0f6e56;--teal50:#e1f5ee;--radius:12px;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.8;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
button,input{font-family:inherit}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--blue);z-index:100;transition:width .08s linear}
.topbar{position:sticky;top:0;z-index:60;height:58px;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;padding:0 28px;backdrop-filter:saturate(1.4) blur(6px)}
.brand{font-weight:500;font-size:15px;color:var(--ink);white-space:nowrap}
.brand:hover{text-decoration:none;color:var(--blue)}
.topbar nav{display:flex;gap:20px;align-items:center;flex:1;flex-wrap:wrap}
.topbar nav a{font-size:13.5px;color:var(--muted)}
.topbar nav a.active{color:var(--blue);font-weight:500}
.menu-toggle{display:none;border:1px solid var(--line2);background:var(--surface);color:var(--ink);border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}

.layout{max-width:1300px;margin:0 auto;padding:32px 24px 80px;display:grid;grid-template-columns:272px minmax(0,1fr);gap:36px;align-items:start}
.sidebar{position:sticky;top:82px;max-height:calc(100vh - 106px);overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:18px 14px}
.sidebar-head{padding:0 6px 12px;border-bottom:1px solid var(--line);margin-bottom:10px}
.sidebar-title{font-size:13px;font-weight:500;color:var(--ink);margin-bottom:10px}
.filter{width:100%;border:1px solid var(--line2);border-radius:8px;padding:7px 10px;font-size:12.5px;color:var(--ink);background:var(--bg);outline:none}
.filter:focus{border-color:var(--blue);background:var(--surface)}
.filter-hint{font-size:11.5px;color:var(--faint);margin-top:7px}
.toc{display:flex;flex-direction:column;gap:1px}
.toc a{display:block;border-radius:6px;padding:6px 9px;font-size:12.8px;line-height:1.5;color:var(--muted);border-left:2px solid transparent}
.toc a:hover{background:var(--bg);text-decoration:none;color:var(--blue)}
.toc a.active{background:var(--blue50);color:var(--blue);border-left-color:var(--blue)}
.toc .toc-group{font-weight:500;color:var(--ink);margin-top:14px;font-size:12.5px;background:transparent}
.toc .toc-group:first-child{margin-top:0}
.toc .toc-item{padding-left:18px}
.sidebar-foot{margin-top:14px;padding:12px 6px 0;border-top:1px solid var(--line);font-size:12px;display:flex;flex-direction:column;gap:6px}
.sidebar-foot a{color:var(--muted)}

.content{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:46px 56px 64px;min-width:0}
.prose{font-size:15.5px;line-height:1.92;color:var(--ink)}
.prose>h1:first-child,.prose>.breadcrumb+h1{font-size:29px;line-height:1.45;margin:0 0 1.1em;font-weight:500;letter-spacing:.01em}
.breadcrumb{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:0 0 18px;font-size:12.5px;line-height:1.7;color:var(--faint)}
.breadcrumb a{color:var(--muted)}
.breadcrumb a:hover{color:var(--blue)}
.breadcrumb span{color:var(--line2)}
.prose h1{font-size:24px;line-height:1.5;margin:2.6em 0 .9em;padding:0 0 .45em;border-bottom:2px solid var(--line);font-weight:500;scroll-margin-top:84px}
.prose h2{font-size:20px;line-height:1.5;margin:2.3em 0 .8em;padding-left:12px;border-left:3px solid var(--blue);font-weight:500;scroll-margin-top:84px}
.prose h3{font-size:16.5px;line-height:1.6;margin:1.8em 0 .6em;color:var(--muted);font-weight:500;scroll-margin-top:84px}
.prose p{margin:.9em 0}
.prose strong{font-weight:500;color:#1b1b19}
.prose ul,.prose ol{padding-left:1.7em;margin:.9em 0}
.prose li{margin:.35em 0}
.prose li::marker{color:var(--blue)}
.prose blockquote{margin:1.3em 0;padding:12px 18px;background:#f5f9fd;border-left:3px solid var(--blue100);border-radius:0 8px 8px 0;color:var(--muted);font-size:14.5px}
.prose blockquote p{margin:.35em 0}
.prose hr{border:0;border-top:1px solid var(--line);margin:2.6em 0}
.prose code{background:#f1efe8;border-radius:4px;padding:2px 5px;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;word-break:break-word}
.prose pre{background:#f7f6f2;border:1px solid var(--line);border-radius:8px;padding:14px 16px;overflow-x:auto}
.prose pre code{background:none;padding:0}
.prose table{border-collapse:collapse;width:100%;margin:1.3em 0;font-size:13.8px;display:block;overflow-x:auto;white-space:nowrap}
.prose table th,.prose table td{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top;white-space:normal;min-width:90px}
.prose table th{background:#f4f2ec;font-weight:500;color:var(--ink)}
.prose table tr:nth-child(even) td{background:#fcfbf8}
.prose a[target="_blank"]::after{content:" \2197";font-size:.78em;color:var(--faint);white-space:nowrap}
.prose img{max-width:100%;height:auto;border-radius:8px}
.article-foot{margin-top:52px;padding-top:22px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:13.5px;color:var(--muted)}
.foot-issues{display:flex;gap:18px;flex-wrap:wrap}
.to-top{position:fixed;right:26px;bottom:26px;width:40px;height:40px;border-radius:50%;border:1px solid var(--line2);background:var(--surface);color:var(--blue);font-size:18px;cursor:pointer;opacity:0;pointer-events:none;transition:opacity .18s;z-index:55}
.to-top.show{opacity:1;pointer-events:auto}
.to-top:hover{background:var(--blue50)}

.home{max-width:1080px;margin:0 auto;padding:64px 24px 90px}
.hero{margin-bottom:44px}
.hero .kicker{display:inline-block;font-size:12.5px;color:var(--teal);background:var(--teal50);border-radius:20px;padding:4px 12px;margin-bottom:18px}
.hero h1{font-size:34px;line-height:1.4;font-weight:500;margin:0 0 14px;letter-spacing:.01em}
.hero p{font-size:15.5px;color:var(--muted);max-width:720px;margin:0 0 20px}
.hero-links{display:flex;gap:18px;flex-wrap:wrap;font-size:13.5px}
.section-title{font-size:19px;font-weight:500;margin:44px 0 18px}
.issue-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.issue-card{display:block;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:28px 28px 26px;color:var(--ink);transition:border-color .16s,transform .16s}
.issue-card:hover{border-color:var(--blue);transform:translateY(-2px);text-decoration:none}
.issue-card.featured{border-color:#c6ddf2;background:linear-gradient(0deg,#fff,#fbfdff)}
.issue-no{font-size:12.5px;color:var(--blue);font-weight:500;letter-spacing:.08em}
.issue-card h2{font-size:21px;font-weight:500;margin:8px 0 6px}
.issue-meta{font-size:13px;color:var(--faint);margin-bottom:14px}
.issue-theme{font-size:14.5px;color:var(--ink);margin:0 0 16px}
.issue-card ul{margin:0 0 20px;padding-left:1.25em;font-size:13px;color:var(--muted)}
.issue-card li{margin:3px 0}
.cta{display:inline-block;font-size:13.5px;color:var(--blue);font-weight:500}
.quick-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.quick-grid a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:9px;padding:13px 15px;font-size:13.5px;color:var(--ink)}
.quick-grid a:hover{border-color:var(--blue);color:var(--blue);text-decoration:none}
.quick-grid a small{display:block;color:var(--faint);font-size:11.5px;margin-top:3px}
.people-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:9px}
.people-grid a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:13px;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.people-grid a:hover{border-color:var(--teal);background:var(--teal50);color:var(--teal);text-decoration:none}
.people-grid a b{color:var(--blue);font-weight:500;margin-right:6px}
.site-foot{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);font-size:12.8px;color:var(--faint);display:flex;gap:18px;flex-wrap:wrap}
.notice{background:var(--blue50);border:1px solid #cfe3f7;border-radius:9px;padding:13px 16px;font-size:13.3px;color:#0c447c;margin-bottom:26px}

@media (max-width:960px){
  .layout{grid-template-columns:1fr;padding:20px 16px 70px}
  .content{padding:30px 22px 46px}
  .topbar{padding:0 16px;gap:12px}
  .topbar nav{gap:14px}
  .topbar nav a{font-size:12.5px}
  .menu-toggle{display:block}
  .sidebar{position:fixed;top:58px;left:0;bottom:0;width:min(310px,86vw);max-height:none;border-radius:0;border-left:0;border-top:0;z-index:59;transform:translateX(-102%);transition:transform .2s;box-shadow:8px 0 24px rgba(0,0,0,.06)}
  .sidebar.open{transform:translateX(0)}
  .prose{font-size:15px}
  .prose>h1:first-child{font-size:24px}
  .hero{padding-top:8px}
  .hero h1{font-size:27px}
  .issue-grid{grid-template-columns:1fr}
  .to-top{right:16px;bottom:16px}
}
@media (max-width:760px){
  .topbar nav a.nav-old{display:none}
}
@media (max-width:560px){
  .topbar nav a.nav-official,.topbar nav a.nav-repo{display:none}
  .content{padding:24px 16px 40px}
  .prose table{font-size:12.8px}
}
.people-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}
.person-card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 17px;display:flex;flex-direction:column}
.person-head{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}
.person-name{font-size:14.5px;font-weight:500;color:var(--ink)}
.person-name:hover{color:var(--blue);text-decoration:none}
.person-num{color:var(--blue);font-size:12px}
.person-topic{font-size:12px;color:var(--faint);margin:0 0 11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{display:inline-block;font-size:12.2px;line-height:1.5;padding:4px 9px;border:1px solid var(--line2);border-radius:20px;color:var(--muted);background:var(--bg);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle}
.chip:hover{border-color:var(--blue);color:var(--blue);text-decoration:none;background:var(--blue50)}
.chip.home{border-color:#b5d4f4;color:#0c447c;background:var(--blue50)}
.chip::after{content:" \2197";font-size:.8em;color:var(--faint)}
.no-links{font-size:12px;color:var(--faint)}
.read-link{display:inline-block;margin-top:11px;font-size:12.3px;align-self:flex-start}
.index-note{font-size:13px;color:var(--muted);margin:-6px 0 16px}
.inline-links{margin:14px 0 20px;padding:11px 13px;background:#fafbfd;border:1px solid var(--line);border-radius:9px;display:flex;flex-wrap:wrap;align-items:center;gap:7px}
.inline-label{font-size:11.8px;color:var(--faint);margin-right:4px}
.issue-sub{font-size:14px;color:var(--muted);margin:26px 0 12px;font-weight:500}

/* Refinement: quiet archive reader — mobile shell, legibility, a11y */
:root{
  --topbar-h:58px;
  --faint:#6f6e68;
  --focus:#185fa5;
  --shadow-md:0 8px 28px rgba(44,44,42,.12);
  --ease-out:cubic-bezier(.22,.61,.36,1);
  --ease-in:cubic-bezier(.55,.06,.68,.19);
}
html{scroll-padding-top:84px}
::selection{background:#cfe3f7;color:#0c447c}
a,button,input{-webkit-tap-highlight-color:transparent}
:focus-visible{outline:2px solid var(--focus);outline-offset:3px;border-radius:4px}
.prose h1,.prose h2,.hero h1,.issue-card h2,.section-title{text-wrap:balance}
.person-num,.issue-no,.issue-meta,.site-foot{font-variant-numeric:tabular-nums}
.prose table{scrollbar-width:thin;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}
.table-wrap{position:relative;margin:1.3em 0}
.table-wrap table{margin:0}
.table-hint{display:none}
.issue-card.featured{background:#fbfdff;border-color:#c6ddf2;border-left:3px solid var(--blue)}
section#tab-thursday,section#handbook{scroll-margin-top:84px}
.section-title.sub{font-size:15.5px;color:var(--muted);margin:34px 0 14px}
.official-row{margin-top:20px}
.guide-card h2{font-size:19px}
.guide-card .issue-meta{margin-bottom:10px}
.sidebar-sub{font-size:11.5px;color:var(--faint);margin:8px 0 2px}
.sidebar-guide{font-weight:500}
.section-title{display:flex;align-items:center;gap:12px}
.section-title::after{content:"";flex:1;height:1px;background:var(--line)}
.chip,.quick-grid a,.toc a,.topbar nav a,.to-top,.menu-toggle,.toc-fab,.drawer-close{transition:background-color 150ms var(--ease-out),color 150ms var(--ease-out),border-color 150ms var(--ease-out),transform 80ms var(--ease-out)}
.chip:active,.quick-grid a:active,.issue-card:active,.to-top:active,.menu-toggle:active,.toc-fab:active{transform:scale(.98)}
.toc a.active{box-shadow:inset 2px 0 0 var(--blue)}
.scrim{display:none}
.toc-fab,.drawer-close{display:none}
.toc-fab-icon{display:flex;flex-direction:column;justify-content:space-between;width:16px;height:12px;flex:none}
.toc-fab-icon i{display:block;height:1.5px;background:currentColor;border-radius:1px}

@media (max-width:960px){
  html{scroll-padding-top:calc(var(--topbar-h) + env(safe-area-inset-top) + 12px)}
  .topbar{height:calc(var(--topbar-h) + env(safe-area-inset-top));padding-top:env(safe-area-inset-top);padding-left:16px;padding-right:16px;gap:12px}
  .topbar nav{gap:16px}
  .topbar nav a{font-size:13px;min-height:44px;display:inline-flex;align-items:center}
  .topbar nav a.nav-old{display:none}
  .menu-toggle{display:none}
  .layout{display:block;padding:0 0 calc(72px + env(safe-area-inset-bottom))}
  .content{border:0;border-radius:0;padding:24px 18px 44px;box-shadow:none}
  .prose{font-size:16.5px;line-height:1.85}
  .prose>h1:first-child{font-size:25px;line-height:1.4}
  .prose h1{font-size:21px;margin-top:2.2em}
  .prose h2{font-size:18.5px;margin-top:2em;padding-left:10px}
  .prose h3{font-size:16px}
  .prose blockquote{padding:12px 14px;font-size:14px}
  .prose table{font-size:13.5px}
  .prose ul,.prose ol{padding-left:1.4em}
  .table-hint{display:block;font-size:11.5px;color:var(--faint);margin-top:6px;text-align:right}
  .sidebar{top:calc(var(--topbar-h) + env(safe-area-inset-top));bottom:0;width:min(320px,88vw);border-radius:0 14px 14px 0;border-left:0;border-top:0;z-index:59;padding-bottom:calc(18px + env(safe-area-inset-bottom));transform:translate3d(-102%,0,0);transition:transform 260ms var(--ease-out);will-change:transform;box-shadow:var(--shadow-md)}
  .sidebar.open{transform:translate3d(0,0,0)}
  .scrim{display:block;position:fixed;inset:0;background:rgba(28,27,25,.42);opacity:0;pointer-events:none;transition:opacity 200ms var(--ease-in);z-index:58}
  .scrim.show{opacity:1;pointer-events:auto}
  body.nav-open{overflow:hidden}
  .sidebar-head{position:relative;padding-right:44px}
  .drawer-close{display:inline-flex;align-items:center;justify-content:center;position:absolute;top:8px;right:8px;width:44px;height:44px;border:0;background:transparent;color:var(--muted);font-size:22px;line-height:1;cursor:pointer;border-radius:8px}
  .toc a{min-height:44px;display:flex;align-items:center;font-size:13.5px;padding:8px 10px}
  .toc .toc-item{padding-left:18px}
  .filter{font-size:16px;min-height:44px}
  .toc-fab{display:inline-flex;align-items:center;gap:9px;position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:57;min-height:48px;padding:0 18px;border:1px solid var(--line2);border-radius:24px;background:var(--surface);color:var(--ink);font-size:13.5px;box-shadow:var(--shadow-md);cursor:pointer}
  .to-top{right:16px;bottom:calc(80px + env(safe-area-inset-bottom));width:44px;height:44px}
  .issue-card:hover{transform:none}
  .home{padding:36px 18px calc(80px + env(safe-area-inset-bottom))}
  .hero h1{font-size:26px}
  .hero-links{gap:12px 18px}
  .issue-grid{grid-template-columns:1fr;gap:14px}
  .issue-card{padding:22px 20px}
  .people-cards{grid-template-columns:1fr;gap:10px}
  .person-card{padding:16px}
  .chip{min-height:36px;display:inline-flex;align-items:center;padding:6px 12px;font-size:12.8px}
  .quick-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  .quick-grid a{min-height:52px;padding:11px 12px;font-size:13px}
  .inline-links{padding:10px 11px;gap:7px}
  .read-link{min-height:36px;display:inline-flex;align-items:center}
}
@media (max-width:560px){
  .hero h1{font-size:24px}
  .prose{font-size:16px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}
}
@media (prefers-color-scheme:dark){
  :root{--bg:#1b1a18;--surface:#232220;--ink:#e9e6df;--muted:#b3afa6;--faint:#96928a;--line:#38352f;--line2:#4a4740;--blue:#7fb3e8;--blue50:#1d2c3c;--blue100:#2c4660;--teal:#63c2a5;--teal50:#17302a;--focus:#7fb3e8;--shadow-md:0 8px 28px rgba(0,0,0,.42)}
  body{background:var(--bg);color:var(--ink)}
  .topbar{background:rgba(27,26,24,.96)}
  .brand{color:var(--ink)}
  .prose strong{color:#f4f1ea}
  .prose blockquote{background:#1f2730;border-left-color:#3a5570}
  .prose code{background:#302e29}
  .prose pre,.prose pre code{background:#272521}
  .prose table th{background:#2b2925}
  .prose table tr:nth-child(even) td{background:#262420}
  .chip,.filter,.toc-fab,.to-top,.menu-toggle{background:#262420;color:var(--ink)}
  .chip.home{background:#1d2c3c;border-color:#3a5570;color:#b8d6f2}
  .inline-links{background:#20211f}
  .issue-card.featured{background:#1e2630;border-color:#3a5570;border-left-color:var(--blue)}
  .notice{background:#1d2c3c;border-color:#3a5570;color:#b8d6f2}
  .hero .kicker{color:var(--teal)}
  .toc a.active{background:#1d2c3c;color:var(--blue)}
  ::selection{background:#2c4660;color:#e9e6df}
}

@media print{
  .topbar,.sidebar,.to-top,#progress,.article-foot,.inline-links{display:none!important}
  .layout{display:block;padding:0}
  .content{border:0;padding:0}
  body{background:#fff}
}
"""

JS = r"""
(function(){
  var toc=document.getElementById('toc');
  var filter=document.getElementById('tocFilter');
  var progress=document.getElementById('progress');
  var toTop=document.getElementById('toTop');
  var toggle=document.getElementById('menuToggle');
  var fab=document.getElementById('tocFab');
  var scrim=document.getElementById('scrim');
  var drawerClose=document.getElementById('drawerClose');
  var sidebar=document.getElementById('sidebar');
  var triggers=[toggle,fab].filter(Boolean);
  var mobile=window.matchMedia('(max-width:960px)');

  function setDrawer(open,returnFocus){
    if(!sidebar)return;
    sidebar.classList.toggle('open',open);
    if(scrim)scrim.classList.toggle('show',open);
    document.body.classList.toggle('nav-open',open&&mobile.matches);
    for(var i=0;i<triggers.length;i++)triggers[i].setAttribute('aria-expanded',open?'true':'false');
    if(!open&&returnFocus&&mobile.matches&&fab)fab.focus({preventScroll:true});
  }
  for(var t=0;t<triggers.length;t++){
    triggers[t].addEventListener('click',function(){
      setDrawer(!sidebar.classList.contains('open'),true);
    });
  }
  if(scrim)scrim.addEventListener('click',function(){setDrawer(false,true);});
  if(drawerClose)drawerClose.addEventListener('click',function(){setDrawer(false,true);});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape')setDrawer(false,true);
  });
  if(toc)toc.addEventListener('click',function(e){
    if(e.target.closest('a'))setDrawer(false,false);
  });
  if(filter&&toc){
    filter.addEventListener('input',function(){
      var q=this.value.trim().toLowerCase();
      var items=toc.querySelectorAll('.toc-item');
      for(var i=0;i<items.length;i++){
        items[i].hidden=!!q&&(items[i].dataset.title||'').toLowerCase().indexOf(q)<0;
      }
      var groups=toc.querySelectorAll('.toc-group'),cur=null,has={};
      var all=toc.querySelectorAll('a');
      for(var j=0;j<all.length;j++){
        var el=all[j];
        if(el.classList.contains('toc-group')){cur=el;has[el.getAttribute('href')]=false;}
        else if(cur&&!el.hidden){has[cur.getAttribute('href')]=true;}
      }
      for(var k=0;k<groups.length;k++){
        groups[k].hidden=!!q&&!has[groups[k].getAttribute('href')];
      }
    });
    document.addEventListener('keydown',function(e){
      if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();filter.focus();filter.select();}
    });
  }
  if(toTop)toTop.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});

  var heads=Array.prototype.slice.call(document.querySelectorAll('.prose h1[id],.prose h2[id]'));
  function update(){
    var d=document.documentElement;
    var max=d.scrollHeight-d.clientHeight;
    if(progress)progress.style.width=(max>0?(d.scrollTop/max*100):0)+'%';
    if(toTop)toTop.classList.toggle('show',d.scrollTop>420);
    if(!toc||!heads.length)return;
    var active=null;
    for(var i=0;i<heads.length;i++){
      if(heads[i].getBoundingClientRect().top<=110)active=heads[i].id;else break;
    }
    var links=toc.querySelectorAll('a');
    for(var j=0;j<links.length;j++){
      links[j].classList.toggle('active',!!active&&links[j].getAttribute('href')==='#'+active);
    }
  }
  window.addEventListener('scroll',update,{passive:true});
  window.addEventListener('resize',update);
  update();

  var tables=document.querySelectorAll('.prose table');
  for(var k=0;k<tables.length;k++){
    var table=tables[k];
    var wrap=document.createElement('div');
    wrap.className='table-wrap';
    table.parentNode.insertBefore(wrap,table);
    wrap.appendChild(table);
    var hint=document.createElement('span');
    hint.className='table-hint';
    hint.textContent='左右滑动查看完整表格 →';
    wrap.appendChild(hint);
  }
})();
"""

PAGE_TPL = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}} · 公开材料精读</title>
<meta name="description" content="{{DESC}}">
<link rel="stylesheet" href="./assets/style.css">
</head>
<body>
<div id="progress"></div>
<header class="topbar">
  <a class="brand" href="./index.html">公开材料精读</a>
  <nav>
    <a href="./index.html">首页</a>
{{NAV}}
  </nav>
  <button class="menu-toggle" id="menuToggle" type="button" aria-controls="sidebar" aria-expanded="false">目录</button>
</header>
<div class="scrim" id="scrim"></div>
<div class="layout">
  <aside class="sidebar" id="sidebar" aria-label="章节目录">
    <div class="sidebar-head">
      <button class="drawer-close" id="drawerClose" type="button" aria-label="关闭目录">×</button>
      <div class="sidebar-title">目录 · {{LABEL}}</div>
      <input class="filter" id="tocFilter" type="search" placeholder="筛选章节" autocomplete="off">
      <div class="filter-hint">Ctrl / ⌘ + K 快速定位</div>
    </div>
    <nav class="toc" id="toc">
{{TOC}}
    </nav>
    <div class="sidebar-foot">
      <a href="{{BLOB}}" target="_blank" rel="noopener noreferrer">Markdown 原文（GitHub）</a>
{{SIDEBAR_EXTRA}}
      <a href="./index.html">← 返回首页</a>
    </div>
  </aside>
  <main class="content">
    <article class="prose" id="article">
{{BODY}}
    </article>
    <div class="article-foot">
      <a href="./index.html">← 返回首页</a>
      <span class="foot-issues">{{PREV}}{{NEXT}}</span>
    </div>
  </main>
</div>
<button class="toc-fab" id="tocFab" type="button" aria-controls="sidebar" aria-expanded="false" aria-label="打开章节目录"><span class="toc-fab-icon" aria-hidden="true"><i></i><i></i><i></i></span><span>目录</span></button>
<button class="to-top" id="toTop" type="button" aria-label="返回顶部">↑</button>
<script src="./assets/app.js"></script>
</body>
</html>
"""

HOME_TPL = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公开材料精读 · 活动精读与学习手册</title>
<meta name="description" content="{{HOME_DESC}}">
<link rel="stylesheet" href="./assets/style.css">
</head>
<body>
<div id="progress"></div>
<header class="topbar">
  <a class="brand" href="./index.html">公开材料精读</a>
  <nav>
    <a href="./index.html" class="active">首页</a>
{{NAV}}
  </nav>
</header>
<main class="home">
  <section class="hero">
    <span class="kicker">活动分享 · 免费资源 · 读论文的方法</span>
    <h1>公开材料精读</h1>
    <p>{{HERO}}</p>
    <div class="hero-links">
      <a href="#tab-thursday">活动精读</a>
      <a href="#handbook">学习手册</a>
      <a href="{{REPO}}" target="_blank" rel="noopener noreferrer">仓库与 Markdown 原文</a>
    </div>
  </section>

  <div class="notice">{{NOTICE}}</div>

  <section id="tab-thursday">
    <h2 class="section-title">活动精读 · {{ISSUE_COUNT}}期</h2>
    <p class="index-note">{{ISSUE_NOTE}}</p>
    <section class="issue-grid">
{{CARDS}}
    </section>
    <div class="hero-links official-row">
{{OFFICIAL_LINKS}}
      <a href="https://tabthursday.com/about" target="_blank" rel="noopener noreferrer">活动规则</a>
    </div>
    <h3 class="section-title sub">{{LATEST_LABEL}} · 按主题跳转</h3>
    <section class="quick-grid">
{{QUICK}}
    </section>
  </section>

  <section id="handbook">
    <h2 class="section-title">学习手册 · {{GUIDE_COUNT}}</h2>
    <p class="index-note">{{GUIDE_NOTE}}</p>
    <section class="issue-grid guide-grid">
{{GUIDE_CARDS}}
    </section>
  </section>

  <section id="resources">
    <h2 class="section-title">资源索引 · {{RESOURCE_PAGE_COUNT}} 页</h2>
    <p class="index-note">{{RESOURCE_NOTE}}</p>
    <section class="issue-grid guide-grid">
{{RESOURCE_CARDS}}
    </section>
  </section>

  <h2 class="section-title">分享者与项目链接</h2>
  <p class="index-note">按官方汇总页整理：每位分享者的个人主页，以及他介绍的项目、源码、幻灯片等链接。点姓名进入本站精读章节，点标签跳转外部站点（新标签页打开）。没有主页或项目链接的会如实标注。</p>
{{INDEX_BLOCKS}}

  <div class="site-foot">
    <span>整理于 {{STAMP}} · 学习笔记性质的重述与分析，非官方记录</span>
    <a href="{{REPO}}" target="_blank" rel="noopener noreferrer">GitHub 仓库</a>
    <a href="https://tabthursday.com" target="_blank" rel="noopener noreferrer">活动官网</a>
  </div>
</main>
<button class="to-top" id="toTop" type="button" aria-label="返回顶部">↑</button>
<script src="./assets/app.js"></script>
</body>
</html>
"""


NOTFOUND_TPL = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>页面不存在 · 公开材料精读</title>
<style>
body{margin:0;background:#faf9f6;color:#2c2c2a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.8}
.wrap{max-width:620px;margin:0 auto;padding:90px 24px}
.code{font-size:64px;font-weight:500;line-height:1;margin:0 0 18px;color:#185fa5}
h1{font-size:21px;font-weight:500;margin:0 0 12px}
p{color:#5f5e5a;margin:0 0 14px}
.box{background:#e6f1fb;border:1px solid #cfe3f7;border-radius:10px;padding:14px 16px;margin:20px 0;color:#0c447c;font-size:13.5px}
code{background:#f1efe8;border-radius:4px;padding:2px 5px;font-size:.9em;word-break:break-all}
.links{display:flex;gap:14px;flex-wrap:wrap;margin-top:22px}
.links a{display:inline-block;border:1px solid #d3d1c7;background:#fff;border-radius:8px;padding:9px 15px;color:#185fa5;text-decoration:none;font-size:13.5px}
.links a:hover{border-color:#185fa5;background:#e6f1fb}
.hint{font-size:12.5px;color:#6f6e68;margin-top:26px}
@media (prefers-color-scheme:dark){
body{background:#1b1a18;color:#e9e6df}
.code{color:#7fb3e8}
p,.hint{color:#b3afa6}
.box{background:#1d2c3c;border-color:#3a5570;color:#b8d6f2}
code{background:#302e29}
.links a{background:#232220;border-color:#4a4740;color:#7fb3e8}
.links a:hover{background:#1d2c3c}
}
</style>
</head>
<body>
<div class="wrap">
  <div class="code">404</div>
  <h1>这个地址没有对应的页面</h1>
  <p id="msg">请检查地址是否完整，或从下面的入口重新进入。</p>
  <div class="box" id="tip" hidden>看起来地址末尾多复制了字符（例如 <code>**</code>）。正确地址是：<br><code>https://73mtq.github.io/public-reading/</code><br>正在自动跳转到首页…</div>
  <div class="links">
    <a href="./">返回首页</a>
{{NAV_LINKS}}
  </div>
  <div class="hint">公开材料精读 · GitHub Pages</div>
</div>
<script>
(function(){
  if(/\*/.test(location.pathname)){
    document.getElementById('tip').hidden=false;
    document.getElementById('msg').textContent='地址里包含了不属于路径的字符，站点本身正常。';
    setTimeout(function(){location.replace('./');},2600);
  }
})();
</script>
</body>
</html>
"""


def slugify(value: str, separator: str = "-") -> str:
    """Keep CJK characters in heading anchors (Python-Markdown strips them by default)."""
    value = re.sub(r"<[^>]+>", "", value)
    value = unicodedata.normalize("NFKC", value)
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", separator, value)
    return value.strip(separator)


AUTOLINK = re.compile(
    r"(?<![\w/@.+:-])"
    r"((?:https?://)?(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    r"(?:com|cn|org|net|io|ai|edu|co|me|dev|app|cc|tv|info|xyz|sh|so)"
    r"(?:\.[a-z]{2})?(?:/[\w./?=&%#+:~-]*)?)",
    re.I,
)
TAG_OR_TEXT = re.compile(r"<[^>]+>|[^<]+")
PROTECT_OPEN = ("<a ", "<a>", "<code", "<pre")
PROTECT_CLOSE = ("</a>", "</code>", "</pre>")


def autolink_html(body: str) -> str:
    """Turn bare domains and URLs in visible text into links."""
    out = []
    depth = 0
    for token in TAG_OR_TEXT.findall(body):
        if token.startswith("<"):
            low = token.lower()
            if low.startswith(PROTECT_OPEN):
                depth += 1
            elif low.startswith(PROTECT_CLOSE):
                depth = max(0, depth - 1)
            out.append(token)
            continue
        if depth:
            out.append(token)
            continue
        out.append(AUTOLINK.sub(link_token, token))
    return "".join(out)


def link_token(match: "re.Match[str]") -> str:
    text = match.group(1).rstrip(".,;:*")
    suffix = match.group(1)[len(text):]
    href = text if text.lower().startswith(("http://", "https://")) else "https://" + text
    return (
        '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>%s'
        % (html.escape(href, quote=True), text, suffix)
    )


DOMAIN_FIND = re.compile(
    r"(?<![\w/])(?:[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}"
    r"(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?)"
)


def linkify_raw_links_section(text: str) -> str:
    """Turn bare domains in the '原始链接' appendix into clickable links.

    Only touches the appendix block, so headings and prose elsewhere are safe.
    """
    out = []
    active = False
    for line in text.splitlines(keepends=True):
        if re.match(r"^## 附：.*原始链接", line):
            active = True
            out.append(line)
            continue
        if active and line.strip() == "---":
            active = False
            out.append(line)
            continue
        if active and ("｜" in line or line.startswith("**线上补充**")):
            def repl(m):
                s = m.group(0)
                if "://" in s or s.endswith("."):
                    return s
                return "[%s](https://%s)" % (s, s)
            line = DOMAIN_FIND.sub(repl, line)
        out.append(line)
    return "".join(out)


def strip_tags(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def convert(src: Path, linkify: bool, text: str | None = None) -> tuple[str, list[tuple[str, str, str]]]:
    text = text if text is not None else src.read_text(encoding="utf-8")
    if linkify:
        text = linkify_raw_links_section(text)

    md = markdown.Markdown(
        extensions=["tables", "toc", "sane_lists", "fenced_code"],
        extension_configs={"toc": {"slugify": slugify, "permalink": False}},
    )
    body = md.convert(text)

    for href, target in HREF_MAP.items():
        body = body.replace('href="%s"' % href, 'href="%s"' % target)
    body = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a href="\1" target="_blank" rel="noopener noreferrer"',
        body,
    )
    body = autolink_html(body)
    body = sanitize_body(body)

    heads = [
        (level, hid, strip_tags(raw))
        for level, hid, raw in re.findall(
            r'<h([12]) id="([^"]+)"[^>]*>(.*?)</h\1>', body, re.S
        )
    ]
    return body, heads


def build_toc(heads) -> str:
    parts = []
    first_h1_skipped = False
    for level, hid, title in heads:
        if level == "1" and not first_h1_skipped:
            first_h1_skipped = True
            continue
        cls = "toc-group" if level == "1" else "toc-item"
        parts.append(
            '      <a class="%s" href="#%s" data-title="%s">%s</a>'
            % (cls, html.escape(hid, quote=True), html.escape(title, quote=True), html.escape(title))
        )
    return "\n".join(parts)


def render(tpl: str, **kv) -> str:
    for key, value in kv.items():
        tpl = tpl.replace("{{" + key + "}}", value)
    left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", tpl)))
    if left:
        raise RuntimeError("unresolved placeholders: %s" % ", ".join(left))
    return tpl


def chip_html(link: dict, kind: str = "") -> str:
    label = html.escape(link["label"])
    url = html.escape(link["url"], quote=True)
    prefix = "主页 · " if kind == "home" else ""
    return (
        '<a class="chip%s" href="%s" target="_blank" rel="noopener noreferrer" title="%s">%s%s</a>'
        % (" " + kind if kind else "", url, label, prefix, label)
    )


def chapter_index(heads) -> list[tuple[str, str, str, str]]:
    out = []
    for level, hid, title in heads:
        if level != "2":
            continue
        m = re.match(r"^(\d{2})\s+(.+?)\s*[：:]\s*(.+)$", title)
        if m:
            out.append((m.group(1), m.group(2).strip(), m.group(3).strip(), hid))
    return out


def person_card(num: str, person: dict, anchor: str, topic: str, issue_key: str) -> str:
    full = "%s %s：%s" % (num, person["name"], topic)
    name = html.escape(person["name"])
    href = (
        "./issue-%s.html#%s" % (issue_key, html.escape(anchor, quote=True))
        if anchor
        else "./issue-%s.html" % issue_key
    )
    chips = []
    if person.get("homepage"):
        chips.append(chip_html(person["homepage"], "home"))
    chips.extend(chip_html(x) for x in person.get("links", []))
    chips_html = "".join(chips) or '<span class="no-links">汇总页未附主页或项目链接</span>'
    return (
        '    <div class="person-card">\n'
        '      <div class="person-head"><span class="person-num">%s</span>'
        '<a class="person-name" href="%s">%s</a></div>\n'
        '      <p class="person-topic" title="%s">%s</p>\n'
        '      <div class="chips">%s</div>\n'
        '      <a class="read-link" href="%s">阅读精读 →</a>\n'
        '    </div>'
        % (num, href, name, html.escape(full, quote=True), html.escape(topic), chips_html, href)
    )


def inject_inline_links(body: str, people: list) -> str:
    by_name = {p["name"]: p for p in people}

    def repl(m):
        num, name = m.group(1), m.group(2).strip()
        person = by_name.get(name)
        if person is None:
            i = int(num) - 1
            person = people[i] if 0 <= i < len(people) else None
        if person is None:
            return m.group(0)
        chips = []
        if person.get("homepage"):
            chips.append(chip_html(person["homepage"], "home"))
        chips.extend(chip_html(x) for x in person.get("links", []))
        if not chips:
            return m.group(0)
        return (
            m.group(0)
            + '\n<div class="inline-links"><span class="inline-label">相关链接</span>'
            + "".join(chips)
            + "</div>"
        )

    return re.sub(
        r'<h2 id="[^"]+">(\d{2})\s+([^：<]+)[：:][^<]*</h2>', repl, body
    )


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def nav_html(kind: str, active: str | None = None) -> str:
    rows = []
    if kind == "issues":
        latest = ISSUES[-1]["key"]
        for issue in ISSUES:
            cls = ["nav-issue"]
            if issue["key"] != latest:
                cls.append("nav-old")
            if issue["key"] == active:
                cls.append("active")
            rows.append(
                '    <a class="%s" href="./issue-%s.html">%s</a>'
                % (" ".join(cls), issue["key"], html.escape(issue["label"]))
            )
        rows.append('    <a class="nav-cross" href="./index.html#handbook">学习手册</a>')
        rows.append('    <a class="nav-cross" href="./index.html#resources">资源索引</a>')
        rows.append(
            '    <a class="nav-official" href="https://tabthursday.com/notes"'
            ' target="_blank" rel="noopener noreferrer">官方汇总</a>'
        )
    elif kind == "guides":
        rows.append('    <a class="nav-cross" href="./index.html#tab-thursday">活动精读</a>')
        rows.append('    <a class="nav-cross" href="./index.html#resources">资源索引</a>')
    elif kind == "resources":
        rows.append('    <a class="nav-cross" href="./index.html#tab-thursday">活动精读</a>')
        rows.append('    <a class="nav-cross" href="./index.html#handbook">学习手册</a>')
    else:
        rows.append('    <a class="nav-issue" href="#tab-thursday">活动精读</a>')
        rows.append('    <a class="nav-issue" href="#handbook">学习手册</a>')
        rows.append('    <a class="nav-issue" href="#resources">资源索引</a>')
    rows.append(
        '    <a class="nav-repo" href="%s" target="_blank" rel="noopener noreferrer">GitHub</a>'
        % REPO_URL
    )
    return "\n".join(rows)


def sidebar_extra_html(active: str) -> str:
    rows = ['      <div class="sidebar-sub">手册其他篇目</div>']
    for guide in GUIDES:
        if guide["key"] == active:
            continue
        rows.append(
            '      <a class="sidebar-guide" href="./guide-%s.html">%s</a>'
            % (guide["key"], html.escape(guide["label"]))
        )
    rows.append('      <div class="sidebar-sub">可直接复制的模板</div>')
    for template in TEMPLATES:
        if template["key"] == active:
            continue
        rows.append(
            '      <a class="sidebar-guide" href="./template-%s.html">%s</a>'
            % (template["key"], html.escape(template["label"]))
        )
    return "\n".join(rows)


def guide_prev_next(idx: int) -> tuple[str, str]:
    prev_html = ""
    next_html = ""
    if idx > 0:
        guide = GUIDES[idx - 1]
        prev_html = '<a href="./guide-%s.html">← %s</a>' % (guide["key"], html.escape(guide["label"]))
    if idx < len(GUIDES) - 1:
        guide = GUIDES[idx + 1]
        next_html = '<a href="./guide-%s.html">%s →</a>' % (guide["key"], html.escape(guide["label"]))
    return prev_html, next_html


def guide_card(idx: int, guide: dict) -> str:
    return (
        '    <a class="issue-card guide-card" href="./guide-%s.html">\n'
        '      <div class="issue-no">第 %d 篇</div>\n'
        '      <h2>%s</h2>\n'
        '      <div class="issue-meta">复核 %s</div>\n'
        '      <p class="issue-theme">%s</p>\n'
        '      <span class="cta">开始阅读 →</span>\n'
        '    </a>'
        % (
            guide["key"],
            idx,
            html.escape(guide["label"]),
            guide["stamp"],
            html.escape(guide["desc"]),
        )
    )


def template_card(idx: int, template: dict) -> str:
    return (
        '    <a class="issue-card guide-card" href="./template-%s.html">\n'
        '      <div class="issue-no">模板 %d</div>\n'
        '      <h2>%s</h2>\n'
        '      <div class="issue-meta">可直接复制 · 复核 %s</div>\n'
        '      <p class="issue-theme">%s</p>\n'
        '      <span class="cta">打开模板 →</span>\n'
        '    </a>'
        % (
            template["key"],
            idx,
            html.escape(template["label"]),
            template["stamp"],
            html.escape(template["desc"]),
        )
    )


def template_prev_next(idx: int) -> tuple[str, str]:
    prev_html = ""
    next_html = ""
    if idx > 0:
        template = TEMPLATES[idx - 1]
        prev_html = '<a href="./template-%s.html">← %s</a>' % (
            template["key"],
            html.escape(template["label"]),
        )
    if idx < len(TEMPLATES) - 1:
        template = TEMPLATES[idx + 1]
        next_html = '<a href="./template-%s.html">%s →</a>' % (
            template["key"],
            html.escape(template["label"]),
        )
    return prev_html, next_html


def prev_next(idx: int) -> tuple[str, str]:
    prev_html = ""
    next_html = ""
    if idx > 0:
        issue = ISSUES[idx - 1]
        prev_html = '<a href="./issue-%s.html">← %s</a>' % (
            issue["key"],
            html.escape(issue["label"]),
        )
    if idx < len(ISSUES) - 1:
        issue = ISSUES[idx + 1]
        next_html = '<a href="./issue-%s.html">%s →</a>' % (
            issue["key"],
            html.escape(issue["label"]),
        )
    return prev_html, next_html


def unique_share_people(links: dict) -> int:
    names = set()
    for issue in ISSUES:
        for person in links.get(issue["key"], []):
            names.add(NAME_ALIASES.get(person["name"], person["name"]))
    return len(names)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8", newline="\n")
    (ASSETS / "style.css").write_text(CSS, encoding="utf-8", newline="\n")
    (ASSETS / "app.js").write_text(JS, encoding="utf-8", newline="\n")
    nav_links = "\n".join(
        [
            '    <a href="./index.html#tab-thursday">活动精读</a>',
            '    <a href="./index.html#handbook">学习手册</a>',
            '    <a href="./index.html#resources">资源索引</a>',
        ]
        + [
            '    <a href="./issue-%s.html">%s</a>'
            % (issue["key"], html.escape(issue["label"]))
            for issue in ISSUES
        ]
    )
    (DOCS / "404.html").write_text(render(NOTFOUND_TPL, NAV_LINKS=nav_links), encoding="utf-8", newline="\n")

    links = (
        json.loads(LINKS_FILE.read_text(encoding="utf-8"))
        if LINKS_FILE.exists()
        else {}
    )
    missing = [issue["key"] for issue in ISSUES if not links.get(issue["key"])]
    if missing:
        raise RuntimeError("links.json 缺少期数: %s" % ", ".join(missing))

    converted = {}
    for issue in ISSUES:
        src = ROOT / issue["src"]
        body, heads = convert(src, linkify=True)
        people = links.get(issue["key"], [])
        body = inject_inline_links(body, people)
        cjk = cjk_count(src.read_text(encoding="utf-8"))
        converted[issue["key"]] = (body, heads, cjk)
        print(
            "  issue %s: %d sharers, %d headings, %.1f 万汉字"
            % (issue["key"], len(people), len(heads), cjk / 10000)
        )

    for idx, issue in enumerate(ISSUES):
        body, heads, _ = converted[issue["key"]]
        prev_html, next_html = prev_next(idx)
        page = render(
            PAGE_TPL,
            TITLE=html.escape(issue["title"]),
            DESC=html.escape(issue["desc"]),
            REPO=REPO_URL,
            LABEL=html.escape(issue["label"]),
            NAV=nav_html("issues", issue["key"]),
            SIDEBAR_EXTRA="",
            BLOB=BLOB + quote(issue["src"]),
            TOC=build_toc(heads),
            BODY=body,
            PREV=prev_html,
            NEXT=next_html,
        )
        out = DOCS / ("issue-%s.html" % issue["key"])
        out.write_text(page, encoding="utf-8", newline="\n")
        print("wrote %-28s %7d bytes  (%d headings)" % (out.name, out.stat().st_size, len(heads)))

    guides_converted = {}
    for guide in GUIDES:
        src = ROOT / guide["src"]
        body, heads = convert(src, linkify=False)
        cjk = cjk_count(src.read_text(encoding="utf-8"))
        guides_converted[guide["key"]] = (body, heads, cjk)
        print("  guide %-14s %2d headings, %.1f 千汉字" % (guide["key"], len(heads), cjk / 1000))

    for idx, guide in enumerate(GUIDES):
        body, heads, _ = guides_converted[guide["key"]]
        prev_html, next_html = guide_prev_next(idx)
        page = render(
            PAGE_TPL,
            TITLE=html.escape(guide["title"]),
            DESC=html.escape(guide["desc"]),
            REPO=REPO_URL,
            LABEL=html.escape(guide["label"]),
            NAV=nav_html("guides", guide["key"]),
            SIDEBAR_EXTRA=sidebar_extra_html(guide["key"]),
            BLOB=BLOB + quote(guide["src"]),
            TOC=build_toc(heads),
            BODY=body,
            PREV=prev_html,
            NEXT=next_html,
        )
        out = DOCS / ("guide-%s.html" % guide["key"])
        out.write_text(page, encoding="utf-8", newline="\n")
        print("wrote %-28s %7d bytes  (%d headings)" % (out.name, out.stat().st_size, len(heads)))

    for idx, template in enumerate(TEMPLATES):
        src = ROOT / template["src"]
        body, heads = convert(src, linkify=False)
        prev_html, next_html = template_prev_next(idx)
        page = render(
            PAGE_TPL,
            TITLE=html.escape(template["title"]),
            DESC=html.escape(template["desc"]),
            REPO=REPO_URL,
            LABEL=html.escape(template["label"]),
            NAV=nav_html("guides", template["key"]),
            SIDEBAR_EXTRA=sidebar_extra_html(template["key"]),
            BLOB=BLOB + quote(template["src"]),
            TOC=build_toc(heads),
            BODY=body,
            PREV=prev_html,
            NEXT=next_html,
        )
        out = DOCS / ("template-%s.html" % template["key"])
        out.write_text(page, encoding="utf-8", newline="\n")
        print("wrote %-28s %7d bytes  (%d headings)" % (out.name, out.stat().st_size, len(heads)))

    resource_pages = [
        (
            "zyscj",
            RESOURCE_DIR / "INDEX.md",
            "资源索引",
            "需求速查 · 我要找什么，看哪一页",
            "84 个资源页按用途归类，每行给出外链数与正文入口。",
        ),
        (
            "zyscj-links",
            RESOURCE_DIR / "LINKS.md",
            "资源索引",
            "全站外链总表",
            "98 个页面的外链按页面分组列出，可以按站名或网址检索。",
        ),
    ]
    for key, src, label, title, desc in resource_pages:
        text = strip_self_anchors(src.read_text(encoding="utf-8"))
        if key == "zyscj-links":
            text = re.sub(
                r"<!--\s*(docs/[^\s]+\.md)\s*-->",
                r"[→ 打开这一页的完整清单](\1)",
                text,
            )
        body, heads = convert(src, linkify=False, text=text)
        if key == "zyscj":
            prev_html = '<a href="./index.html#resources">← 资源索引</a>'
            next_html = '<a href="./zyscj-all.html">全部 %d 页 →</a>' % len(RESOURCE_SLUGS)
        else:
            prev_html = '<a href="./zyscj-all.html">← 全部 %d 页</a>' % len(RESOURCE_SLUGS)
            next_html = '<a href="./zyscj.html">需求速查 →</a>'
        page = render(
            PAGE_TPL,
            TITLE=html.escape(title),
            DESC=html.escape(desc),
            REPO=REPO_URL,
            LABEL=html.escape(label),
            NAV=nav_html("resources"),
            SIDEBAR_EXTRA=resource_entry_sidebar_html(key),
            BLOB=BLOB + quote(src.relative_to(ROOT).as_posix()),
            TOC=build_toc(heads),
            BODY=body,
            PREV=prev_html,
            NEXT=next_html,
        )
        out = DOCS / ("%s.html" % key)
        out.write_text(page, encoding="utf-8", newline="\n")
        print("wrote %-28s %7d bytes  (%d headings)" % (out.name, out.stat().st_size, len(heads)))

    for path, slug in RESOURCE_SLUGS.items():
        raw = path.read_text(encoding="utf-8")
        body, heads = convert(path, linkify=False, text=strip_self_anchors(raw))
        parent = resource_parent(path)
        prev_html = (
            '<a href="./%s.html">↑ %s</a>'
            % (RESOURCE_SLUGS[parent], html.escape(resource_heading(parent)))
            if parent is not None
            else '<a href="./zyscj-all.html">↑ 全部资源页</a>'
        )
        page = render(
            PAGE_TPL,
            TITLE=html.escape(resource_heading(path)),
            DESC=html.escape("资源索引 · " + resource_heading(path)),
            REPO=REPO_URL,
            LABEL="资源索引",
            NAV=nav_html("resources"),
            SIDEBAR_EXTRA=resource_doc_sidebar_html(path),
            BLOB=BLOB + quote(path.relative_to(ROOT).as_posix()),
            TOC=build_toc(heads),
            BODY=resource_breadcrumb(path) + body,
            PREV=prev_html,
            NEXT='<a href="./zyscj-all.html">全部 %d 页 →</a>' % len(RESOURCE_SLUGS),
        )
        out = DOCS / ("%s.html" % slug)
        out.write_text(page, encoding="utf-8", newline="\n")
    print("wrote zyscj-doc-*.html           %d resource pages" % len(RESOURCE_SLUGS))

    body, heads = convert(RESOURCE_DIR / "INDEX.md", linkify=False, text=resource_all_markdown())
    page = render(
        PAGE_TPL,
        TITLE="全部资源页",
        DESC=html.escape("资源站 %d 个页面按目录分组，每一页都能在本站打开。" % len(RESOURCE_DOCS)),
        REPO=REPO_URL,
        LABEL="资源索引 · 全部页面",
        NAV=nav_html("resources"),
        SIDEBAR_EXTRA=resource_entry_sidebar_html("zyscj-all"),
        BLOB=REPO_URL + "/tree/main/resource-grocery/zyscj/docs",
        TOC=build_toc(heads),
        BODY=body,
        PREV='<a href="./zyscj.html">需求速查</a>',
        NEXT='<a href="./zyscj-links.html">外链总表 →</a>',
    )
    out = DOCS / "zyscj-all.html"
    out.write_text(page, encoding="utf-8", newline="\n")
    print("wrote %-28s %7d bytes  (%d headings)" % (out.name, out.stat().st_size, len(heads)))

    latest = ISSUES[-1]
    cards = []
    for issue in ISSUES:
        _, _, cjk = converted[issue["key"]]
        bullets = "\n".join("        <li>%s</li>" % html.escape(b) for b in issue["bullets"])
        cards.append(
            '    <a class="issue-card%s" href="./issue-%s.html">\n'
            '      <div class="issue-no">#%s</div>\n'
            '      <h2>%s · %s</h2>\n'
            '      <div class="issue-meta">%s · %s · 约 %.1f 万汉字</div>\n'
            '      <p class="issue-theme">%s</p>\n'
            '      <p style="font-size:13.5px;color:var(--muted);margin:0 0 14px">%s</p>\n'
            '      <ul>\n%s\n      </ul>\n'
            '      <span class="cta">开始阅读 →</span>\n'
            '    </a>'
            % (
                " featured" if issue["key"] == latest["key"] else "",
                issue["key"], issue["key"],
                html.escape(issue["label"]), html.escape(issue["count"]),
                html.escape(issue["date"]), html.escape(issue["place"]), cjk / 10000,
                html.escape(issue["theme"]), html.escape(issue["desc"]),
                bullets,
            )
        )

    _, latest_heads, _ = converted[latest["key"]]
    quick = []
    part_no = 0
    skipped_first = False
    for level, hid, title in latest_heads:
        if level == "1" and not skipped_first:
            skipped_first = True
            continue
        if level == "1":
            part_no += 1
            quick.append(
                '    <a href="./issue-%s.html#%s">%s<small>第 %d 部分</small></a>'
                % (latest["key"], html.escape(hid, quote=True), html.escape(title), part_no)
            )
    if not quick:
        raise RuntimeError("最新一期缺少分部标题: %s" % latest["key"])

    index_blocks = []
    total_cards = 0
    for issue in ISSUES:
        _, heads, _ = converted[issue["key"]]
        chapters = chapter_index(heads)
        entries = links.get(issue["key"], [])
        if len(entries) != len(chapters):
            raise RuntimeError(
                "issue %s: %d link entries vs %d chapter anchors"
                % (issue["key"], len(entries), len(chapters))
            )
        by_name = {p["name"]: p for p in entries}
        cards_html = []
        for num, name, topic, hid in chapters:
            person = by_name.get(name)
            if person is None:
                canonical = NAME_ALIASES.get(name, name)
                person = next(
                    (p for p in entries if NAME_ALIASES.get(p["name"], p["name"]) == canonical),
                    None,
                )
            if person is None:
                raise RuntimeError(
                    "issue %s: 章节 %s 找不到对应分享者" % (issue["key"], num)
                )
            cards_html.append(person_card(num, person, hid, topic, issue["key"]))
        total_cards += len(entries)
        index_blocks.append(
            '  <div class="issue-sub">%s · %s</div>\n  <section class="people-cards">\n%s\n  </section>'
            % (html.escape(issue["label"]), html.escape(issue["count"]), "\n".join(cards_html))
        )
        print("  issue %s: %d sharer cards, %d chapter anchors" % (
            issue["key"], len(entries), len(chapters)
        ))

    official_links = "\n".join(
        '      <a href="https://tabthursday.com/%s" target="_blank" rel="noopener noreferrer">#%s 官方汇总</a>'
        % (issue["key"], issue["key"])
        for issue in ISSUES
    )
    unique_people = unique_share_people(links)
    issue_count_cn = CN_NUM.get(len(ISSUES), str(len(ISSUES)))
    hero = (
        "三类整理放在一起：Tab 星期四%s期共 %d 个分享席位（%d 位分享者）的逐章精读；"
        "面向计算机视觉方向研究生的学习手册；以及一个资源导航站的全站索引（%d 个页面、3323 条外链）。"
        "每条数字都标了来源等级与复核日期，推断与事实分开写。"
        % (issue_count_cn, total_cards, unique_people, len(RESOURCE_DOCS))
    )
    issue_note = (
        "每人带一个本周想分享的浏览器标签页，现场投票决定讲述时长。%s期共 %d 个分享席位、%d 位分享者，"
        "逐条访问产品站点、GitHub 仓库与公开报道后扩写成可独立阅读的章节，每期各收敛出 5 条判断。"
        % (issue_count_cn, total_cards, unique_people)
    )
    guide_note = (
        "五篇手册整理于 2026 年 9 月，复核日期写在每篇文首；两份模板可以直接复制填写。"
        "免费额度与政策类数字会过期，注册前按官网确认一次。"
    )
    notice = "正文里的外部链接都会在新标签页打开；文章页左侧目录可以按章节标题筛选，点击直达对应位置。"
    if NEXT_EVENT:
        notice += (
            '下一期 %s 正在报名：%s %s · %s · '
            '<a href="%s" target="_blank" rel="noopener noreferrer">Luma 报名</a>。'
            % (
                NEXT_EVENT["label"],
                NEXT_EVENT["date"],
                NEXT_EVENT["time"],
                NEXT_EVENT["place"],
                NEXT_EVENT["url"],
            )
        )
    home_desc = (
        "公开材料精读：Tab 星期四%s期分享的深度精读（%d 个分享席位、%d 位分享者）、"
        "五篇研究生学习手册与两份可复制模板，以及一个资源导航站的全站索引（%d 个页面、3323 条外链）。"
        % (issue_count_cn, total_cards, unique_people, len(RESOURCE_DOCS))
    )

    resource_cards = [
        '    <a class="issue-card guide-card" href="./zyscj.html">\n'
        '      <div class="issue-no">需求速查</div>\n'
        '      <h2>我要找什么，看哪一页</h2>\n'
        '      <div class="issue-meta">84 个资源页 · 3323 条外链 · 抓取于 2026-11-01</div>\n'
        '      <p class="issue-theme">按用途归类：图片与设计素材、音乐、书籍、软件、影视、网盘、学习与工具。</p>\n'
        '      <span class="cta">开始查找 →</span>\n'
        '    </a>',
        '    <a class="issue-card guide-card" href="./zyscj-links.html">\n'
        '      <div class="issue-no">外链总表</div>\n'
        '      <h2>全站外链总表</h2>\n'
        '      <div class="issue-meta">98 个页面 · 3323 条外链</div>\n'
        '      <p class="issue-theme">每个页面的外链按站名与网址列出，可以直接在浏览器里搜关键词。</p>\n'
        '      <span class="cta">开始检索 →</span>\n'
        '    </a>',
        '    <a class="issue-card guide-card" href="./zyscj-all.html">\n'
        '      <div class="issue-no">全部页面</div>\n'
        '      <h2>%d 个资源页的总目录</h2>\n'
        '      <div class="issue-meta">%d 个页面 · 按目录分组 · 每页带外链数</div>\n'
        '      <p class="issue-theme">资源站的首页、总索引、各章节索引与正文页全在这里，每一页都能从这一页打开。</p>\n'
        '      <span class="cta">查看全部 →</span>\n'
        '    </a>'
        % (len(RESOURCE_DOCS), len(RESOURCE_DOCS)),
    ]
    resource_note = (
        "这里镜像一个资源导航站的全站内容：%d 个页面与 3323 条外链，按原样收录、未做筛选；"
        "链接能不能打开、有没有版权风险，需要自己判断。"
    ) % len(RESOURCE_DOCS)

    home = render(
        HOME_TPL,
        REPO=REPO_URL,
        HOME_DESC=html.escape(home_desc),
        HERO=html.escape(hero),
        NOTICE=notice,
        NAV=nav_html("home"),
        OFFICIAL_LINKS=official_links,
        CARDS="\n".join(cards),
        GUIDE_CARDS="\n".join(
            [guide_card(i, guide) for i, guide in enumerate(GUIDES, 1)]
            + [template_card(i, template) for i, template in enumerate(TEMPLATES, 1)]
        ),
        RESOURCE_CARDS="\n".join(resource_cards),
        RESOURCE_PAGE_COUNT=str(len(RESOURCE_DOCS) + 2),
        RESOURCE_NOTE=html.escape(resource_note),
        QUICK="\n".join(quick),
        ISSUE_COUNT=issue_count_cn,
        GUIDE_COUNT="%d 篇 + %d 份模板" % (len(GUIDES), len(TEMPLATES)),
        ISSUE_NOTE=html.escape(issue_note),
        GUIDE_NOTE=html.escape(guide_note),
        LATEST_LABEL=html.escape(latest["label"]),
        INDEX_BLOCKS="\n\n".join(index_blocks),
        STAMP=STAMP,
    )
    (DOCS / "index.html").write_text(home, encoding="utf-8", newline="\n")
    print("wrote %-28s %7d bytes  (%d issue cards, %d guide cards, %d sharer cards)" % (
        "index.html",
        (DOCS / "index.html").stat().st_size,
        len(cards),
        len(GUIDES),
        total_cards,
    ))
    print("\nPreview locally:  open docs/index.html")
    print("After push:       " + SITE_URL)


if __name__ == "__main__":
    main()
