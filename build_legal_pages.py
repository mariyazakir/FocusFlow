"""Generate the PWA's static legal pages from the shared Markdown drafts."""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PWA = ROOT / "pwa"


def inline(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"`(.+?)`", r"<code>\1</code>", value)
    return value


def render_markdown(markdown: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    list_open = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            output.append("</ul>")
            list_open = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            close_list()
        elif line == "---":
            flush_paragraph()
            close_list()
            output.append("<hr>")
        elif line.startswith("#"):
            flush_paragraph()
            close_list()
            level = len(line) - len(line.lstrip("#"))
            output.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
        elif line.startswith("- "):
            flush_paragraph()
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append("<li>" + inline(line[2:]) + "</li>")
        else:
            close_list()
            paragraph.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(output)


def build_page(source: str, target: str, title: str) -> None:
    body = render_markdown((ROOT / source).read_text(encoding="utf-8"))
    body = body.replace('href="PRIVACY_POLICY.md"', 'href="/privacy.html"')
    body = body.replace('href="TERMS_OF_USE.md"', 'href="/terms.html"')
    page = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#6855e8">
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="stylesheet" href="/styles.css">
  <link rel="stylesheet" href="/legal.css">
  <title>{title} · FocusFlow</title>
</head>
<body>
  <main class="main-content" style="margin:0 auto;max-width:1000px">
    <a class="legal-back" href="/">← Back to FocusFlow</a>
    <article class="legal-article">{body}</article>
    <a class="legal-back" href="/">← Back to FocusFlow</a>
  </main>
</body>
</html>
'''
    (PWA / target).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    build_page("TERMS_OF_USE.md", "terms.html", "Terms of Use")
    build_page("PRIVACY_POLICY.md", "privacy.html", "Privacy Policy")
