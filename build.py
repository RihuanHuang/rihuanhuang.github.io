#!/usr/bin/env python3
import argparse
import difflib
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PART = os.path.join(SRC, "partials")
PAGES = os.path.join(SRC, "pages")
OUT = os.path.join(HERE, "docs")

SKELETON = """<!doctype html>
<html lang="{htmllang}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{descmeta}<link rel="stylesheet" href="assets/css/site.css">
</head>

<body>

{header}

<div class="wrap">

  {banner}
</div>
<div class="{layoutclass}">

  {profile}

  {main}
{toc}
</div>

{footer}

{scripts}

</body>
</html>
"""


def partial(name):
    return io.open(os.path.join(PART, name), encoding="utf-8").read().rstrip("\n")


def parse_page(path):
    raw = io.open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, flags=re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def render(filename):
    meta, main = parse_page(os.path.join(PAGES, filename))
    zh = "-zh" in filename
    lg = "zh" if zh else "en"
    key = filename.replace("-zh", "").replace(".html", "")

    home = "" if key == "index" else ("index-zh.html" if zh else "index.html")
    other = filename.replace("-zh", "") if zh else filename.replace(".html", "-zh.html")

    header = partial(f"header.{lg}.html")
    header = (header
              .replace("{{home}}", home)
              .replace("{{other}}", other)
              .replace("{{cur_misc}}", ' aria-current="page"' if key == "misc" else "")
              .replace("{{cur_ms}}", ' aria-current="page"' if key == "ms" else ""))

    profile_name = "profile-ms" if meta.get("profile") == "ms" else "profile"

    has_toc = meta.get("toc") == "yes"
    toc = "\n  " + partial(f"toc.{lg}.html") + "\n" if has_toc else ""
    scripts = partial("scripts.html") if has_toc else ""

    desc = meta.get("desc", "")
    descmeta = f'<meta name="description" content="{desc}">\n' if desc else ""

    return SKELETON.format(
        htmllang="zh-Hans" if zh else "en",
        title=meta.get("title", ""),
        descmeta=descmeta,
        header=header,
        banner=partial("banner-full.html" if meta.get("banner") == "full"
                       else "banner-slim.html"),
        layoutclass=("wrap layout" if meta.get("layout") == "3col"
                     else "wrap layout layout--2col layout--slim"),
        profile=partial(f"{profile_name}.{lg}.html"),
        main=main,
        toc=toc,
        footer=partial(f"footer.{lg}.html"),
        scripts=scripts,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true",
                    help="compare only, do not write")
    args = ap.parse_args()

    pages = sorted(f for f in os.listdir(PAGES) if f.endswith(".html"))
    changed = 0
    for f in pages:
        new = render(f)
        dest = os.path.join(OUT, f)
        old = io.open(dest, encoding="utf-8").read() if os.path.isfile(dest) else ""
        if new == old:
            print(f"  =  {f}")
            continue
        changed += 1
        if args.diff:
            print(f"  ~  {f}")
            d = list(difflib.unified_diff(
                old.splitlines(), new.splitlines(),
                "docs/" + f, "build", lineterm="", n=1))
            for line in d[:40]:
                print("       " + line)
            if len(d) > 40:
                print(f"       ... {len(d) - 40} more lines")
        else:
            io.open(dest, "w", encoding="utf-8", newline="\n").write(new)
            print(f"  ->  {f}")

    if args.diff:
        print(f"\n{changed} page(s) differ from src/" if changed
              else "\ndocs/ is identical to src/")
    else:
        print(f"\nbuilt {len(pages)} pages, {changed} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
