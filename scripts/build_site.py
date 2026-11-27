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
  --paper:#fffdfa;--surface:#fffefb;--ink:#212427;--muted:#4f5452;--faint:#6f736f;
  --line:#e9e4d9;--line2:#d8d1c2;
  --accent:#164e63;--accent-soft:#eaf2f5;--accent-line:#2291bc;--mark:#b45309;
  --edge:rgba(255,255,255,.9);--warm-line:rgba(120,100,70,.09);
  --card-bg:linear-gradient(180deg,rgba(255,255,255,.9),rgba(255,255,255,.6));
  --card-bg-soft:linear-gradient(180deg,rgba(255,255,255,.78),rgba(255,255,255,.46));
  --chip-bg:#faf6ec;--quote-bg:#f7f2e6;--quote-ink:#4a4a44;--th-bg:#f5f0e2;--row-alt:#fdfbf5;
  --code-bg:#f2ede0;--notice-bg:#f4f0e3;--notice-ink:#3c4a4d;
  --notice-sheen-top:rgba(255,255,255,.5);--notice-sheen-bottom:rgba(255,255,255,.16);
  --bar-bg:rgba(255,253,250,.68);
  --bar-shadow:inset 0 -1px 0 var(--warm-line),0 1px 0 rgba(255,255,255,.8);
  --atmosphere:radial-gradient(ellipse 46% 38% at 86% -8%,rgba(255,255,255,.92),rgba(255,252,244,.35) 46%,rgba(255,250,240,0) 72%),radial-gradient(ellipse 40% 34% at 4% 92%,rgba(252,214,166,.24),rgba(252,214,166,0) 68%),radial-gradient(ellipse 52% 40% at 50% 106%,rgba(206,224,230,.2),rgba(206,224,230,0) 70%);
  --grain:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='160' height='160' filter='url(%23n)' opacity='.55'/></svg>");
  --grain-opacity:.05;--grain-blend:multiply;
  --sel-bg:#086a8d;--sel-ink:#ffffff;
  --r-lg:22px;--r-md:12px;--r-sm:8px;--r-pill:999px;
  --sheen:rgba(255,255,255,.94);
  --shadow-card:inset 0 1px 0 rgba(255,255,255,.95),0 0 0 1px rgba(120,100,70,.07),0 1px 2px rgba(74,55,30,.05),0 14px 28px -16px rgba(74,55,30,.2),0 42px 84px -48px rgba(74,55,30,.3);
  --shadow-card-hover:inset 0 1px 0 rgba(255,255,255,.98),0 0 0 1px rgba(120,100,70,.14),0 2px 4px rgba(74,55,30,.06),0 22px 40px -20px rgba(74,55,30,.26),0 60px 110px -56px rgba(74,55,30,.34);
  --shadow-pop:inset 0 1px 0 rgba(255,255,255,.9),0 0 0 1px rgba(120,100,70,.08),0 2px 4px rgba(74,55,30,.05),0 10px 22px -14px rgba(74,55,30,.22),0 28px 56px -40px rgba(74,55,30,.26);
  --shadow-pop-hover:inset 0 1px 0 rgba(255,255,255,.96),0 0 0 1px rgba(120,100,70,.12),0 2px 4px rgba(74,55,30,.06),0 16px 30px -16px rgba(74,55,30,.24),0 40px 72px -46px rgba(74,55,30,.28);
  --serif:"Songti SC","Noto Serif SC","Source Han Serif SC","STSong","SimSun",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Consolas,monospace;
  --ease-out:cubic-bezier(.22,.61,.36,1);
  --ease-in:cubic-bezier(.55,.06,.68,.19);
  --topbar-h:64px;
  color-scheme:light;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.85;letter-spacing:.012em;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.page-atmosphere{position:fixed;inset:0;z-index:0;pointer-events:none;background:var(--atmosphere)}
.page-atmosphere::after{content:"";position:absolute;inset:0;background-image:var(--grain);background-size:160px 160px;opacity:var(--grain-opacity);mix-blend-mode:var(--grain-blend)}
a{color:inherit;text-decoration:none}
button,input{font-family:inherit}
::selection{background:var(--sel-bg);color:var(--sel-ink)}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent-line);z-index:100;transition:width .08s linear}
.topbar{position:sticky;top:0;z-index:60;height:var(--topbar-h);background:var(--bar-bg);display:flex;align-items:center;gap:26px;padding:0 30px;box-shadow:var(--bar-shadow);transition:box-shadow .28s var(--ease-out)}
@supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){
  .topbar{-webkit-backdrop-filter:blur(16px) saturate(1.4);backdrop-filter:blur(16px) saturate(1.4)}
}
.topbar.is-stuck{box-shadow:inset 0 -1px 0 var(--warm-line),0 12px 32px -26px rgba(74,55,30,.5)}
.brand{font-family:var(--serif);font-weight:600;font-size:17px;color:var(--ink);white-space:nowrap;letter-spacing:.01em}
.brand:hover{color:var(--accent)}
.topbar nav{display:flex;gap:22px;align-items:center;flex:1;flex-wrap:wrap}
.topbar nav a{font-size:13.5px;color:var(--muted);border-bottom:1px solid transparent;padding-bottom:1px;transition:color .18s,border-color .18s}
.topbar nav a:hover{color:var(--accent);border-bottom-color:var(--accent-line)}
.topbar nav a.active{color:var(--accent);font-weight:600;border-bottom-color:var(--accent)}
.menu-toggle{display:none;border:1px solid var(--line2);background:var(--surface);color:var(--ink);border-radius:var(--r-sm);padding:6px 12px;font-size:13px;cursor:pointer}
.theme-toggle{position:fixed;right:24px;bottom:calc(24px + env(safe-area-inset-bottom));z-index:56;width:44px;height:44px;border-radius:var(--r-pill);border:1px solid var(--line2);background:var(--surface);color:var(--accent);font-size:17px;line-height:1;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;box-shadow:var(--shadow-pop);transition:transform .18s var(--ease-out),border-color .18s,background-color .18s}
.theme-toggle:hover{border-color:var(--accent-line);background:var(--accent-soft)}
.theme-toggle:active{transform:scale(.96)}

