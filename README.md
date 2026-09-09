# rihuan.me

Source for my personal academic homepage — [rihuan.me](https://rihuan.me/).

Plain static HTML. No Jekyll, no bundler, no framework, no external CDN, and no
JavaScript files: the only script is about fifteen inlined lines that highlight the
current section in the sidebar. A tiny Python script assembles the pages from shared
partials so the header, sidebar and footer exist in one place each.

Every path is relative, so the same tree works at a domain root and under a subpath —
it is published here with GitHub Pages and also uploaded by hand to my university's
homepage service.

```
src/partials/   header, sidebar, banners, section nav, footer
src/pages/      one file per page: a few lines of front matter + its own <main>
docs/           the generated site — this is what gets published
build.py        assembles docs/ from src/
check.py        pre-publish checks (dead links, tag structure, image dimensions, …)
subset-fonts.py cuts the Chinese webfonts down to the glyphs actually used
```

## Using it for your own site

Nothing here is specific to my setup beyond the content itself, so a fork is mostly a
matter of replacing text and images.

```bash
git clone https://github.com/<you>/<your-fork>.git
cd <your-fork>

# 1. put your own content in
#    - src/pages/*.html      the text of each page
#    - src/partials/*.html   name, links, sidebar, footer
#    - docs/images/, docs/files/   your photos and PDFs
#    - docs/CNAME            your domain, or delete it
#    - docs/assets/css/site.css    colors live in :root at the top

# 2. build and check
python build.py
python check.py

# 3. publish
git add -A && git commit -m "..." && git push
```

Then in **Settings → Pages**, set the source to your default branch with the **`/docs`**
folder. Everything outside `docs/` — the scripts, `src/`, this file — stays in the repo
without being served as a web page.

`python check.py` is worth running before every push. It catches the failures that are
invisible in a browser: an unclosed tag the parser silently repairs, an `<img>` whose
declared dimensions do not match the file (which makes the page jump while lazy-loading),
a dead link or a `#fragment` that matches no `id`, an asset nothing references any more,
and — if you write Chinese — characters missing from the font subset.

### Preview

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File preview.ps1
```

Serves `docs/` at `http://localhost:8765/subpath/`. The extra path segment is
deliberate: any absolute path that slipped in will 404 immediately instead of working
locally and breaking once deployed.

### If you write Chinese

The pages ship their own Chinese webfonts rather than relying on whatever the visitor's
system has. `subset-fonts.py` downloads Source Han Sans/Serif and cuts them down to the
characters your pages actually use — roughly 56 MB of source fonts becomes about 156 KB
of WOFF2, with a content hash in each filename so a stale copy can never be cached.

Re-run it after adding Chinese text, or the new characters will silently fall back to a
system font mid-sentence:

```bash
pip install fonttools brotli
python subset-fonts.py
```

The bundled subsets are [Source Han](https://github.com/adobe-fonts), licensed under the
SIL Open Font License 1.1.

## Reuse

The code — the build scripts, the CSS, the page structure — is yours to take and adapt,
no attribution needed. The written content, photographs and PDFs are not: please replace
them with your own.
