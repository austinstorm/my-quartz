#!/usr/bin/env python3
"""Audit commonplace entries for missing author and publication tags.

Usage:
    python scripts/audit_tags.py [--apply]

Reads every note in content/, detects the quoted author (from the attribution
line) and the source publication (from the URL domain), and reports which notes
are missing a CamelCased author tag and/or publication tag. With --apply, adds
the missing tags to the frontmatter (uncommitted).

Substack and personal/social platforms are not treated as publications.
"""

import os
import re
import sys
from collections import Counter

CONTENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "content"))

# domain -> publication tag (skip entries handled below)
PUBLICATIONS = {
    "theatlantic.com": "theAtlantic",
    "harpers.org": "Harpers",
    "thenewatlantis.com": "theNewAtlantis",
    "firstthings.com": "FirstThings",
    "theparisreview.org": "theParisReview",
    "wsj.com": "WSJ",
    "nytimes.com": "NYT",
    "newyorker.com": "theNewYorker",
    "comment.org": "Comment",
    "plough.com": "Plough",
    "mereorthodoxy.com": "MereOrthodoxy",
    "unherd.com": "UnHerd",
    "damagemag.com": "DamageMag",
    "asteriskmag.com": "Asterisk",
    "thelampmagazine.com": "TheLamp",
    "desiringgod.org": "DesiringGod",
    "northamanglican.com": "NorthAmAnglican",
    "educationprogress.org": "EducationProgress",
    "christianitytoday.com": "ChristianityToday",
    "theamericanconservative.com": "theAmericanConservative",
    "americamagazine.org": "America",
    "commonwealmagazine.org": "Commonweal",
    "newcriterion.com": "theNewCriterion",
    "prospectmagazine.co.uk": "Prospect",
    "aeon.co": "Aeon",
    "eurozine.com": "Eurozine",
    "lithub.com": "LitHub",
    "poetryfoundation.org": "PoetryFoundation",
    "publicdomainreview.org": "thePublicDomainReview",
    "longreads.com": "Longreads",
    "firstthings.com": "FirstThings",
    "theopolisinstitute.com": "Theopolis",
    "conversatio.org": "Conversatio",
    "christkirk.com": "ChristKirk",
    "anglicancompass.com": "AnglicanCompass",
    "livingchurch.org": "theLivingChurch",
    "covenant.livingchurch.org": "Covenant",
    "9marks.org": "NineMarks",
    "religionnews.com": "ReligionNews",
    "churchlifejournal.nd.edu": "ChurchLifeJournal",
    "cruxnow.com": "Crux",
    "nationalreview.com": "NationalReview",
    "thecritic.co.uk": "TheCritic",
    "spectator.co.uk": "TheSpectator",
    "thespectator.com": "TheSpectator",
    "newstatesman.com": "NewStatesman",
    "lrb.co.uk": "LondonReview",
    "nybooks.com": "NYRB",
    "theguardian.com": "theGuardian",
    "thetimes.co.uk": "TheTimes",
    "economist.com": "theEconomist",
    "ft.com": "FinancialTimes",
    "bloomberg.com": "Bloomberg",
    "vox.com": "Vox",
    "slate.com": "Slate",
    "theatlantic...": None,  # placeholder never matches
}

# domains that are platforms / personal sites / social — never a publication tag
SKIP_DOMAINS = {
    "substack.com", "medium.com", "youtube.com", "instagram.com", "x.com",
    "twitter.com", "imgur.com", "pbs.twimg.com", "wordpress.com", "wikipedia.org",
    "reddit.com", "archive.org", "spotify.com", "soundcloud.com", "tiktok.com",
    "facebook.com", "github.com", "google.com", "maps.google.com", "news.ycombinator.com",
    "dougwils.com", "tobyjsumpter.com", "maryharrington.co.uk", "aworkinglibrary.com",
    "adesertfather.org", "nhc.anglican.center", "alastairadversaria.wordpress.com",
}


def read_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {"title": "", "tags": []}, text
    fm = m.group(1)
    title = re.search(r"^title:\s*(.+)$", fm, re.M)
    tags = re.findall(r"^\s*-\s+(.+)$", fm, re.M)
    body = text[m.end():]
    return {"title": title.group(1).strip() if title else "", "tags": [t.strip() for t in tags]}, body


