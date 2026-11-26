# 校验 docs/ 下的生成结果：站内链接、锚点、占位符、页面可达性与 Markdown 源文件的相对链接。
# 用法：python scripts/check_site.py

import re
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
RESOURCE_DOCS = ROOT / "resource-grocery" / "zyscj" / "docs"

HREF = re.compile(r'href="([^"]+)"')
ID = re.compile(r'id="([^"]+)"')

EXPECTED = [
    "index.html",
    "404.html",
    "issue-001.html",
    "issue-002.html",
    "issue-003.html",
    "issue-004.html",
    "guide-starter.html",
    "guide-free-resources.html",
    "guide-projects.html",
    "guide-paper-reading.html",
    "guide-ai-boundaries.html",
    "template-notes.html",
    "template-disclosure.html",
    "zyscj.html",
    "zyscj-all.html",
    "zyscj-links.html",
]

EXTERNAL = ("http://", "https://", "mailto:")


def local_target(href: str, current: str) -> str:
    target = href.split("#")[0]
    if not target or target in (".", "./"):
        return current
    return target.lstrip("./")


def main() -> None:
    pages = {path.name: path.read_text(encoding="utf-8") for path in sorted(DOCS.glob("*.html"))}
    ids = {name: set(ID.findall(text)) for name, text in pages.items()}
    problems = []

    for name, text in pages.items():
        for href in HREF.findall(text):
            if href.startswith(EXTERNAL):
                continue
            target = local_target(href, name)
            if target not in pages:
                if not (DOCS / target).exists():
                    problems.append("%s 指向不存在的文件 %s" % (name, href))
                continue
            _, _, frag = href.partition("#")
            if frag and frag not in ids[target]:
                problems.append("%s 指向不存在的锚点 %s" % (name, href))

    for name in EXPECTED:
        if name not in pages:
            problems.append("缺少页面 %s" % name)

    sources = sorted(RESOURCE_DOCS.rglob("*.md"))
    generated = [name for name in pages if name.startswith("zyscj-doc-")]
    if len(sources) != len(generated):
        problems.append("资源页数量不匹配：源文件 %d 个，站点 %d 个" % (len(sources), len(generated)))

    for name, text in pages.items():
        if "{{" in text:
            problems.append("%s 有未替换的占位符" % name)

    seen = {"index.html"}
    queue = deque(["index.html"])
    while queue:
        current = queue.popleft()
        for href in HREF.findall(pages[current]):
            if href.startswith(EXTERNAL):
                continue
            target = local_target(href, current)
            if target.endswith(".html") and target in pages and target not in seen:
                seen.add(target)
                queue.append(target)
    for name in sorted(set(pages) - seen - {"404.html"}):
        problems.append("从首页点不到 %s" % name)

    markdown = (
        sorted(ROOT.glob("*.md"))
        + sorted((ROOT / "handbook").rglob("*.md"))
        + sorted((ROOT / "tab-thursday").glob("*.md"))
    )
    for source in markdown:
        text = source.read_text(encoding="utf-8")
        for link in re.findall(r"\]\((\./[^)#]+)\)", text):
            if not (source.parent / link[2:]).resolve().exists():
                problems.append("%s 的相对链接失效 %s" % (source.relative_to(ROOT), link))

    print("页面 %d 个，首页可达 %d 个，资源页 %d 个" % (len(pages), len(seen & set(pages)), len(generated)))
    if problems:
        print("")
        print("问题 %d 处：" % len(problems))
        for item in problems:
            print("  " + item)
        sys.exit(1)
    print("全部检查通过")


if __name__ == "__main__":
    main()
