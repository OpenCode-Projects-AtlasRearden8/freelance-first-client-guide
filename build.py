#!/usr/bin/env python3
"""Build a static HTML site from the Markdown guides in docs/.

Usage:
    python3 build.py          # build site/ from docs/
    python3 build.py --test   # run self-tests and exit
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
SITE = ROOT / "site"

TITLE = "The First-Client Survival Kit"
SUBTITLE = "A plain-English manual for landing and surviving your first freelance client"
FOOTER = (
    "Education only — never legal, medical, or tax advice. "
    "Published as an Asdale Dynamics, LLC project. MIT licensed."
)

NAV = [
    ("index", "Welcome"),
    ("00-start-here", "Start here"),
    ("01-services-one-pager", "1 - One-pager"),
    ("02-quoting-projects", "2 - Quoting"),
    ("03-simple-contracts", "3 - Contracts"),
    ("04-invoices-that-get-paid", "4 - Invoices"),
    ("05-scope-guarding", "5 - Scope"),
    ("06-testimonials", "6 - Testimonials"),
    ("07-when-llc-makes-sense", "7 - LLC"),
    ("quote-worksheet", "Quote worksheet"),
    ("invoice-checklist", "Invoice checklist"),
    ("glossary", "Glossary"),
]

BLOCK_TOKEN = "\x02BLOCK{}\x03"
BLOCK_RE = re.compile(r"\x02BLOCK(\d+)\x03")

# ---------------------------------------------------------------- markdown ---

def _split_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_table_sep(line):
    row = _split_table_row(line)
    return 2 <= len(row) <= 8 and all(re.fullmatch(r":?-{3,}:?", c) for c in row)


def _extract_block_spans(text):
    """Stash fenced code blocks and :::disclaimer blocks behind tokens so
    inline formatting does not touch them. Returns (text, spans)."""
    spans = []

    def stash(match):
        spans.append(match.group(0))
        return BLOCK_TOKEN.format(len(spans) - 1)

    text = re.sub(r"```.*?```", stash, text, flags=re.S)
    text = re.sub(r":::[a-z-]+.*?(?=\n\n|$)", stash, text, flags=re.S)
    return text, spans


def render_block_spans(spans, token):
    def one(match):
        span = spans[int(match.group(1))]
        if span.startswith("```"):
            body = re.sub(r"^```\w*\n?", "", span).removesuffix("```")
            return f"<pre><code>{html.escape(body.rstrip())}</code></pre>"
        lines = [l for l in span.splitlines() if l.strip() and not l.startswith(":::")]
        inner = "<br>".join(escape_inline(l.lstrip()) for l in lines)
        return f'<aside class="disclaimer"><p><strong>Heads-up:</strong> {inner}</p></aside>'

    return BLOCK_RE.sub(one, token)


def escape_inline(text):
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    return text


BLOCK_START = ("#", "- ", "> ", "|", "```", ":::")


def md_to_html(md_text):
    text, spans = _extract_block_spans(
        md_text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.split("\n")

    out = []
    open_tag = None
    table_cache = None  # header cells waiting for a separator row

    def close_paragraph():
        nonlocal open_tag
        if open_tag == "p":
            out.append("</p>")
            open_tag = None

    def close_list():
        nonlocal open_tag
        if open_tag in ("ul", "ol"):
            out.append(f"</{open_tag}>")
            open_tag = None

    def close_all():
        close_paragraph()
        close_list()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if BLOCK_RE.fullmatch(stripped):
            close_all()
            out.append(render_block_spans(spans, stripped))
            table_cache = None
            i += 1
            continue

        if not stripped:
            close_all()
            table_cache = None
            i += 1
            continue

        if table_cache is not None:
            if _is_table_sep(stripped):
                out.append("<table><thead><tr>"
                           + "".join(f"<th>{escape_inline(c)}</th>" for c in table_cache)
                           + "</tr></thead><tbody>")
                i += 1
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = _split_table_row(lines[i])
                    out.append("<tr>" + "".join(f"<td>{escape_inline(c)}</td>" for c in cells) + "</tr>")
                    i += 1
                out.append("</tbody></table>")
                table_cache = None
                continue
            table_cache = None  # not a table after all; fall through as text

        if re.fullmatch(r"-{3,}", stripped):
            close_all()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            close_all()
            level = len(m.group(1))
            out.append(f"<h{level}>{escape_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            close_paragraph()
            if open_tag != "ul":
                close_list()
                open_tag = "ul"
                out.append("<ul>")
            out.append(f"<li>{escape_inline(stripped[2:])}</li>")
            i += 1
            continue

        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            close_paragraph()
            if open_tag != "ol":
                close_list()
                open_tag = "ol"
                out.append("<ol>")
            out.append(f"<li>{escape_inline(m.group(1))}</li>")
            i += 1
            continue

        if stripped.startswith("> "):
            close_all()
            quote_lines = [escape_inline(stripped[2:])]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(escape_inline(lines[i].strip()[2:]))
                i += 1
            out.append("<blockquote><p>" + "<br>".join(quote_lines) + "</p></blockquote>")
            continue

        if stripped.startswith("|"):
            close_all()
            table_cache = _split_table_row(stripped)
            i += 1
            continue

        if in_paragraph := (open_tag == "p"):
            out.append(escape_inline(stripped))
            i += 1
            continue

        out.append("<p>")
        open_tag = "p"
        out.append(escape_inline(stripped))
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(BLOCK_START)
                    or re.fullmatch(r"-{3,}", nxt)
                    or re.match(r"^\d+\.\s", nxt)
                    or BLOCK_RE.fullmatch(nxt)):
                break
            out.append(" " + escape_inline(nxt))
            i += 1
        out.append("</p>")
        open_tag = None

    close_all()
    return "".join(out)

# ------------------------------------------------------------------ page ----

def wrap_page(body, slug):
    nav_items = "".join(
        f'<a href="{s}.html"{" aria-current=\"page\"" if s == slug else ""}>{html.escape(t)}</a>'
        for s, t in NAV)
    idx = [s for s, _ in NAV].index(slug)
    prev = NAV[idx - 1] if idx > 0 else None
    nxt = NAV[idx + 1] if idx < len(NAV) - 1 else None
    prev_html = f'<a class="pager" href="{prev[0]}.html">&#8592; {html.escape(prev[1])}</a>' if prev else "<span></span>"
    next_html = f'<a class="pager right" href="{nxt[0]}.html">&#8594; {html.escape(nxt[1])}</a>' if nxt else "<span></span>"
    page_title = dict(NAV)[slug]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(f"{TITLE} — {page_title}")}</title>
<meta name="description" content="{html.escape(SUBTITLE)}. Education only, never legal or tax advice.">
<style>
:root {{ --ink:#26303a; --paper:#fbfaf7; --accent:#24625f; --accent2:#c96b3f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Georgia,'Times New Roman',serif; background:var(--paper); color:var(--ink); line-height:1.65; font-size:17px; }}
a {{ color:var(--accent); }}
code {{ background:#eeede8; padding:1px 5px; border-radius:4px; font-size:.9em; }}
pre code {{ display:block; padding:1em; overflow-x:auto; }}
nav {{ display:flex; flex-wrap:wrap; gap:.4rem .9rem; padding:1rem 1.5rem; background:var(--ink); }}
nav a {{ color:#f4f1ea; text-decoration:none; font-family:system-ui,sans-serif; font-size:.86rem; }}
nav a[aria-current="page"] {{ color:#ffd9a8; font-weight:700; }}
main {{ max-width:46rem; margin:0 auto; padding:2rem 1.25rem 1rem; }}
h1 {{ font-size:2rem; line-height:1.25; margin:.2rem 0 1rem; }}
h2 {{ margin-top:2rem; font-size:1.35rem; color:var(--accent); }}
h3 {{ margin-top:1.6rem; }}
blockquote {{ margin:1rem 0; padding:.4rem 1.2rem; border-left:4px solid var(--accent2); background:#f5f2ec; }}
aside.disclaimer {{ margin:1.5rem 0; padding:.8rem 1.2rem; border:1px solid var(--accent2); border-radius:8px; background:#fbf3ec; font-size:.94em; }}
table {{ border-collapse:collapse; width:100%; margin:1rem 0; font-size:.94em; font-family:system-ui,sans-serif; }}
th, td {{ border:1px solid #ddd6c9; padding:.45rem .7rem; }}
th {{ background:#eee9de; text-align:left; }}
hr {{ border:0; border-top:1px solid #ddd6c9; margin:2rem 0; }}
.pagers {{ display:flex; justify-content:space-between; max-width:46rem; margin:2rem auto; padding:0 1.25rem; font-family:system-ui,sans-serif; }}
.pager {{ text-decoration:none; }}
footer {{ max-width:46rem; margin:0 auto; padding:0 1.25rem 2.5rem; font-size:.85rem; color:#6c7480; font-family:system-ui,sans-serif; }}
@media print {{ nav, .pagers {{ display:none; }} body {{ background:#fff; }} }}
</style>
</head>
<body>
<nav aria-label="Chapters">{nav_items}</nav>
<main>
{body}
</main>
<div class="pagers">{prev_html}{next_html}</div>
<footer>{html.escape(FOOTER)}</footer>
</body>
</html>
"""


