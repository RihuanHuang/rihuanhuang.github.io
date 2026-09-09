#!/usr/bin/env python3
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
                fail("fonts", line.strip()[2:])
        if not any(p[0] == "fonts" for p in problems):
            fail("fonts", (r.stdout or r.stderr or "").strip()[:300])
    else:
        m = re.search(r"pages need (\d+) glyphs", r.stdout or "")
        notes.append(f"fonts cover {m.group(1) if m else '?'} CJK glyphs")


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
            self.errors.append(f"stray </{tag}> on line {self.getpos()[0]}")
            return
        if self.stack[-1][0] != tag:
            top, pos = self.stack[-1]
            self.errors.append(
                f"</{tag}> on line {self.getpos()[0]} does not match <{top}> opened on line {pos[0]}")
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
            fail("structure", f"{page}: {e}")
        for tag, pos in p.stack:
            fail("structure", f"{page}: <{tag}> opened on line {pos[0]} is never closed")


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
                fail("images", f"{page}: {src.group(1)} has no width/height")
                continue
            actual = dims(path)
            if not actual:
                continue
            declared = int(w.group(1)) / int(h.group(1))
            real = actual[0] / actual[1]
            if abs(declared - real) > 0.01:
                fail("images", f"{page}: {src.group(1)} declares "
                             f"{w.group(1)}x{h.group(1)}, file is {actual[0]}x{actual[1]}")
            checked += 1
    notes.append(f"{checked} image aspect ratios match")


# --- 4. links and assets --------------------------------------------------- #

def ids_of(page):
    return set(re.findall(r'\sid="([^"]+)"', read(page)))


def check_links():
    total = 0
    id_cache = {}
    for page in ALL_PAGES:
        html = read(page)
        for ref in sorted(set(re.findall(r'(?:href|src)="([^"][^":]*)"', html))):
            if ref.startswith(("mailto:", "//", "#")) and not ref.startswith("#"):
                continue
            path, _, frag = ref.partition("#")
            path = path.split("?")[0]
            target = page if path == "" else path
            if path:
                total += 1
                if not os.path.isfile(os.path.join(SITE, path)):
                    fail("links", f"{page}: links to missing {path}")
                    continue
            if frag:
                if target not in id_cache:
                    id_cache[target] = ids_of(target) if os.path.isfile(
                        os.path.join(SITE, target)) else set()
                if frag not in id_cache[target]:
                    fail("links", f"{page}: #{frag} matches no id on {target}")
        for abs_ref in set(re.findall(r'(?:href|src)="(/[^/][^"]*)"', html)):
            fail("links", f"{page}: absolute path {abs_ref} (404s under a subpath)")
        if "github.io" in html:
            fail("links", f"{page}: still links back to github.io")
        if "〔待译" in visible(html):
            n = visible(html).count("〔待译")
            fail("translation", f"{page}: {n} untranslated placeholders left")
    css = io.open(os.path.join(SITE, "assets", "css", "site.css"), encoding="utf-8").read()
    for f in re.findall(r'url\("\.\./fonts/([^"]+)"\)', css):
        total += 1
        if not os.path.isfile(os.path.join(SITE, "assets", "fonts", f)):
            fail("links", f"site.css: points at missing font {f}")
    notes.append(f"{total} references resolve")


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
                fail("orphans", f"{rel} is on disk but no page references it")


# --- 6. bilingual consistency --------------------------------------------- #

def nav_of(page):
    html = read(page)
    m = re.search(r'<nav class="mainnav">(.*?)</nav>', html, flags=re.S)
    return m.group(1) if m else ""


def check_bilingual():
    for en, zh in zip(PAGES_EN, PAGES_ZH):
        if not os.path.isfile(os.path.join(SITE, zh)):
            fail("bilingual", f"{en} has no counterpart {zh}")
            continue
        n_en = len(re.findall(r"<a ", nav_of(en)))
        n_zh = len(re.findall(r"<a ", nav_of(zh)))
        if n_en != n_zh:
            fail("bilingual", f"nav item count differs: {en} has {n_en}, {zh} has {n_zh}")
        for page, want in ((en, zh), (zh, en)):
            m = re.search(r'class="langswitch" href="([^"]+)"', nav_of(page))
            if not m:
                fail("bilingual", f"{page}: no language switch link")
            elif m.group(1) != want:
                fail("bilingual", f"{page}: language switch points at {m.group(1)}, expected {want}")
        for page in (en, zh):
            cur = re.findall(r'aria-current="page"', nav_of(page))
            if page.startswith("index") and cur:
                fail("bilingual", f"{page}: the home page should not carry aria-current")
            if not page.startswith("index") and len(cur) != 1:
                fail("bilingual", f"{page}: {len(cur)} aria-current markers, expected 1")
        if not en.startswith("index"):
            for page in (en, zh):
                m = re.search(r'<a href="([^"]+)" aria-current="page"', nav_of(page))
                if m and m.group(1) != page:
                    fail("bilingual", f"{page}: aria-current marks {m.group(1)}, expected the page itself")
    notes.append(f"{len(PAGES_EN)} EN/ZH page pairs")


# --- run ------------------------------------------------------------------- #

def check_in_sync():
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "--diff"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout or ""
    drifted = [ln.strip()[3:].strip() for ln in out.splitlines() if ln.startswith("  ~ ")]
    if drifted:
        for f in drifted:
            fail("source", f"docs/{f} does not match src/ -- edit src/, "
                           "docs/ is generated")
        fail("source", "see the diff with py build.py --diff, then rebuild with ./build.sh")
    else:
        notes.append("docs/ matches src/")


if __name__ == "__main__":
    for fn in (check_in_sync, check_fonts, check_structure, check_images,
               check_links, check_orphans, check_bilingual):
        fn()

    n_files = sum(len(fs) for _, _, fs in os.walk(SITE))
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(SITE) for f in fs)

    print()
    for n in notes:
        print(f"  ✓ {n}")
    print(f"  ✓ upload set: {n_files} files, {size // 1024 // 1024} MB")

    if problems:
        print(f"\n  {len(problems)} problem(s):\n")
        last = None
        for section, msg in problems:
            if section != last:
                print(f"  [{section}]")
                last = section
            print(f"     - {msg}")
        print("\n  fix these and run again.")
        sys.exit(1)

    print("\n  all checks passed.")
    sys.exit(0)