.layout{position:relative;z-index:1;max-width:1320px;margin:0 auto;padding:40px 26px 104px;display:grid;grid-template-columns:276px minmax(0,1fr);gap:40px;align-items:start}
.sidebar{position:sticky;top:calc(var(--topbar-h) + 20px);max-height:calc(100vh - var(--topbar-h) - 44px);overflow:auto;background:var(--card-bg-soft);border-radius:var(--r-lg);padding:20px 16px;box-shadow:var(--shadow-card);scrollbar-width:thin;-webkit-backdrop-filter:blur(16px) saturate(1.2);backdrop-filter:blur(16px) saturate(1.2)}
.sidebar-head{padding:2px 6px 14px;border-bottom:1px solid var(--line);margin-bottom:12px}
.sidebar-title{font-size:12.5px;font-weight:600;color:var(--accent);letter-spacing:.06em;margin-bottom:11px}
.filter{width:100%;border:1px solid var(--line2);border-radius:var(--r-sm);padding:8px 11px;font-size:12.5px;color:var(--ink);background:var(--chip-bg);outline:none;transition:border-color .18s,background-color .18s}
.filter:focus{border-color:var(--accent-line);background:var(--surface)}
.filter-hint{font-size:11.5px;color:var(--faint);margin-top:8px}
.toc{display:flex;flex-direction:column;gap:1px}
.toc a{display:block;border-radius:var(--r-sm);padding:6px 10px;font-size:12.8px;line-height:1.55;color:var(--muted);border-left:2px solid transparent;transition:background-color .16s,color .16s,border-color .16s}
.toc a:hover{background:var(--accent-soft);color:var(--accent);text-decoration:none}
.toc a.active{background:var(--accent-soft);color:var(--accent);border-left-color:var(--accent)}
.toc .toc-group{font-family:var(--serif);font-weight:600;color:var(--ink);margin-top:16px;font-size:13px;background:transparent}
.toc .toc-group:first-child{margin-top:0}
.toc .toc-item{padding-left:18px}
.sidebar-foot{margin-top:16px;padding:14px 6px 0;border-top:1px solid var(--line);font-size:12px;display:flex;flex-direction:column;gap:7px}
.sidebar-foot a{color:var(--muted)}
.sidebar-foot a:hover{color:var(--accent)}

.content{background:var(--card-bg);border-radius:var(--r-lg);padding:60px 68px 84px;min-width:0;box-shadow:var(--shadow-card);-webkit-backdrop-filter:blur(16px) saturate(1.2);backdrop-filter:blur(16px) saturate(1.2)}
.content::before,.sidebar::before,.issue-card::before,.hero-spot::before{content:"";position:absolute;left:20px;right:20px;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--sheen) 22%,var(--sheen) 78%,transparent);pointer-events:none}
.content,.sidebar,.issue-card{position:relative}
.prose{font-size:17px;line-height:1.95;color:var(--ink)}
.prose a{text-decoration:underline;text-decoration-color:var(--accent-line);text-decoration-thickness:1px;text-underline-offset:3px}
.prose a:hover{color:var(--accent);text-decoration-color:var(--accent);text-decoration-thickness:2px}
.prose .chip{text-decoration:none}
.prose>h1:first-child,.prose>.breadcrumb+h1{font-family:var(--serif);font-size:40px;line-height:1.28;margin:0 0 1.1em;font-weight:600;letter-spacing:-.02em;border-bottom:0;padding-bottom:0}
.prose>h1:first-child::after,.prose>.breadcrumb+h1::after{content:"";display:block;width:52px;height:2px;margin-top:.55em;background:linear-gradient(90deg,var(--accent),rgba(22,78,99,0))}
.breadcrumb{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:0 0 20px;font-size:12.5px;line-height:1.7;color:var(--faint)}
.breadcrumb a{color:var(--muted);text-decoration:none;border-bottom:1px solid transparent}
.breadcrumb a:hover{color:var(--accent);border-bottom-color:var(--accent-line)}
.breadcrumb span{color:var(--line2)}
.prose h1{font-family:var(--serif);font-size:27px;line-height:1.45;margin:2.9em 0 1em;padding:0 0 .5em;border-bottom:1px solid var(--line);font-weight:600;letter-spacing:-.012em;scroll-margin-top:calc(var(--topbar-h) + 24px)}
.prose h2{font-family:var(--serif);font-size:21.5px;line-height:1.5;margin:2.5em 0 .85em;font-weight:600;letter-spacing:-.008em;scroll-margin-top:calc(var(--topbar-h) + 24px)}
.prose h3{font-size:16.5px;line-height:1.65;margin:1.9em 0 .6em;color:var(--muted);font-weight:600;scroll-margin-top:calc(var(--topbar-h) + 24px)}
.prose p{margin:1.15em 0}
.prose strong{font-weight:600;color:var(--ink)}
.prose ul,.prose ol{padding-left:1.6em;margin:.95em 0}
.prose li{margin:.38em 0}
.prose li::marker{color:var(--accent-line)}
.prose blockquote{margin:1.5em 0;padding:16px 22px;background:var(--quote-bg);border-left:3px solid var(--accent-line);border-radius:0 var(--r-md) var(--r-md) 0;color:var(--quote-ink);font-size:15.5px;line-height:1.8}
.prose blockquote p{margin:.4em 0}
.prose hr{border:0;border-top:1px solid var(--line);margin:2.8em 0}
.prose code{background:var(--code-bg);border-radius:5px;padding:2px 6px;font-size:.86em;font-family:var(--mono);word-break:break-word}
.prose pre{background:var(--quote-bg);border:1px solid var(--line);border-radius:var(--r-md);padding:16px 18px;overflow-x:auto}
.prose pre code{background:none;padding:0}
.prose table{border-collapse:collapse;width:100%;margin:1.5em 0;font-size:14px;display:block;overflow-x:auto;white-space:nowrap}
.prose table th,.prose table td{border:1px solid var(--line);padding:10px 14px;text-align:left;vertical-align:top;white-space:normal;min-width:96px}
.prose table th{background:var(--th-bg);font-weight:600;color:var(--ink)}
.prose table tr:nth-child(even) td{background:var(--row-alt)}
.prose a[target="_blank"]::after{content:" \2197";font-size:.76em;color:var(--accent-line);white-space:nowrap;margin-left:.1em}
.prose img{max-width:100%;height:auto;border-radius:var(--r-md)}
.article-foot{margin-top:58px;padding-top:24px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:13.5px;color:var(--muted)}
.article-foot a{color:var(--muted);border-bottom:1px solid transparent;transition:color .18s,border-color .18s}
.article-foot a:hover{color:var(--accent);border-bottom-color:var(--accent-line)}
.foot-issues{display:flex;gap:20px;flex-wrap:wrap}
.to-top{position:fixed;right:24px;bottom:calc(76px + env(safe-area-inset-bottom));width:44px;height:44px;border-radius:var(--r-pill);border:1px solid var(--line2);background:var(--surface);color:var(--accent);font-size:17px;cursor:pointer;opacity:0;pointer-events:none;transition:opacity .2s,transform .18s var(--ease-out),border-color .18s;z-index:55;box-shadow:var(--shadow-pop)}
.to-top.show{opacity:1;pointer-events:auto}
.to-top:hover{border-color:var(--accent-line);transform:translateY(-2px)}

