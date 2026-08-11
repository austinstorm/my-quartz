#!/usr/bin/env python3
"""Migrate a TiddlyWiki JSON export into the Quartz commonplace book.

Usage:
    python scripts/tiddlywiki_to_quartz.py [export.json] [output_dir]

Defaults: reads tiddlers.json from the current directory, writes to content/.

Skips system tiddlers, converts TiddlyWiki wikitext to Markdown, parses tags
(including [[multi word]] tags) into CamelCased Quartz tags, and writes one
.md file per tiddler with frontmatter. Reports any tiddlers that still contain
unconverted wikitext so they can be reviewed by hand.
"""

import json
import os
import re
import sys

SYSTEM_PREFIX = "$:/"
DROP_TAGS = {"commonplace"}

# TiddlyWiki app/Merhegan boilerplate tiddlers — not the user's content.
# They contain live widgets/macros that have no Markdown rendering.
SKIP_TITLES = {
    "Autocomplete Triggers Summary",
    "ChangeLog",
    "Home",
    "How to Use AutoComplete",
    "Mehregan Information",
    "yikes",
}

# Windows-illegal filename characters (also strips control chars)
INVALID_FILENAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# Wikitext patterns (rough)
IMAGE_RE = re.compile(r"\[img\[([^\]]*)\]\]")
WIKILINK_RE = re.compile(r"\[\[([^\]\]]+?)\]\]")
TRANSCLUDE_RE = re.compile(r"\{\{([^}]+?)\}\}")


def parse_tags(tags_str: str) -> list[str]:
    """Split TiddlyWiki tags field, joining [[multi word]] tags correctly."""
    tokens = tags_str.split()
    tags = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("[["):
            buf = tok
            while not buf.endswith("]]") and i + 1 < len(tokens):
                i += 1
                buf += " " + tokens[i]
            tags.append(buf)
        else:
            tags.append(tok)
        i += 1
    return tags


def camel(tag: str) -> str:
    """CamelCase a tag. Multi-word (space/period separated) tags become
    CamelCased single tokens; single-word tags are kept verbatim."""
    tag = tag.strip()
    if tag.startswith("[["):
        tag = tag[2:]
    if tag.endswith("]]"):
        tag = tag[:-2]
    if not tag:
        return ""
    if re.search(r"[\s._\-/]", tag):
        parts = [p for p in re.split(r"[\s._\-/]+", tag) if p]
        return "".join((p[0].upper() + p[1:]) if p else "" for p in parts)
    return tag


def convert_blockquotes(text: str) -> str:
    """Convert TiddlyWiki <<< blockquotes to > markdown with - Author citations."""
    lines = text.split("\n")
    out = []
    in_quote = False
    for line in lines:
        s = line.strip()
        if s == "<<<":
            if in_quote:
                in_quote = False
                out.append("")
            else:
                in_quote = True
            continue
        if s.startswith("<<<"):
            citation = s[3:].strip()
            if in_quote:
                in_quote = False
                out.append("")
                if citation:
                    out.append(f"- {citation}")
            else:
                in_quote = True
            continue
        if in_quote:
            out.append("> " + line if line.strip() else ">")
        else:
            out.append(line)
    return "\n".join(out)


def convert_blocks(text: str) -> str:
    """Heading marks !/!!/!!! at start of line -> #/##/###."""
    return re.sub(r"(?m)^(\s*)(!+)(\s)", lambda m: m.group(1) + "#" * len(m.group(2)) + m.group(3), text)


def convert_inline(text: str) -> str:
    """Bold ''x'' -> **x**, italic //x// -> *x*."""
    text = re.sub(r"''(.+?)''", r"**\1**", text)
    # (?<!:) avoids matching the // in http(s):// URLs
    text = re.sub(r"(?<!:)//([^/\n]+?)//", r"*\1*", text)
    return text


def convert_images(text: str) -> str:
    def repl(m):
        inner = m.group(1)
        if "|" in inner:
            parts = inner.split("|")
            alt = parts[0]
            url = parts[-1]
        else:
            alt, url = "", inner
        return f"![{alt}]({url})"
    return IMAGE_RE.sub(repl, text)


