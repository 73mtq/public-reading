from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "links.json"
PAGES = {
    "001": "https://tabthursday.com/001.md",
    "002": "https://tabthursday.com/002.md",
    "003": "https://tabthursday.com/003.md",
    "004": "https://tabthursday.com/004.md",
}
EXPECTED = {"001": 18, "002": 21, "003": 22, "004": 21}
UA = "Mozilla/5.0 (compatible; public-reading-link-builder/1.1)"
MEDIA_HOST = "media.jant.me"

IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\((https?://[^)\s]+)\)")
ORDERED_RE = re.compile(r"^\d+\. \*\*(.+?)\*\*(.*)$")
BULLET_RE = re.compile(r"^\s+-\s+(.*)$")
HOMEPAGE_RE = re.compile(r"（\[([^\]]*)\]\((https?://[^)]+)\)）")
DOMAIN_LABEL_RE = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$")
FOOTER_MARKERS = ("以上是 Tab 星期四第", "\n> 身边有一群")


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return text


def body_after_cover(text: str) -> str:
    marker = "<!--more-->"
    if marker in text:
        return text.split(marker, 1)[1]
    return text


def cut_footer(text: str) -> str:
    cut = len(text)
    for marker in FOOTER_MARKERS:
        pos = text.find(marker)
        if pos != -1:
            cut = min(cut, pos)
    return text[:cut]


def normalize(url: str) -> str:
    url = url.strip().rstrip("/")
    url = re.sub(r"^https?://", "", url, flags=re.I)
    url = re.sub(r"^www\.", "", url, flags=re.I)
    return url.lower()


def is_media(url: str) -> bool:
    return MEDIA_HOST in normalize(url).split("/")[0]


def is_domain_label(label: str) -> bool:
    return bool(DOMAIN_LABEL_RE.fullmatch(label.strip()))


def clean_label(label: str) -> str:
    label = re.sub(r"\\([\\`*_{}\[\]()#+\-.!])", r"\1", label)
    return html.unescape(label).strip()


def collect(pairs, skip_urls: set[str]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for label, url in pairs:
        label = clean_label(label)
        if not label or not url.startswith(("http://", "https://")):
            continue
        if is_media(url):
            continue
        n = normalize(url)
        if n in seen or n in skip_urls:
            continue
        host = n.split("/")[0]
        if is_domain_label(label) and any(s.split("/")[0] == host for s in seen):
            continue
        seen.add(n)
        out.append({"label": label, "url": url})
    return out


def parse_ordered(text: str) -> list[dict]:
    text = cut_footer(text)
    people: list[dict] = []
    current = None
    for line in text.splitlines():
        m = ORDERED_RE.match(line)
        if m:
            tail = m.group(2)
            hm = HOMEPAGE_RE.search(tail)
            homepage = None
            if hm:
                homepage = {"label": clean_label(hm.group(1)), "url": hm.group(2)}
            current = {"name": m.group(1).strip(), "homepage": homepage, "raw": []}
            people.append(current)
            continue
        bm = BULLET_RE.match(line)
        if bm and current is not None:
            current["raw"].append(bm.group(1))
    for person in people:
        block = "\n".join(person.pop("raw"))
        pairs = LINK_RE.findall(IMAGE_RE.sub("", block))
        skip = {normalize(person["homepage"]["url"])} if person["homepage"] else set()
        person["links"] = collect(pairs, skip)
    return people


def parse_sections(text: str) -> list[dict]:
    text = cut_footer(text)
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    people: list[dict] = []
    for chunk in parts:
        section = re.split(r"^## ", chunk, flags=re.M)[0]
        nl = section.find("\n")
        if nl == -1:
            continue
        body = IMAGE_RE.sub("", section[nl + 1:])
        hm = re.search(r"主页：\s*\[([^\]]*)\]\((https?://[^)]+)\)", body)
        homepage = None
        if hm:
            homepage = {"label": clean_label(hm.group(1)), "url": hm.group(2)}
        pairs = LINK_RE.findall(body)
        skip = {normalize(homepage["url"])} if homepage else set()
        people.append({"name": section[:nl].strip(), "homepage": homepage, "links": collect(pairs, skip)})
    return people


def main() -> None:
    data = {}
    for key, url in PAGES.items():
        page = body_after_cover(strip_front_matter(fetch(url)))
        people = parse_ordered(page) if key == "001" else parse_sections(page)
        if len(people) != EXPECTED[key]:
            raise RuntimeError(
                "issue %s: expected %d people, parsed %d (%s)" % (key, EXPECTED[key], len(people), url)
            )
        for i, person in enumerate(people, 1):
            if not person["name"]:
                raise RuntimeError("issue %s: empty name at position %d" % (key, i))
        data[key] = people
        total = sum(len(p["links"]) for p in people)
        homes = sum(1 for p in people if p["homepage"])
        print("issue %s: %d people, %d homepages, %d links" % (key, len(people), homes, total))
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT.name, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