def build():
    SITE.mkdir(exist_ok=True)
    built = []
    for slug, _label in NAV:
        md_path = DOCS / f"{slug}.md"
        if not md_path.exists():
            raise SystemExit(f"Missing required doc: {md_path}")
        md_text = md_path.read_text(encoding="utf-8")
        (SITE / f"{slug}.html").write_text(wrap_page(md_to_html(md_text), slug),
                                           encoding="utf-8")
        built.append(slug)
    return built

# ------------------------------------------------------------------ tests ---

def run_tests():
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)

    out = md_to_html("# Hi\n\nSome **bold** and *em* and `code` and [a link](x.html).\n")
    check("h1", "<h1>Hi</h1>" in out)
    check("bold", "<strong>bold</strong>" in out)
    check("em", "<em>em</em>" in out)
    check("code", "<code>code</code>" in out)
    check("link", '<a href="x.html">a link</a>' in out)

    out = md_to_html("- one\n- two\n\n1. a\n2. b\n")
    check("ul", "<ul><li>one</li><li>two</li></ul>" in out)
    check("ol", "<ol><li>a</li><li>b</li></ol>" in out)

    out = md_to_html("| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |")
    check("table", "<table><thead><tr><th>A</th><th>B</th></tr></thead><tbody>" in out
          and "<tr><td>2</td><td>4</td></tr>" not in out
          and "<tr><td>1</td><td>2</td></tr>" in out)

    out = md_to_html("> quoted line one\n> quoted line two\n")
    check("blockquote", "<blockquote><p>quoted line one<br>quoted line two</p></blockquote>" in out)

    out = md_to_html(":::disclaimer\nNot legal advice.\n:::\n\nAfter.\n")
    check("disclaimer", 'class="disclaimer"' in out and "Not legal advice." in out
          and "<p>After.</p>" in out)

    out = md_to_html('```python\nx = "<b>"\n```\n')
    check("code_fence", "<pre><code>" in out and "&lt;b&gt;" in out and "<b></code>" not in out)

    out = md_to_html("Para line one\nline two continues.\n\nNext para.\n")
    check("para_wrap", "<p>Para line one line two continues.</p>" in out
          and "<p>Next para.</p>" in out)

    out = md_to_html("before\n\n---\n\nafter\n")
    check("hr", "<p>before</p>" in out and "<hr>" in out and "<p>after</p>" in out)

    out = md_to_html("a <b> & c")
    check("escape", "&lt;b&gt;" in out and "&amp;" in out and "<b>" not in out)

    out = md_to_html("## Roadmap\n\n1. [Start](00.html) first\n2. Then pricing\n\nDone.\n")
    check("ordered_with_links", '<a href="00.html">Start</a>' in out
          and "<li>Then pricing</li>" in out and "<p>Done.</p>" in out)

    for slug in build():
        page = (SITE / f"{slug}.html").read_text(encoding="utf-8")
        check(f"page:{slug}:doctype", page.startswith("<!DOCTYPE html>"))
        check(f"page:{slug}:nav", "<nav" in page and f'{slug}.html"' in page)
        check(f"page:{slug}:footer", "Asdale Dynamics, LLC" in page)

    home = (SITE / "index.html").read_text(encoding="utf-8")
    for slug, _label in NAV:
        check(f"index_links:{slug}", f'href="{slug}.html"' in home)
    check("index_disclaimer", "never legal" in home)

    if failures:
        print("FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("All tests passed.")
    print(f"Built {len(NAV)} pages into {SITE.name}/")
    return 0


def main():
    if "--test" in sys.argv:
        return run_tests()
    build()
    print(f"Built {len(NAV)} pages into {SITE.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
