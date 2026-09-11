#!/usr/bin/env python3
import argparse
import glob
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "docs")
FONT_DIR = os.path.join(SITE, "assets", "fonts")
CSS = os.path.join(SITE, "assets", "css", "site.css")
CACHE = os.path.join(os.environ.get("TEMP", "/tmp"), "sourcehan")
BASE = "https://github.com/adobe-fonts"

FONTS = [
    ("source-han-serif", "SourceHanSerifSC-SemiBold"),
    ("source-han-sans", "SourceHanSansSC-Regular"),
    ("source-han-sans", "SourceHanSansSC-Bold"),
]

CJK = (
    (0x4E00, 0x9FFF),   # unified ideographs
    (0x3000, 0x303F),   # CJK punctuation
    (0xFF00, 0xFFEF),   # fullwidth forms
    (0x2000, 0x206F),   # general punctuation (— … “ ” etc.)
)


def wanted_chars():
    seen = set()
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        s = io.open(path, encoding="utf-8").read()
        s = re.sub(r"<script.*?</script>", "", s, flags=re.S)
        s = re.sub(r"<style.*?</style>", "", s, flags=re.S)
        s = re.sub(r"<[^>]+>", "", s)
        for ch in s:
            o = ord(ch)
            if any(lo <= o <= hi for lo, hi in CJK):
                seen.add(ch)
    return "".join(sorted(seen))


def charset_hash(chars):
    return hashlib.sha256(chars.encode("utf-8")).hexdigest()[:8]


def css_text():
    return io.open(CSS, encoding="utf-8").read()


def css_font_urls():
    return re.findall(r'url\("\.\./fonts/([^"]+\.woff2)"\)', css_text())


def cmap_of(path):
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    chars = set()
    for t in font["cmap"].tables:
        chars |= set(t.cmap.keys())
    return chars


# --------------------------------------------------------------------------- #

def check():
    chars = wanted_chars()
    h = charset_hash(chars)
    print(f"pages need {len(chars)} glyphs  (charset hash {h})")

    problems = []
    referenced = css_font_urls()
    if len(referenced) != len(FONTS):
        problems.append(f"site.css references {len(referenced)} font files, expected {len(FONTS)}")

    for name in referenced:
        path = os.path.join(FONT_DIR, name)
        if not os.path.isfile(path):
            problems.append(f"site.css points at a missing file: {name}")
            continue
        missing = [c for c in chars if ord(c) not in cmap_of(path)]
        if missing:
            problems.append(f"{name} is missing {len(missing)} glyph(s): {''.join(missing)}")
        else:
            print(f"  OK  {name}")

    stale = [f for f in os.listdir(FONT_DIR)
             if f.endswith(".woff2") and f not in referenced]
    for f in stale:
        problems.append(f"unused font file left behind: {f}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        print("\nrun:  py subset-fonts.py")
        return 1

    print("\nall good - fonts cover every character on the pages")
    return 0


def build():
    chars = wanted_chars()
    h = charset_hash(chars)
    print(f"==> {len(chars)} glyphs, charset hash {h}")

    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(FONT_DIR, exist_ok=True)
    charfile = os.path.join(CACHE, "charset.txt")
    io.open(charfile, "w", encoding="utf-8").write(chars)

    produced = []
    for repo, name in FONTS:
        otf = os.path.join(CACHE, name + ".otf")
        if not os.path.isfile(otf):
            url = f"{BASE}/{repo}/raw/release/OTF/SimplifiedChinese/{name}.otf"
            print(f"    downloading {name}.otf")
            urllib.request.urlretrieve(url, otf)

        out_name = f"{name}.subset.{h}.woff2"
        out = os.path.join(FONT_DIR, out_name)
        subprocess.run(
            [sys.executable, "-m", "fontTools.subset", otf,
             f"--text-file={charfile}", "--flavor=woff2",
             "--layout-features=", "--no-hinting", "--desubroutinize",
             f"--output-file={out}"],
            check=True,
        )
        produced.append(out_name)
        print(f"    {out_name}  {os.path.getsize(out) // 1024} KB")

    css = css_text()
    for (_, name), out_name in zip(FONTS, produced):
        css = re.sub(
            rf'url\("\.\./fonts/{re.escape(name)}\.subset\.[^"]*\.woff2"\)|'
            rf'url\("\.\./fonts/{re.escape(name)}\.subset\.woff2"\)',
            f'url("../fonts/{out_name}")',
            css,
        )
    io.open(CSS, "w", encoding="utf-8", newline="\n").write(css)
    print("==> site.css updated")

    for f in sorted(os.listdir(FONT_DIR)):
        if f.endswith(".woff2") and f not in produced:
            os.remove(os.path.join(FONT_DIR, f))
            print(f"    removed stale {f}")

    total = sum(os.path.getsize(os.path.join(FONT_DIR, f)) for f in produced)
    print(f"==> done, {total // 1024} KB total")
    print(f"    source OTFs cached in {CACHE} (~55 MB, safe to delete)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify only, do not rebuild")
    args = ap.parse_args()
    sys.exit(check() if args.check else build())
