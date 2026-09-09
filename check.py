#!/usr/bin/env python3
"""
Pre-upload checks for docs/.

    py check.py

Exits non-zero if anything is wrong, so it can gate an upload.
The font check shells out to subset-fonts.py so both share one definition of
"which characters does this site need".
"""

import glob
import io
import os
import re
import struct
import subprocess
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "docs")

PAGES_EN = ["index.html", "misc.html", "ms.html"]
PAGES_ZH = ["index-zh.html", "misc-zh.html", "ms-zh.html"]
ALL_PAGES = PAGES_EN + PAGES_ZH

VOID = {"br", "img", "meta", "link", "hr", "input", "source", "area", "base",
        "col", "embed", "param", "track", "wbr", "path", "rect", "circle",
        "polygon", "polyline", "use", "stop", "ellipse", "line"}

problems = []
notes = []


def fail(section, msg):
    problems.append((section, msg))


def read(page):
    return io.open(os.path.join(SITE, page), encoding="utf-8").read()


def visible(html):
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", "", html)


# --- 1. fonts -------------------------------------------------------------- #

def check_fonts():
    r = subprocess.run([sys.executable, os.path.join(HERE, "subset-fonts.py"), "--check"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        for line in (r.stdout or "").splitlines():
            if line.strip().startswith("-"):
                fail("字体", line.strip()[2:])
        if not any(p[0] == "字体" for p in problems):
            fail("字体", (r.stdout or r.stderr or "").strip()[:300])
    else:
        m = re.search(r"pages need (\d+) glyphs", r.stdout or "")
        notes.append(f"字体覆盖 {m.group(1) if m else '?'} 个中文字形")


# --- 2. tag structure ------------------------------------------------------ #

class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"多余的 </{tag}> 第 {self.getpos()[0]} 行")
            return
        if self.stack[-1][0] != tag:
            top, pos = self.stack[-1]
            self.errors.append(
                f"第 {self.getpos()[0]} 行的 </{tag}> 对不上，栈顶是第 {pos[0]} 行的 <{top}>")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
            return
        self.stack.pop()


def check_structure():
    for page in ALL_PAGES:
        p = Structure()
        p.feed(read(page))
        for e in p.errors:
            fail("结构", f"{page}: {e}")
        for tag, pos in p.stack:
            fail("结构", f"{page}: <{tag}> 第 {pos[0]} 行未闭合")


# --- 3. image dimensions --------------------------------------------------- #

def dims(path):
    with open(path, "rb") as f:
        head = f.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                b = f.read(1)
                if not b:
                    return None
                if b != b"\xff":
                    continue
                while b == b"\xff":
                    b = f.read(1)
                m = b[0]
                if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                    continue
                ln = struct.unpack(">H", f.read(2))[0]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                         0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(1)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                f.seek(ln - 2, 1)
    return None


def check_images():
    checked = 0
    for page in ALL_PAGES:
        for tag in re.findall(r"<img[^>]*>", read(page)):
            src = re.search(r'src="([^"]+)"', tag)
            w = re.search(r'width="(\d+)"', tag)
            h = re.search(r'height="(\d+)"', tag)
            if not src:
                continue
            path = os.path.join(SITE, src.group(1))
            if not os.path.isfile(path):
                continue
            if not (w and h):
                fail("图片", f"{page}: {src.group(1)} 缺 width/height")
                continue
            actual = dims(path)
            if not actual:
                continue
            declared = int(w.group(1)) / int(h.group(1))
            real = actual[0] / actual[1]
            if abs(declared - real) > 0.01:
                fail("图片", f"{page}: {src.group(1)} 声明 "
                             f"{w.group(1)}x{h.group(1)}，实际 {actual[0]}x{actual[1]}")
            checked += 1
    notes.append(f"图片宽高比 {checked} 处一致")


# --- 4. links and assets --------------------------------------------------- #

def ids_of(page):
    return set(re.findall(r'\sid="([^"]+)"', read(page)))


def check_links():
    total = 0
    id_cache = {}
    for page in ALL_PAGES:
        html = read(page)
        # local references: strip the #fragment before testing the file,
        # then check the fragment resolves to an id on the target page
        for ref in sorted(set(re.findall(r'(?:href|src)="([^"][^":]*)"', html))):
            if ref.startswith(("mailto:", "//", "#")) and not ref.startswith("#"):
                continue
            path, _, frag = ref.partition("#")
            path = path.split("?")[0]
            target = page if path == "" else path
            if path:
                total += 1
                if not os.path.isfile(os.path.join(SITE, path)):
                    fail("链接", f"{page}: 指向不存在的 {path}")
                    continue
            if frag:
                if target not in id_cache:
                    id_cache[target] = ids_of(target) if os.path.isfile(
                        os.path.join(SITE, target)) else set()
                if frag not in id_cache[target]:
                    fail("链接", f"{page}: 锚点 #{frag} 在 {target} 上不存在")
        for abs_ref in set(re.findall(r'(?:href|src)="(/[^/][^"]*)"', html)):
            fail("链接", f"{page}: 绝对路径 {abs_ref}（子目录部署下会 404）")
        if "github.io" in html:
            fail("链接", f"{page}: 仍有指回 github.io 的链接")
        if "〔待译" in visible(html):
            n = visible(html).count("〔待译")
            fail("翻译", f"{page}: 还有 {n} 处未翻译的占位")
    # font files referenced by the stylesheet
    css = io.open(os.path.join(SITE, "assets", "css", "site.css"), encoding="utf-8").read()
    for f in re.findall(r'url\("\.\./fonts/([^"]+)"\)', css):
        total += 1
        if not os.path.isfile(os.path.join(SITE, "assets", "fonts", f)):
            fail("链接", f"site.css: 指向不存在的字体 {f}")
    notes.append(f"链接与资源 {total} 处可达")


# --- 5. orphans ------------------------------------------------------------ #

def check_orphans():
    referenced = set()
    for page in ALL_PAGES:
        referenced |= set(re.findall(r'(?:href|src)="([^"#?][^":]*)"', read(page)))
    for folder in ("files", "images", os.path.join("images", "MS")):
        d = os.path.join(SITE, folder)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            rel = os.path.join(folder, name).replace("\\", "/")
            if rel not in referenced:
                fail("孤儿文件", f"{rel} 在磁盘上但没有任何页面引用")


# --- 6. bilingual consistency --------------------------------------------- #

def nav_of(page):
    html = read(page)
    m = re.search(r'<nav class="mainnav">(.*?)</nav>', html, flags=re.S)
    return m.group(1) if m else ""


def check_bilingual():
    for en, zh in zip(PAGES_EN, PAGES_ZH):
        if not os.path.isfile(os.path.join(SITE, zh)):
            fail("中英一致", f"{en} 没有对应的 {zh}")
            continue
        n_en = len(re.findall(r"<a ", nav_of(en)))
        n_zh = len(re.findall(r"<a ", nav_of(zh)))
        if n_en != n_zh:
            fail("中英一致", f"导航项数不同：{en} {n_en} 个，{zh} {n_zh} 个")
        for page, want in ((en, zh), (zh, en)):
            m = re.search(r'class="langswitch" href="([^"]+)"', nav_of(page))
            if not m:
                fail("中英一致", f"{page}: 找不到语言切换按钮")
            elif m.group(1) != want:
                fail("中英一致", f"{page}: 切换按钮指向 {m.group(1)}，应为 {want}")
        for page in (en, zh):
            cur = re.findall(r'aria-current="page"', nav_of(page))
            if page.startswith("index") and cur:
                fail("中英一致", f"{page}: 首页不该有 aria-current")
            if not page.startswith("index") and len(cur) != 1:
                fail("中英一致", f"{page}: aria-current 有 {len(cur)} 处，应为 1 处")
        # the current-page marker must sit on the link to this very page
        if not en.startswith("index"):
            for page in (en, zh):
                m = re.search(r'<a href="([^"]+)" aria-current="page"', nav_of(page))
                if m and m.group(1) != page:
                    fail("中英一致", f"{page}: 高亮的是 {m.group(1)}，应为自己")
    notes.append(f"中英页面 {len(PAGES_EN)} 对")


# --- run ------------------------------------------------------------------- #

def check_in_sync():
    """docs/*.html must be what src/ produces, or an edit is about to be lost."""
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "--diff"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout or ""
    drifted = [ln.strip()[3:].strip() for ln in out.splitlines() if ln.startswith("  ~ ")]
    if drifted:
        for f in drifted:
            fail("源同步", f"docs/{f} 和 src/ 不一致 —— 你可能改错了地方"
                           "（应该改 src/，docs/ 是产物）")
        fail("源同步", "看差异：py build.py --diff　；确认后重新生成：./build.sh")
    else:
        notes.append("docs/ 与 src/ 同步")


if __name__ == "__main__":
    for fn in (check_in_sync, check_fonts, check_structure, check_images,
               check_links, check_orphans, check_bilingual):
        fn()

    # CNAME and .nojekyll only mean anything to GitHub Pages; they are inert
    # on the school server, so they stay in the count but are called out.
    n_files = sum(len(fs) for _, _, fs in os.walk(SITE))
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(SITE) for f in fs)

    print()
    for n in notes:
        print(f"  ✓ {n}")
    print(f"  ✓ 上传清单 {n_files} 个文件，{size // 1024 // 1024} MB")

    if problems:
        print(f"\n  发现 {len(problems)} 个问题：\n")
        last = None
        for section, msg in problems:
            if section != last:
                print(f"  [{section}]")
                last = section
            print(f"     - {msg}")
        print("\n  修好之后重新跑一次。")
        sys.exit(1)

    print("\n  全部通过，可以上传。")
    sys.exit(0)