.home{position:relative;z-index:1;max-width:1120px;margin:0 auto;padding:112px 26px 132px}
.hero{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(380px,.8fr);gap:64px;align-items:end;margin-bottom:96px}
.eyebrow{display:block;font-size:11.5px;font-weight:600;letter-spacing:.2em;color:var(--accent);opacity:.72;margin:0 0 14px}
.hero .eyebrow{margin:0 0 14px}
.hero h1{font-family:var(--serif);font-size:clamp(38px,4.6vw,58px);line-height:1.12;font-weight:600;margin:0 0 22px;letter-spacing:-.028em;text-wrap:balance}
.hero .hero-lede{font-size:17.5px;line-height:1.9;color:var(--muted);max-width:620px;margin:0 0 26px}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.hero-main>*{animation:rise .56s var(--ease-out) both}
.hero-main>*:nth-child(2){animation-delay:.08s}
.hero-main>*:nth-child(3){animation-delay:.16s}
.hero-main>*:nth-child(4){animation-delay:.24s}
.hero-spot{animation:rise .56s var(--ease-out) both;animation-delay:.2s}
.hero-links{display:flex;gap:22px;flex-wrap:wrap;font-size:13.5px}
.hero-links a{color:var(--muted);border-bottom:1px solid transparent;padding-bottom:2px;transition:color .18s,border-color .18s}
.hero-links a:hover{color:var(--accent);border-bottom-color:var(--accent-line)}
.section-title{font-family:var(--serif);font-size:clamp(28px,3vw,40px);font-weight:600;line-height:1.2;letter-spacing:-.02em;margin:120px 0 22px;padding-bottom:18px;border-bottom:1px solid var(--line)}
.section-no{display:inline-block;font-family:var(--serif);font-style:italic;font-size:13px;font-weight:400;letter-spacing:.18em;color:var(--accent);opacity:.55;margin-right:14px;vertical-align:3px;font-variant-numeric:tabular-nums}
.hero-spot{position:relative;background:var(--card-bg);border-radius:var(--r-lg);padding:32px 30px 28px;box-shadow:var(--shadow-card);-webkit-backdrop-filter:blur(16px) saturate(1.2);backdrop-filter:blur(16px) saturate(1.2)}
.hero-spot-kicker{font-size:11.5px;font-weight:600;letter-spacing:.16em;color:var(--mark);margin:0 0 14px}
.hero-spot-title{font-family:var(--serif);font-size:24px;line-height:1.35;font-weight:600;letter-spacing:-.012em;margin:0 0 18px}
.hero-spot-list{list-style:none;margin:0 0 22px;padding:0;display:flex;flex-direction:column;gap:9px;font-size:13px;line-height:1.65;color:var(--muted)}
.hero-spot-list li{position:relative;padding-left:16px}
.hero-spot-list li::before{content:"";position:absolute;left:0;top:.68em;width:7px;height:1px;background:var(--mark);opacity:.7}
.hero-spot-link{font-size:13px;color:var(--accent);font-weight:600;display:inline-flex;gap:6px;border-bottom:1px solid transparent;transition:border-color .18s}
.hero-spot-link:hover{border-bottom-color:var(--accent-line)}
.hero-meta{display:flex;flex-wrap:wrap;align-items:center;font-size:12.5px;color:var(--faint);margin:0 0 8px;padding:15px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.hero-meta span+span::before{content:"·";margin:0 14px;color:var(--line2)}
.issue-list{border-top:1px solid var(--line)}
.issue-row{display:grid;grid-template-columns:116px minmax(0,1fr) 116px;gap:36px;align-items:start;padding:28px 0 30px;border-bottom:1px solid var(--line);color:var(--ink);text-decoration:none;transition:background-color .24s var(--ease-out)}
.issue-row:hover{background:linear-gradient(90deg,rgba(255,255,255,.55),rgba(255,255,255,0));text-decoration:none}
.issue-row-no{font-family:var(--serif);font-size:84px;line-height:.86;font-weight:600;color:var(--ink);opacity:.13;font-variant-numeric:tabular-nums;transition:color .24s var(--ease-out),opacity .24s var(--ease-out)}
.issue-row:hover .issue-row-no{color:var(--accent);opacity:.85}
.issue-row.featured .issue-row-no{color:var(--mark);opacity:.85}
.issue-row-main{display:flex;flex-direction:column;gap:11px;min-width:0}
.issue-row-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px;font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums}
.issue-row-label{color:var(--mark);font-weight:600;letter-spacing:.1em}
.issue-row-title{font-family:var(--serif);font-size:26px;line-height:1.34;font-weight:600;letter-spacing:-.014em;margin:0;text-wrap:balance}
.issue-row-desc{font-size:13.5px;line-height:1.78;color:var(--muted);max-width:720px;margin:0;overflow:hidden}
.issue-row-points{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 26px;list-style:none;margin:2px 0 0;padding:0;font-size:12.5px;line-height:1.6;color:var(--muted)}
.issue-row-points li{position:relative;padding-left:14px}
.issue-row-points li::before{content:"";position:absolute;left:0;top:.66em;width:6px;height:1px;background:var(--mark);opacity:.55}
.issue-row-cta{align-self:center;font-size:12.5px;color:var(--faint);letter-spacing:.04em;white-space:nowrap;transition:color .2s}
.issue-row:hover .issue-row-cta{color:var(--accent)}
.guide-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 44px;border-top:1px solid var(--line)}
.guide-row{display:grid;grid-template-columns:30px minmax(0,1fr) auto;gap:4px 12px;align-items:baseline;padding:16px 0 15px;border-bottom:1px solid var(--line);color:var(--ink);text-decoration:none;transition:padding-left .2s var(--ease-out)}
.guide-row:hover{padding-left:6px;text-decoration:none}
.guide-row-no{font-family:var(--serif);font-size:13px;font-style:italic;color:var(--mark);letter-spacing:.06em;font-variant-numeric:tabular-nums}
.guide-row-name{font-family:var(--serif);font-size:18px;font-weight:600;letter-spacing:-.008em}
.guide-row-date{font-size:11.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.guide-row-desc{grid-column:2 / 4;font-size:12.5px;line-height:1.7;color:var(--muted);margin:2px 0 0}
.people-block{margin-top:52px}
.people-block-head{display:flex;align-items:baseline;gap:14px;margin:0 0 12px;padding-bottom:11px;border-bottom:1px solid var(--line)}
.people-block-no{font-family:var(--serif);font-size:13px;font-style:italic;color:var(--mark);letter-spacing:.08em}
.people-block-title{font-family:var(--serif);font-size:20px;font-weight:600;letter-spacing:-.008em;margin:0}
.people-block-count{margin-left:auto;font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums}
.people-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 44px}
.people-row{display:grid;grid-template-columns:26px 118px minmax(0,1fr) auto;gap:10px;align-items:baseline;padding:11px 0;border-bottom:1px solid rgba(120,100,70,.09);font-size:13px;transition:background-color .16s}
.people-row:hover{background:rgba(255,255,255,.4)}
.people-row-no{font-size:10.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.people-row-name{color:var(--ink);font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-decoration:none}
.people-row-name:hover{color:var(--accent)}
.people-row-topic{color:var(--faint);font-size:11.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.people-row-home{font-size:10.5px;color:var(--accent);white-space:nowrap;text-decoration:none;border-bottom:1px solid transparent}
.people-row-home:hover{border-bottom-color:var(--accent-line)}
.people-row-home.is-empty{color:var(--line2);border:0}
.section-title.sub{font-size:19px;color:var(--muted);letter-spacing:0;margin:38px 0 14px;padding-bottom:10px}
.issue-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.issue-card{display:block;background:var(--card-bg);border-radius:var(--r-lg);padding:32px 32px 30px;color:var(--ink);box-shadow:var(--shadow-card);-webkit-backdrop-filter:blur(14px) saturate(1.2);backdrop-filter:blur(14px) saturate(1.2);transition:transform .22s var(--ease-out),box-shadow .22s var(--ease-out)}
.issue-card:hover{transform:translateY(-4px);box-shadow:var(--shadow-card-hover);text-decoration:none}
.issue-card.featured{border-left:3px solid var(--accent);padding-left:27px}
.issue-no{font-size:11.5px;color:var(--accent);font-weight:600;letter-spacing:.16em;text-transform:uppercase}
.issue-card h2{font-family:var(--serif);font-size:24px;font-weight:600;line-height:1.35;margin:10px 0 8px;letter-spacing:-.01em}
.issue-meta{font-size:12.5px;color:var(--faint);margin-bottom:14px;letter-spacing:.02em}
.issue-theme{font-size:15px;line-height:1.7;color:var(--ink);margin:0 0 14px}
.issue-desc{font-size:13.5px;line-height:1.75;color:var(--muted);margin:0 0 16px}
.issue-card ul{margin:0 0 20px;padding-left:1.15em;font-size:13px;line-height:1.7;color:var(--muted)}
.issue-card li{margin:4px 0}
.cta{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--accent);font-weight:600;letter-spacing:.02em;transition:gap .18s var(--ease-out)}
.issue-card:hover .cta{gap:10px}
.guide-card h2{font-size:20px}
.guide-card .issue-meta{margin-bottom:10px}
.quick-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:12px}
.quick-grid a{display:block;background:var(--chip-bg);border:1px solid var(--line);border-radius:var(--r-md);padding:14px 16px;font-size:13.5px;color:var(--ink);transition:border-color .18s,background-color .18s,transform .18s var(--ease-out)}
.quick-grid a:hover{border-color:var(--accent-line);background:var(--accent-soft);color:var(--accent);transform:translateY(-1px)}
.quick-grid a small{display:block;color:var(--faint);font-size:11.5px;margin-top:4px;letter-spacing:.04em}
.site-foot{margin-top:64px;padding-top:24px;border-top:1px solid var(--line);font-size:12.5px;color:var(--faint);display:flex;gap:20px;flex-wrap:wrap}
.site-foot a{color:var(--faint);border-bottom:1px solid transparent}
.site-foot a:hover{color:var(--accent);border-bottom-color:var(--accent-line)}
.notice{background:linear-gradient(180deg,var(--notice-sheen-top),var(--notice-sheen-bottom)),var(--notice-bg);border:1px solid var(--line);border-left:3px solid var(--accent-line);border-radius:var(--r-md);padding:16px 20px;font-size:13.5px;line-height:1.85;color:var(--notice-ink);margin:0 0 4px;box-shadow:0 1px 2px rgba(74,55,30,.04),0 12px 24px -18px rgba(74,55,30,.24)}
.notice a{color:inherit;text-decoration:underline;text-decoration-color:var(--accent-line);text-underline-offset:3px}

