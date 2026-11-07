#!/usr/bin/env python3
"""Zero-dependency HTML + JS checker for cksau.com."""
import ast
import os
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML_FILES = ["index.html", "play.html", "resume.html", "play/boxwrapestimator.html"]
JS_FILES = ["filenames.js", "menubar.js", "sorting.js"]
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class PageChecker(HTMLParser):
    def __init__(self, html_path: Path):
        super().__init__()
        self.html_path = html_path
        self.errors = []
        self.has_doctype = False
        self.has_title = False
        self.in_script = False
        self.script_buf = []
        self.inline_scripts = []
        self.tag_stack = []

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if tag == "title":
            self.has_title = True
        if tag == "script" and "src" not in attr_map:
            self.in_script = True
            self.script_buf = []

        if tag not in VOID_ELEMENTS:
            self.tag_stack.append((tag, self.getpos()[0]))

        for attr in ("src", "href"):
            val = attr_map.get(attr)
            if not val or val.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            target = (self.html_path.parent / val.split("?")[0].split("#")[0]).resolve()
            if not target.exists():
                self.errors.append(f"{self.html_path.name}:{self.getpos()[0]} broken {attr}='{val}'")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS and self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            self.in_script = False
            self.inline_scripts.append("".join(self.script_buf))
        if tag in VOID_ELEMENTS:
            return
        if self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()
        else:
            self.errors.append(f"{self.html_path.name}:{self.getpos()[0]} mismatched closing </{tag}>")

    def handle_data(self, data):
        if self.in_script:
            self.script_buf.append(data)


def check_js_syntax(code: str, label: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    try:
        res = subprocess.run(["node", "--check", tmp_path], capture_output=True, text=True)
        if res.returncode != 0:
            err = res.stderr.replace(tmp_path, label).strip()
            return [f"JS syntax error in {label}:\n{err}"]
        return []
    finally:
        os.unlink(tmp_path)


def check_filenames_js(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8").strip()
    prefix = "const imageFilePaths = "
    if not content.startswith(prefix):
        return ["filenames.js: must start with 'const imageFilePaths = '"]
    try:
        paths = ast.literal_eval(content[len(prefix):].rstrip(";"))
    except Exception as exc:
        return [f"filenames.js: invalid array literal ({exc})"]
    if not isinstance(paths, list) or not paths:
        return ["filenames.js: imageFilePaths must be a non-empty list"]
    bad = [p for p in paths if not isinstance(p, str) or not p.startswith("images/")]
    if bad:
        return [f"filenames.js: invalid image path entries: {bad[:3]}"]
    return []


def check_unit_tests() -> list[str]:
    test_js = """
    const fs = require('fs');
    eval(fs.readFileSync('sorting.js', 'utf8'));
    const sample = ['images/web/b.jpg', 'images/mj/1a.jpg', 'images/web/a.jpg'];
    const sorted = sortGalleryAlphabetically(sample);
    if (sorted[0] !== 'images/mj/1a.jpg' || sample[0] !== 'images/web/b.jpg') {
        throw new Error('sortGalleryAlphabetically failed or mutated input');
    }
    const webOnly = sortGalleryByCategory(sample, 'web');
    if (webOnly.length !== 2) throw new Error('sortGalleryByCategory failed');
    const mjOnly = sortGalleryByCustomCategory(sample, 'mj');
    if (mjOnly.length !== 1) throw new Error('sortGalleryByCustomCategory failed');
    """
    res = subprocess.run(["node", "-e", test_js], cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        return [f"Unit test failure:\n{res.stderr.strip()}"]
    return []


def check_play_launcher() -> list[str]:
    errs = []
    if (ROOT / "play" / "gpt-formatter").exists():
        errs.append("play/gpt-formatter directory should be removed")
    play_html = (ROOT / "play.html").read_text(encoding="utf-8")
    for app_id in ("#tiles", "#boxwrap", "#rss", "#big5"):
        if f'href="{app_id}"' not in play_html:
            errs.append(f"play.html: missing launcher link for {app_id}")
    if 'id="app-modal-close"' not in play_html:
        errs.append("play.html: missing #app-modal-close button")
    if "hashchange" not in play_html:
        errs.append("play.html: missing hashchange listener for back navigation")
    return errs


def check_cli_resume() -> list[str]:
    errs = []
    resume_html = (ROOT / "resume.html").read_text(encoding="utf-8")
    for required in ("Lockheed Martin", "Funnel Leasing", "United States Air Force", "CompTIA Security+"):
        if required not in resume_html:
            errs.append(f"resume.html: missing required text '{required}'")
    for forbidden in ("843-806-9639", "Home Depot", "Palauanvibe.biz"):
        if forbidden in resume_html:
            errs.append(f"resume.html: contains excluded text '{forbidden}'")
    return errs


def main() -> int:
    errors = []

    for rel in JS_FILES:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing JS file: {rel}")
            continue
        errors.extend(check_js_syntax(p.read_text(encoding="utf-8"), rel))

    if (ROOT / "filenames.js").exists():
        errors.extend(check_filenames_js(ROOT / "filenames.js"))

    for rel in HTML_FILES:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing HTML file: {rel}")
            continue
        checker = PageChecker(p)
        checker.feed(p.read_text(encoding="utf-8"))
        if not checker.has_doctype:
            errors.append(f"{rel}: missing <!DOCTYPE>")
        if not checker.has_title:
            errors.append(f"{rel}: missing <title>")
        for tag, line in checker.tag_stack:
            errors.append(f"{rel}:{line} unclosed <{tag}>")
        errors.extend(checker.errors)
        for idx, script in enumerate(checker.inline_scripts, 1):
            errors.extend(check_js_syntax(script, f"{rel}<script #{idx}>"))

    errors.extend(check_unit_tests())
    errors.extend(check_play_launcher())
    errors.extend(check_cli_resume())

    if errors:
        print("CHECKS FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK: Checked {len(HTML_FILES)} HTML files, {len(JS_FILES)} JS files, and unit tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
