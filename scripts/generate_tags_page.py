#!/usr/bin/env python3
"""Regenerate content/all-tags.md: every tag with its usage count, sorted by
frequency (then alphabetically), linked to its Quartz tag page.

Run after adding notes that introduce new tags:
    python scripts/generate_tags_page.py
"""

import os
import re

CONTENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "content"))
OUT = os.path.join(CONTENT, "all-tags.md")


def extract_tags(text: str) -> list[str]:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return []
    return [t.strip() for t in re.findall(r"^\s*-\s+(.+)$", m.group(1), re.M)]


counts: dict[str, int] = {}
for name in os.listdir(CONTENT):
    if not name.endswith(".md") or name == "all-tags.md":
        continue
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        for tag in extract_tags(f.read()):
            counts[tag] = counts.get(tag, 0) + 1

ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))

lines = [
    "---",
    "title: All Tags",
    "draft: false",
    "---",
    "",
    f"There are **{len(ordered)}** tags, sorted by how often they're used:",
    "",
]
lines += [f"- [{tag} ({n})](/tags/{tag})" for tag, n in ordered]
lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote {len(ordered)} tags to {OUT}")