def camel(name):
    name = re.sub(r"[\[(\]]", "", name).strip()
    if not name:
        return ""
    parts = [p for p in re.split(r"[\s.,'\-/]+", name) if p]
    return "".join((p[0].upper() + p[1:]) if p else "" for p in parts)


def extract_author(body):
    """Best-effort attribution: `- Name` line, ideally right after a blockquote."""
    lines = body.split("\n")
    candidates = []
    for i, line in enumerate(lines):
        m = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if not m:
            continue
        cand = m.group(1).strip()
        # strip trailing markdown link, comma/em-dash citations
        cand = re.sub(r"\[.*?\]\(https?://[^)]*\)", "", cand)
        cand = re.sub(r"^.*?—\s*", "", cand)
        cand = re.sub(r"[,;].*$", "", cand).strip()
        if not cand:
            continue
        # must look like a person's name: capital letters and a space
        if re.match(r"^[A-Z]", cand) and " " in cand and len(cand) < 60:
            score = 0
            if i > 0 and lines[i - 1].strip().startswith(">"):
                score += 2  # directly after a blockquote
            if re.search(r"\(https?://", line):
                score += 1  # has a source link
            candidates.append((cand, score))
    if not candidates:
        return ""
    # highest score, then last in file
    candidates.sort(key=lambda c: (-c[1], 0))
    return candidates[0][0]


def extract_domains(body):
    urls = re.findall(r"https?://(?:www\.)?([^/\s\)\]]+)", body)
    return [u.lower() for u in urls]


def main():
    apply_changes = "--apply" in sys.argv
    files = sorted(n for n in os.listdir(CONTENT) if n.endswith(".md") and n != "all-tags.md")

    missing_author = []
    missing_pub = []
    unmapped_domains = Counter()
    pub_counter = Counter()

    for name in files:
        with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
            text = f.read()
        fm, body = read_frontmatter(text)
        tags = set(fm["tags"])

        author = extract_author(body)
        if author:
            atag = camel(author)
            if atag and atag not in tags:
                missing_author.append((name, fm["title"], author, atag))

        for dom in extract_domains(body):
            if dom in SKIP_DOMAINS or dom.endswith(".substack.com"):
                continue
            tag = PUBLICATIONS.get(dom)
            if tag:
                pub_counter[tag] += 1
                if tag not in tags:
                    missing_pub.append((name, fm["title"], tag, dom))
            else:
                unmapped_domains[dom] += 1

    print(f"Audited {len(files)} notes")
    print(f"Missing author tag: {len(missing_author)} notes")
    print(f"Missing publication tag: {len(missing_pub)} notes")
    print(f"Unmapped domains (review): {dict(unmapped_domains.most_common(30))}")
    print()
    print("=== MISSING AUTHOR TAGS ===")
    for name, title, author, atag in missing_author:
        print(f"{atag}: {title}")
    print()
    print("=== MISSING PUBLICATION TAGS ===")
    for name, title, tag, dom in missing_pub:
        print(f"{tag} ({dom}): {title}")

    if apply_changes:
        applied_a = 0
        applied_p = 0
        for name, title, author, atag in missing_author:
            p = os.path.join(CONTENT, name)
            text = open(p, encoding="utf-8").read()
            text = text.replace("tags:", "tags:", 1)
            text = text.replace("---\ntags:", "---\ntags:", 1)
            text = re.sub(r"^tags:\s*$", "tags:\n  - " + atag, text, count=1, flags=re.M)
            open(p, "w", encoding="utf-8").write(text)
            applied_a += 1
        for name, title, tag, dom in missing_pub:
            p = os.path.join(CONTENT, name)
            text = open(p, encoding="utf-8").read()
            text = re.sub(r"^tags:\s*$", "tags:\n  - " + tag, text, count=1, flags=re.M)
            open(p, "w", encoding="utf-8").write(text)
            applied_p += 1
        print(f"\nApplied {applied_a} author tags and {applied_p} publication tags")


if __name__ == "__main__":
    main()