.chip{display:inline-block;font-size:12px;line-height:1.5;padding:4px 10px;border:1px solid var(--line2);border-radius:var(--r-pill);color:var(--muted);background:var(--chip-bg);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;text-decoration:none;transition:border-color .16s,color .16s,background-color .16s}
.chip:hover{border-color:var(--accent-line);color:var(--accent);background:var(--accent-soft);text-decoration:none}
.chip.home{border-color:var(--accent-line);color:var(--accent);background:var(--accent-soft)}
.chip::after{content:" \2197";font-size:.78em;color:var(--accent-line);margin-left:.22em}
.index-note{font-size:14px;line-height:1.85;color:var(--muted);margin:0 0 20px;max-width:760px}
.inline-links{margin:16px 0 22px;padding:12px 14px;background:var(--chip-bg);border:1px solid var(--line);border-radius:var(--r-md);display:flex;flex-wrap:wrap;align-items:center;gap:7px}
.inline-label{font-size:11.5px;color:var(--faint);margin-right:4px;letter-spacing:.08em}

/* 阅读器外壳：抽屉、目录、表格、打印与夜间 */
html{scroll-padding-top:calc(var(--topbar-h) + 24px)}
a,button,input{-webkit-tap-highlight-color:transparent}
:focus-visible{outline:2px solid var(--accent-line);outline-offset:3px;border-radius:4px}
.prose h1,.prose h2,.hero h1,.issue-card h2,.section-title{text-wrap:balance}
.issue-no,.issue-meta,.site-foot,.issue-row-no,.issue-row-top,.hero-meta,.people-row-no,.people-block-count,.guide-row-no,.guide-row-date{font-variant-numeric:tabular-nums}
.prose table{scrollbar-width:thin;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}
.table-wrap{position:relative;margin:1.5em 0;border:1px solid var(--line);border-radius:var(--r-md);overflow:hidden}
.table-wrap table{margin:0;border:0}
.table-hint{display:none}
section#tab-thursday,section#handbook,section#resources{scroll-margin-top:calc(var(--topbar-h) + 24px)}
.official-row{margin-top:22px}
.sidebar-sub{font-size:11.5px;color:var(--faint);margin:10px 0 2px;letter-spacing:.06em}
.sidebar-guide{font-weight:600;color:var(--muted)}
.sidebar-guide:hover{color:var(--accent)}
.scrim{display:none}
.toc-fab,.drawer-close{display:none}
.toc-fab-icon{display:flex;flex-direction:column;justify-content:space-between;width:16px;height:12px;flex:none}
.toc-fab-icon i{display:block;height:1.5px;background:currentColor;border-radius:1px}
.fade-in{animation:rise .32s var(--ease-out) both}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

