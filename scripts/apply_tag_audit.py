#!/usr/bin/env python3
"""Apply the curated tag-audit additions to note frontmatter.

Merges missing tags into each note's frontmatter `tags:` block:
- publication tags (computed from source URL domains, with corrections)
- curated author tags (AUTHOR_ADD below)
- section-3 people/subject suggestions (parsed from tag_audit_report.md)

Usage: python scripts/apply_tag_audit.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from audit_tags import extract_domains, PUBLICATIONS, SKIP_DOMAINS  # noqa: E402

CONTENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "content"))
REPORT = os.path.join(os.path.dirname(__file__), "tag_audit_report.md")

# Publication tag corrections / additions (from user review)
PUB_CORRECT = {"Comment": "CommentMag", "America": "AmericaMag"}
PUB_EXTRA = {
    "symbol of divine wrath.md": ["Credenda"],
    "it is a wise thing to simulate craziness.md": ["ClaremontReview"],
}

# Curated author tags: filename -> tags (corrections applied: PeterLeithart,
# FrancisSchaeffer, CornelWest, etc.)
AUTHOR_ADD = {
    "A Christianity that is not merely correct.md": ["JavierValazquez"],
    "Not merely correct.md": ["JavierValazquez"],
    "A ditch on either side of the road.md": ["KirstenSanders"],
    "Against communion wafers.md": ["BenCrosby"],
    "Americans need to party more.md": ["EllenCushing"],
    "An entrepreneur is a person who.md": ["ChinNingChu"],
    "Being well set to music.md": ["JosephAddison"],
    "Big Belly trash cans.md": ["AndrewMManshel"],
    "Blessed convent of the infirm.md": ["SisterTeresaDeCartagena"],
    "Cancel culture retrospective.md": ["HugoSchwyzer"],
    "Consumption and Eucharist.md": ["WilliamTCavanaugh"],
    "Criticism is language that expresses.md": ["NorthropFrye"],
    "Cross of reality.md": ["PeterLeithart"],
    "Divert his attention, then clobber him.md": ["FlanneryOConnor"],
    "Large and startling figures.md": ["FlanneryOConnor"],
    "The truth does not change.md": ["FlanneryOConnor"],
    "Each day is a gift.md": ["HopeCantwell"],
    "Eternity is not the negation of time.md": ["FrAlexanderSchmemann"],
    "Evangelical preacher as TED talk presenter.md": ["AlastairRoberts"],
    "Everyone complains of his memory.md": ["LaRochefoucauld"],
    "Figure out who you want to be on your team.md": ["JohnLilly"],
    "Good work.md": ["AnthonyScholle"],
    "I am always a child.md": ["MadeleineLEngle"],
    "In defense of websites.md": ["MandyBrown"],
    "Individual liberation within capitalism.md": ["SebastianThrul"],
    "Life as art.md": ["FrancisSchaeffer"],
    "Life is best lived in the active voice.md": ["FrStephenFreeman"],
    "We are all in a Christmas play.md": ["FrStephenFreeman"],
    "Others' superiority.md": ["AGSertillanges"],
    "Personal writing.md": ["RaxKing"],
    "The draft.md": ["RaxKing"],
    "Places to disappear.md": ["AMHickman"],
    "Postmodernism was cute in art.md": ["ClaytonCubit"],
    "Redeeming culture.md": ["JoshGibbs"],
    "Relating to art.md": ["AndreyTarkovski"],
    "Style is like a frog.md": ["RoyWilliams"],
    "Tarot contra rationalism.md": ["JessicaDore"],
    "The Kybalion and New Thought.md": ["NicholasEChapel"],
    "The business of the church.md": ["WalterBrueggemann"],
    "The future of theological education.md": ["TedSmith"],
    "The machine that builds the product.md": ["DennisCrowley"],
    "The paradoxes of creativity.md": ["GeorgeKneller"],
    "The perils of audience capture.md": ["GurwinderBhogal"],
    "The right to vote has killed a lot of people.md": ["NateWolff"],
    "The telephone was an aberration.md": ["RickWebb"],
    "To the human heart.md": ["StJohnOfKronstadt"],
    "Twee is a diagnosis of cultural ennui.md": ["IreneTriendl"],
    "Via media.md": ["FrMartinThornton"],
    "What makes videogame labor so exciting.md": ["TabithaArnold"],
    "Young, Rested, Reformed.md": ["SethTroutt"],
    "a way of getting good at things.md": ["CharlesAndRayEames"],
    "bring back evil.md": ["NicholasRussell"],
    "cobelligerents.md": ["TimKeller"],
    "food and drink actually differ by region.md": ["TimWu"],
    "fellowship of the grievance.md": ["DougWilson"],
    "vanguard of the reformation.md": ["DougWilson"],
    "zero-sum thinking.md": ["DougWilson"],
    "love my way through the absurdity of life.md": ["CornelWest"],
    "the eros of souls.md": ["BartonSwaim"],
    "somebody you went to high school with.md": ["PJORourke"],
    "the pet dream.md": ["MerrittK"],
    "Orthodoxy contra the West.md": ["BenJohnson"],
    "tricking other people to take their place.md": ["MaryHKChoi"],
    "Bad trips.md": ["AshleyLande"],
    "enclose himself in the inner closet of his heart.md": ["StDimitriOfRostov"],
    # 2b: cleaned of source context
    "Anything that happened to a baby boomer twice.md": ["RandallMunroe"],
    "Art is error.md": ["TedOrland", "DavidBayles"],
    "Can computers do math.md": ["DavidSchaengold"],
    "Dividing ways of seeing the world into two.md": ["DanHitchens"],
    "God draws straight with crooked lines.md": ["DavidByrne"],
    "God's will.md": ["MeisterEckhart"],
    "Ignorance has the guilt of a vice.md": ["ANWhitehead"],
    "Independence is an unnatural state.md": ["JohnHenryNewman"],
    "Jesus is a pacifist.md": ["Gandhi"],
    "Love God and do what you will.md": ["StAugustine"],
    "Love is our true destiny.md": ["ThomasMerton"],
    "Make 'em wait.md": ["WilkieCollins"],
    "Marilynne Robinson on bad hymns.md": ["MarilynneRobinson"],
    "No other creed.md": ["GeoffreyFisher"],
    "Nothing is so silly.md": ["AndreGide"],
    "Ready for what comes next.md": ["GeorgeMacDonald"],
    "Scars.md": ["ElbertHubbard"],
    "Screw up as fast as possible.md": ["LeeUnkrich"],
    "The best way to complain.md": ["JamesMurphy"],
    "Trying to get with the plan.md": ["JamesMurphy"],
    "The family and work  economic justice.md": ["AlanJacobs"],
    "The goal of adulthood.md": ["ChrisBallas"],
    "The middle aged.md": ["GeorgeEliot"],
    "The questioning impulse is the creative catalyst.md": ["NickCave"],
    "The rich exist for the poor.md": ["StJohnChrysostom"],
    "What important truth.md": ["PeterThiel"],
    "What is chosen by others.md": ["AndreMaurois"],
    "What makes for good chanting.md": ["GHPalmer"],
    "Within that household.md": ["HilaireBelloc"],
    "audience capture and demonic possession.md": ["MaryHarrington"],
    "it is a wise thing to simulate craziness.md": ["MichaelAnton"],
    "rights and interests must be constantly asserted and defended.md": ["WendellBerry"],
    "the prophetic tone is offensive.md": ["TobySumpter"],
}


def parse_section3():
    txt = open(REPORT, encoding="utf-8").read()
    sec = txt.split("## 3.")[1]
    out = {}
    for line in sec.split("\n"):
        # line format: `filename.md → +Tag, +tag`
        m = re.match(r"^`(.+?\.md)\s*→\s*\+(.*)`$", line)
        if m:
            tags = [t.strip().lstrip("+") for t in m.group(2).split(",") if t.strip()]
            out[m.group(1)] = tags
    return out


def compute_pubs():
    out = {}
    for name in sorted(n for n in os.listdir(CONTENT) if n.endswith(".md") and n != "all-tags.md"):
        text = open(os.path.join(CONTENT, name), encoding="utf-8").read()
        fm = re.match(r"^---\n(.*?)\n---", text, re.S)
        existing = set(re.findall(r"^\s*-\s+(.+)$", fm.group(1), re.M)) if fm else set()
        tags = []
        for dom in extract_domains(text):
            if dom in SKIP_DOMAINS or dom.endswith(".substack.com"):
                continue
            tag = PUBLICATIONS.get(dom)
            if tag:
                tag = PUB_CORRECT.get(tag, tag)
                if tag not in existing:
                    tags.append(tag)
        if tags:
            out[name] = sorted(set(tags))
    for name, tags in PUB_EXTRA.items():
        out.setdefault(name, [])
        for t in tags:
            if t not in out[name]:
                out[name].append(t)
    return out


def merge_tags(text, tags):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return text, 0
    fm, body = m.group(1), text[m.end():]
    lines = fm.split("\n")
    existing = set()
    tag_idx = None
    for i, l in enumerate(lines):
        mt = re.match(r"^\s*-\s+(.+)$", l)
        if mt:
            existing.add(mt.group(1).strip())
        elif l.strip() == "tags:":
            tag_idx = i
    new_tags = [t for t in tags if t and t not in existing]
    if not new_tags:
        return text, 0
    if tag_idx is not None:
        insert_at = tag_idx + 1
        while insert_at < len(lines) and re.match(r"^\s*-\s+", lines[insert_at]):
            insert_at += 1
        lines = lines[:insert_at] + [f"  - {t}" for t in new_tags] + lines[insert_at:]
    else:
        lines = lines + ["tags:"] + [f"  - {t}" for t in new_tags]
    return "---\n" + "\n".join(lines) + "\n---" + body, len(new_tags)


def main():
    pubs = compute_pubs()
    sec3 = parse_section3()
    all_names = set(pubs) | set(AUTHOR_ADD) | set(sec3)
    changed = 0
    missing = []
    total_added = 0
    for name in sorted(all_names):
        path = os.path.join(CONTENT, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        tags = []
        tags += pubs.get(name, [])
        tags += AUTHOR_ADD.get(name, [])
        tags += sec3.get(name, [])
        tags = list(dict.fromkeys(tags))  # dedupe, preserve order
        text = open(path, encoding="utf-8").read()
        new_text, added_count = merge_tags(text, tags)
        if added_count:
            open(path, "w", encoding="utf-8").write(new_text)
            changed += 1
            total_added += added_count
    print(f"Files changed: {changed}")
    print(f"Total tags added (approx): {total_added}")
    if missing:
        print("MISSING FILES (check spelling):")
        for m in missing:
            print("  ", m)


if __name__ == "__main__":
    main()