def convert_links(text: str) -> str:
    """[[text|Target]] -> [[Target|text]] (Obsidian alias form); URL targets
    become plain markdown links [text](url)."""

    def repl(m):
        inner = m.group(1)
        display, _, target = inner.partition("|")
        if not target:
            if re.match(r"https?://|www\.", inner.strip()):
                return f"[{inner.strip()}]({inner.strip()})"
            return f"[[{inner}]]"
        if re.match(r"https?://|www\.", target.strip()):
            return f"[{display}]({target.strip()})"
        return f"[[{target}|{display}]]"

    return WIKILINK_RE.sub(repl, text)


def convert_transclusions(text: str) -> str:
    def repl(m):
        inner = m.group(1)
        target = inner.split("||", 1)[0].split("!!", 1)[0]
        return f"[[{target}]]"
    return TRANSCLUDE_RE.sub(repl, text)


def convert_wikitext(text: str) -> str:
    text = convert_blockquotes(text)
    text = convert_blocks(text)
    text = convert_inline(text)
    text = convert_images(text)
    text = convert_links(text)
    text = convert_transclusions(text)
    return text.strip("\n")


def safe_filename(title: str) -> str:
    name = INVALID_FILENAME.sub("", title)
    return name.rstrip(" .")


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_file(tiddler: dict) -> tuple[str, str] | None:
    title = tiddler.get("title", "").strip()
    if title.startswith(SYSTEM_PREFIX) or not title or title in SKIP_TITLES:
        return None

    tags = []
    for t in parse_tags(tiddler.get("tags", "")):
        c = camel(t)
        if c and c not in DROP_TAGS and c not in tags:
            tags.append(c)

    body = convert_wikitext(tiddler.get("text", ""))

    tags_block = ""
    if tags:
        tags_block = "tags:\n" + "\n".join(f"  - {t}" for t in tags) + "\n"
    frontmatter = (
        f"---\n"
        f"title: {yaml_str(title)}\n"
        f"draft: false\n"
        f"{tags_block}"
        f"---\n"
    )
    content = frontmatter + "\n" + body + "\n" if body else frontmatter
    return title, content


def residue_scan(text: str) -> list[str]:
    """Find leftover wikitext a hand review would care about."""
    hits = []
    if text.count("[[") != text.count("]]"):
        hits.append("unbalanced wikilinks")
    if "<<<" in text:
        hits.append("blockquote marker")
    if re.search(r"<<[^>\n]+>>", text):
        hits.append("macro")
    if "{{" in text or "}}" in text:
        hits.append("transclusion/braces")
    if text.count("''") % 2 == 1:
        hits.append("unpaired bold")
    if re.search(r"\*https?:", text):
        hits.append("possibly mangled URL (italic)")
    return hits


def main():
    export = sys.argv[1] if len(sys.argv) > 1 else "tiddlers.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "content"

    with open(export, encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    written = 0
    skipped_system = 0
    collisions = {}
    warnings = []
    used = set()

    for tiddler in data:
        result = build_file(tiddler)
        if result is None:
            skipped_system += 1
            continue
        title, content = result
        fname = safe_filename(title) + ".md"
        base = safe_filename(title)
        n = 2
        while fname in used:
            fname = f"{base}_{n}.md"
            n += 1
        used.add(fname)

        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

        for name in residue_scan(content):
            warnings.append(f"CHECK ({name}): {fname}")

    print(f"Exported: {len(data)} tiddlers")
    print(f"  written: {written}")
    print(f"  skipped (system/empty title): {skipped_system}")
    print(f"  hand-review warnings: {len(warnings)}")

    if warnings:
        report = os.path.join(out_dir, "..", "scripts", "migration_warnings.txt")
        report = os.path.abspath(report)
        with open(report, "w", encoding="utf-8") as f:
            f.write("\n".join(warnings) + "\n")
        print(f"  warnings written to {report}")


if __name__ == "__main__":
    main()