@media (max-width:1040px){
  .hero{grid-template-columns:1fr;gap:34px;align-items:start}
}
@media (max-width:960px){
  html{scroll-padding-top:calc(var(--topbar-h) + env(safe-area-inset-top) + 12px)}
  .topbar{height:calc(var(--topbar-h) + env(safe-area-inset-top));padding-top:env(safe-area-inset-top);padding-left:16px;padding-right:16px;gap:12px}
  .topbar nav{gap:16px}
  .topbar nav a{font-size:13px;min-height:44px;display:inline-flex;align-items:center;border-bottom:0}
  .topbar nav a.nav-old{display:none}
  .menu-toggle{display:none}
  .layout{display:block;padding:0 0 calc(96px + env(safe-area-inset-bottom))}
  .content{border:0;border-radius:0;padding:26px 18px 48px;box-shadow:none;background:transparent}
  .prose{font-size:17px;line-height:1.9}
  .prose>h1:first-child{font-size:29px;line-height:1.34}
  .prose h1{font-size:22px;margin-top:2.3em}
  .prose h2{font-size:19px;margin-top:2.1em}
  .prose h3{font-size:16px}
  .prose blockquote{padding:14px 16px;font-size:15px}
  .prose table{font-size:13.5px}
  .prose ul,.prose ol{padding-left:1.35em}
  .table-hint{display:block;font-size:11.5px;color:var(--faint);margin-top:6px;text-align:right}
  .sidebar{top:calc(var(--topbar-h) + env(safe-area-inset-top));bottom:0;width:min(322px,88vw);border-radius:0 var(--r-lg) var(--r-lg) 0;border-left:0;border-top:0;z-index:59;padding-bottom:calc(20px + env(safe-area-inset-bottom));transform:translate3d(-102%,0,0);transition:transform 260ms var(--ease-out);will-change:transform;box-shadow:var(--shadow-card)}
  .sidebar.open{transform:translate3d(0,0,0)}
  .scrim{display:block;position:fixed;inset:0;background:rgba(20,18,14,.44);opacity:0;pointer-events:none;transition:opacity 200ms var(--ease-in);z-index:58}
  .scrim.show{opacity:1;pointer-events:auto}
  body.nav-open{overflow:hidden}
  .sidebar-head{position:relative;padding-right:44px}
  .drawer-close{display:inline-flex;align-items:center;justify-content:center;position:absolute;top:8px;right:8px;width:44px;height:44px;border:0;background:transparent;color:var(--muted);font-size:22px;line-height:1;cursor:pointer;border-radius:var(--r-sm)}
  .toc a{min-height:44px;display:flex;align-items:center;font-size:13.5px;padding:8px 10px}
  .toc .toc-item{padding-left:18px}
  .filter{font-size:16px;min-height:44px}
  .toc-fab{display:inline-flex;align-items:center;gap:9px;position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:57;min-height:48px;padding:0 18px;border:1px solid var(--line2);border-radius:var(--r-pill);background:var(--surface);color:var(--ink);font-size:13.5px;box-shadow:var(--shadow-pop);cursor:pointer}
  .theme-toggle{right:16px;bottom:calc(84px + env(safe-area-inset-bottom))}
  .to-top{right:16px;bottom:calc(140px + env(safe-area-inset-bottom));width:44px;height:44px}
  .issue-card:hover,.quick-grid a:hover,.guide-row:hover{padding-left:0;transform:none}
  .issue-row:hover{background:none}
  .home{padding:52px 18px calc(104px + env(safe-area-inset-bottom))}
  .hero{margin-bottom:40px}
  .hero h1{font-size:34px}
  .hero .hero-lede{font-size:16.5px}
  .hero-links{gap:12px 18px}
  .hero-spot{padding:26px 22px 24px}
  .issue-row{grid-template-columns:64px minmax(0,1fr);gap:18px;padding:26px 0 28px}
  .issue-row-no{font-size:52px}
  .issue-row-cta{display:none}
  .issue-row-title{font-size:21px}
  .issue-row-points{grid-template-columns:1fr;gap:6px}
  .guide-list{grid-template-columns:1fr}
  .people-list{grid-template-columns:1fr}
  .people-row{grid-template-columns:24px 104px minmax(0,1fr) auto;padding:12px 0}
  .people-block{margin-top:40px}
  .section-title{font-size:26px;margin:64px 0 16px;padding-bottom:14px}
  .content,.sidebar,.issue-card,.hero-spot{-webkit-backdrop-filter:none;backdrop-filter:none}
  .hero-main>*,.hero-spot{animation:none}
  .section-title.sub{font-size:17.5px;margin:34px 0 12px}
  .issue-grid{grid-template-columns:1fr;gap:14px}
  .issue-card{padding:24px 20px}
  .issue-card h2{font-size:21px}
  .person-card{padding:16px}
  .chip{min-height:36px;display:inline-flex;align-items:center;padding:6px 12px;font-size:12.5px}
  .quick-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  .quick-grid a{min-height:52px;padding:12px 13px;font-size:12.8px}
  .inline-links{padding:10px 11px;gap:7px}
  .read-link{min-height:36px;display:inline-flex;align-items:center}
}
@media (max-width:560px){
  .hero h1{font-size:29px}
  .prose{font-size:16.5px}
  .topbar nav a.nav-official,.topbar nav a.nav-repo{display:none}
  .content{padding:22px 16px 42px}
  .prose table{font-size:12.8px}
  .hero-spot{padding:24px 20px 22px}
  .issue-row{grid-template-columns:1fr;gap:14px}
  .issue-row-no{font-size:44px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
}
@media print{
  .topbar,.sidebar,.to-top,.theme-toggle,.toc-fab,.scrim,#progress,.article-foot,.inline-links,.page-atmosphere,.section-no{display:none!important}
  .layout{display:block;padding:0}
  .content{border:0;border-radius:0;box-shadow:none;padding:0;background:none}
  body{background:#fff;color:#000;font-size:12pt}
  .prose h1,.prose h2,.prose h3,.prose>h1:first-child{font-family:var(--serif);color:#000}
  .prose table th{background:#f2f2f2}
  .prose a{text-decoration:underline;color:#000}
  .prose a[target="_blank"]::after{content:" (" attr(href) ")";font-size:.7em;color:#555}
}

/* 夜间：组件只引用 token，覆盖变量即可 */
:root[data-theme="dark"]{
  --paper:#0f131c;--surface:#151b26;--ink:#e9e6dd;--muted:#b6b1a6;--faint:#9a958b;
  --line:#26303d;--line2:#33404f;
  --accent:#82c8dc;--accent-soft:#16242c;--accent-line:#5fa8c4;--mark:#e8a06a;
  --edge:rgba(255,255,255,.08);--warm-line:rgba(255,255,255,.06);
  --card-bg:linear-gradient(180deg,rgba(36,45,58,.92),rgba(22,29,40,.68));
  --card-bg-soft:linear-gradient(180deg,rgba(30,38,50,.9),rgba(19,25,35,.66));
  --chip-bg:#1a2230;--quote-bg:#172029;--quote-ink:#c8c3b8;--th-bg:#1d2632;--row-alt:#171f2a;
  --code-bg:#1b232f;--notice-bg:#17212a;--notice-ink:#c3d3d8;
  --notice-sheen-top:rgba(255,255,255,.04);--notice-sheen-bottom:rgba(255,255,255,0);
  --bar-bg:rgba(15,19,28,.7);
  --bar-shadow:inset 0 -1px 0 var(--warm-line),0 1px 0 rgba(255,255,255,.05);
  --atmosphere:radial-gradient(ellipse 46% 38% at 86% -8%,rgba(150,190,210,.3),rgba(120,160,180,.1) 46%,rgba(20,28,40,0) 72%),radial-gradient(ellipse 40% 34% at 4% 92%,rgba(88,62,120,.26),rgba(88,62,120,0) 68%),radial-gradient(ellipse 52% 40% at 50% 106%,rgba(40,74,96,.32),rgba(40,74,96,0) 70%);
  --grain-opacity:.06;--grain-blend:screen;
  --sel-bg:#0d5b74;--sel-ink:#ffffff;
  --sheen:rgba(255,255,255,.14);
  --shadow-card:inset 0 1px 0 rgba(255,255,255,.06),0 0 0 1px rgba(255,255,255,.06),0 2px 4px rgba(0,0,0,.4),0 16px 32px -16px rgba(0,0,0,.55),0 52px 96px -48px rgba(0,0,0,.6);
  --shadow-card-hover:inset 0 1px 0 rgba(255,255,255,.1),0 0 0 1px rgba(255,255,255,.1),0 2px 4px rgba(0,0,0,.45),0 24px 44px -18px rgba(0,0,0,.6),0 64px 110px -50px rgba(0,0,0,.7);
  --shadow-pop:inset 0 1px 0 rgba(255,255,255,.05),0 0 0 1px rgba(255,255,255,.05),0 2px 4px rgba(0,0,0,.35),0 12px 24px -14px rgba(0,0,0,.5),0 32px 60px -40px rgba(0,0,0,.6);
  --shadow-pop-hover:inset 0 1px 0 rgba(255,255,255,.09),0 0 0 1px rgba(255,255,255,.09),0 2px 4px rgba(0,0,0,.4),0 18px 32px -14px rgba(0,0,0,.55),0 44px 76px -44px rgba(0,0,0,.65);
  color-scheme:dark;
}
:root[data-theme="dark"] .topbar.is-stuck{box-shadow:inset 0 -1px 0 var(--warm-line),0 12px 32px -26px rgba(0,0,0,.75)}
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

  var themeToggle=document.getElementById('themeToggle');
  function isDark(){return document.documentElement.getAttribute('data-theme')==='dark';}
  function paintToggle(){
    if(!themeToggle)return;
    themeToggle.textContent=isDark()?'\u2600':'\u263E';
    themeToggle.setAttribute('aria-pressed',isDark()?'true':'false');
    themeToggle.setAttribute('aria-label',isDark()?'切换到日间模式':'切换到夜间模式');
  }
  if(themeToggle){
    themeToggle.addEventListener('click',function(){
      var next=isDark()?'light':'dark';
      document.documentElement.setAttribute('data-theme',next);
      try{localStorage.setItem('pr-theme',next);}catch(e){}
      paintToggle();
    });
    paintToggle();
  }

  var topbar=document.querySelector('.topbar');
  var heads=Array.prototype.slice.call(document.querySelectorAll('.prose h1[id],.prose h2[id]'));
  function update(){
    var d=document.documentElement;
    var max=d.scrollHeight-d.clientHeight;
    if(progress)progress.style.width=(max>0?(d.scrollTop/max*100):0)+'%';
    if(toTop)toTop.classList.toggle('show',d.scrollTop>420);
    if(topbar)topbar.classList.toggle('is-stuck',d.scrollTop>8);
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
<meta name="theme-color" content="#fffdfa" media="(prefers-color-scheme:light)">
<meta name="theme-color" content="#0f131c" media="(prefers-color-scheme:dark)">
<script>(function(){try{var t=localStorage.getItem('pr-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<link rel="stylesheet" href="./assets/style.css">
</head>
<body>
<div class="page-atmosphere" aria-hidden="true"></div>
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
<button class="theme-toggle" id="themeToggle" type="button" aria-label="切换到夜间模式" aria-pressed="false">☾</button>
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
<meta name="theme-color" content="#fffdfa" media="(prefers-color-scheme:light)">
<meta name="theme-color" content="#0f131c" media="(prefers-color-scheme:dark)">
<script>(function(){try{var t=localStorage.getItem('pr-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
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
<div class="page-atmosphere" aria-hidden="true"></div>
<main class="home">
  <section class="hero">
    <div class="hero-main">
      <p class="eyebrow">Tab 星期四 · 学习手册 · 资源索引</p>
      <h1>公开材料精读</h1>
      <p class="hero-lede">{{HERO}}</p>
      <div class="hero-links">
        <a href="#tab-thursday">活动精读</a>
        <a href="#handbook">学习手册</a>
        <a href="#resources">资源索引</a>
        <a href="{{REPO}}" target="_blank" rel="noopener noreferrer">仓库与 Markdown 原文</a>
      </div>
    </div>
    <aside class="hero-spot" aria-label="本期看点">
{{SPOT}}
    </aside>
  </section>
  <p class="hero-meta">{{HERO_META}}</p>

  <div class="notice">{{NOTICE}}</div>

  <section id="tab-thursday">
    <h2 class="section-title"><span class="section-no">01</span>活动精读 · {{ISSUE_COUNT}}期</h2>
    <p class="index-note">{{ISSUE_NOTE}}</p>
    <div class="issue-list">
{{CARDS}}
    </div>
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
    <h2 class="section-title"><span class="section-no">02</span>学习手册 · {{GUIDE_COUNT}}</h2>
    <p class="index-note">{{GUIDE_NOTE}}</p>
    <div class="guide-list">
{{GUIDE_CARDS}}
    </div>
  </section>

  <section id="resources">
    <h2 class="section-title"><span class="section-no">03</span>资源索引 · {{RESOURCE_PAGE_COUNT}} 页</h2>
    <p class="index-note">{{RESOURCE_NOTE}}</p>
    <section class="issue-grid guide-grid">
{{RESOURCE_CARDS}}
    </section>
  </section>

  <h2 class="section-title"><span class="section-no">04</span>分享者与项目链接</h2>
  <p class="index-note">按官方汇总页整理：每位分享者的个人主页，以及他介绍的项目、源码、幻灯片等链接。点姓名进入本站精读章节，点标签跳转外部站点（新标签页打开）。没有主页或项目链接的会如实标注。</p>
{{INDEX_BLOCKS}}

  <div class="site-foot">
    <span>整理于 {{STAMP}} · 学习笔记性质的重述与分析，非官方记录</span>
    <a href="{{REPO}}" target="_blank" rel="noopener noreferrer">GitHub 仓库</a>
    <a href="https://tabthursday.com" target="_blank" rel="noopener noreferrer">活动官网</a>
  </div>
</main>
<button class="to-top" id="toTop" type="button" aria-label="返回顶部">↑</button>
<button class="theme-toggle" id="themeToggle" type="button" aria-label="切换到夜间模式" aria-pressed="false">☾</button>
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
<meta name="theme-color" content="#fffdfa" media="(prefers-color-scheme:light)">
<meta name="theme-color" content="#0f131c" media="(prefers-color-scheme:dark)">
<script>(function(){try{var t=localStorage.getItem('pr-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<style>
:root{--paper:#fffdfa;--ink:#212427;--muted:#4f5452;--faint:#6f736f;--line:#d8d1c2;--accent:#164e63;--accent-soft:#eaf2f5;--accent-line:#2291bc;--chip:#faf6ec;--card:linear-gradient(180deg,rgba(255,255,255,.82),rgba(255,255,255,.58));--shadow:0 24px 70px -36px rgba(74,55,30,.36);--serif:"Songti SC","Noto Serif SC","Source Han Serif SC","STSong","SimSun",Georgia,serif;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color-scheme:light}
:root[data-theme="dark"]{--paper:#0f131c;--ink:#e9e6dd;--muted:#b6b1a6;--faint:#9a958b;--line:#33404f;--accent:#82c8dc;--accent-soft:#16242c;--accent-line:#5fa8c4;--chip:#1a2230;--card:linear-gradient(180deg,rgba(30,38,50,.86),rgba(21,27,38,.7));--shadow:0 26px 70px -34px rgba(0,0,0,.8);color-scheme:dark}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.85;-webkit-font-smoothing:antialiased}
.wrap{max-width:640px;margin:0 auto;padding:96px 24px}
.code{font-family:var(--serif);font-size:66px;font-weight:600;line-height:1;margin:0 0 20px;color:var(--accent);letter-spacing:-.02em}
h1{font-family:var(--serif);font-size:24px;font-weight:600;margin:0 0 14px;letter-spacing:-.01em}
p{color:var(--muted);margin:0 0 14px}
.box{background:var(--chip);border:1px solid var(--line);border-left:3px solid var(--accent-line);border-radius:12px;padding:15px 18px;margin:22px 0;color:var(--ink);font-size:13.5px}
code{background:var(--chip);border-radius:5px;padding:2px 6px;font-size:.9em;word-break:break-all}
.links{display:flex;gap:14px;flex-wrap:wrap;margin-top:24px}
.links a{display:inline-block;border:1px solid var(--line);background:var(--card);border-radius:12px;padding:10px 16px;color:var(--accent);text-decoration:none;font-size:13.5px;box-shadow:var(--shadow)}
.links a:hover{border-color:var(--accent-line);background:var(--accent-soft)}
.hint{font-size:12.5px;color:var(--faint);margin-top:28px}
::selection{background:#086a8d;color:#fff}
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


def person_row(num: str, person: dict, anchor: str, topic: str, issue_key: str) -> str:
    full = "%s · %s" % (person["name"], topic)
    href = (
        "./issue-%s.html#%s" % (issue_key, html.escape(anchor, quote=True))
        if anchor
        else "./issue-%s.html" % issue_key
    )
    if person.get("homepage"):
        home = (
            '<a class="people-row-home" href="%s" target="_blank" rel="noopener noreferrer">主页 ↗</a>'
            % html.escape(person["homepage"]["url"], quote=True)
        )
    else:
        home = '<span class="people-row-home is-empty">—</span>'
    return (
        '      <div class="people-row">\n'
        '        <span class="people-row-no">%s</span>\n'
        '        <a class="people-row-name" href="%s" title="%s">%s</a>\n'
        '        <span class="people-row-topic" title="%s">%s</span>\n'
        '        %s\n'
        '      </div>'
        % (
            num,
            href,
            html.escape(full, quote=True),
            html.escape(person["name"]),
            html.escape(topic, quote=True),
            html.escape(topic),
            home,
        )
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


def guide_row(idx: int, guide: dict) -> str:
    return (
        '    <a class="guide-row" href="./guide-%s.html">\n'
        '      <span class="guide-row-no">%02d</span>\n'
        '      <span class="guide-row-name">%s</span>\n'
        '      <span class="guide-row-date">复核 %s</span>\n'
        '      <span class="guide-row-desc">%s</span>\n'
        '    </a>'
        % (
            guide["key"],
            idx,
            html.escape(guide["label"]),
            guide["stamp"],
            html.escape(guide["desc"]),
        )
    )


def template_row(idx: int, template: dict) -> str:
    return (
        '    <a class="guide-row" href="./template-%s.html">\n'
        '      <span class="guide-row-no">T%d</span>\n'
        '      <span class="guide-row-name">%s</span>\n'
        '      <span class="guide-row-date">可直接复制 · 复核 %s</span>\n'
        '      <span class="guide-row-desc">%s</span>\n'
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
    for idx, issue in enumerate(ISSUES, 1):
        _, _, cjk = converted[issue["key"]]
        points = "".join("<li>%s</li>" % html.escape(b) for b in issue["bullets"])
        cards.append(
            '    <a class="issue-row%s" href="./issue-%s.html">\n'
            '      <span class="issue-row-no">%s</span>\n'
            '      <div class="issue-row-main">\n'
            '        <div class="issue-row-top"><span class="issue-row-label">%s</span>'
            '<span>%s · %s</span><span>%s</span><span>约 %.1f 万汉字</span></div>\n'
            '        <h3 class="issue-row-title">%s</h3>\n'
            '        <p class="issue-row-desc">%s</p>\n'
            '        <ol class="issue-row-points">%s</ol>\n'
            '      </div>\n'
            '      <span class="issue-row-cta">开始阅读 →</span>\n'
            '    </a>'
            % (
                " featured" if issue["key"] == latest["key"] else "",
                issue["key"], "%02d" % idx,
                html.escape(issue["label"]),
                html.escape(issue["date"]), html.escape(issue["place"]),
                html.escape(issue["count"]),
                cjk / 10000,
                html.escape(issue["theme"]), html.escape(issue["desc"]),
                points,
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
    for idx, issue in enumerate(ISSUES, 1):
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
            cards_html.append(person_row(num, person, hid, topic, issue["key"]))
        total_cards += len(entries)
        index_blocks.append(
            '  <div class="people-block">\n'
            '    <div class="people-block-head"><span class="people-block-no">%02d</span>'
            '<h3 class="people-block-title">%s</h3>'
            '<span class="people-block-count">%s · %d 位</span></div>\n'
            '    <div class="people-list">\n%s\n    </div>\n'
            '  </div>'
            % (
                idx,
                html.escape(issue["label"]),
                html.escape(issue["count"]),
                len(cards_html),
                "\n".join(cards_html),
            )
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

    total_cjk = sum(cjk for _, _, cjk in converted.values())
    spot_points = "".join("<li>%s</li>" % html.escape(b) for b in latest["bullets"])
    spot_html = (
        '<p class="hero-spot-kicker">本期 · #%s · %s</p>'
        '<h2 class="hero-spot-title">%s</h2>'
        '<ol class="hero-spot-list">%s</ol>'
        '<a class="hero-spot-link" href="./issue-%s.html">读%s <span aria-hidden="true">→</span></a>'
        % (
            latest["key"],
            html.escape(latest["date"]),
            html.escape(latest["theme"]),
            spot_points,
            latest["key"],
            html.escape(latest["label"]),
        )
    )
    meta_items = [
        "%d 期" % len(ISSUES),
        "%d 个分享席位" % total_cards,
        "%d 位分享者" % unique_people,
        "%.1f 万汉字" % (total_cjk / 10000),
        "%d 篇手册" % len(GUIDES),
        "%d 页资源索引" % len(RESOURCE_DOCS),
    ]
    meta_html = "".join("<span>%s</span>" % html.escape(x) for x in meta_items)

    home = render(
        HOME_TPL,
        REPO=REPO_URL,
        HOME_DESC=html.escape(home_desc),
        HERO=html.escape(hero),
        SPOT=spot_html,
        HERO_META=meta_html,
        NOTICE=notice,
        NAV=nav_html("home"),
        OFFICIAL_LINKS=official_links,
        CARDS="\n".join(cards),
        GUIDE_CARDS="\n".join(
            [guide_row(i, guide) for i, guide in enumerate(GUIDES, 1)]
            + [template_row(i, template) for i, template in enumerate(TEMPLATES, 1)]
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
