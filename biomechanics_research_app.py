#!/usr/bin/env python3
"""Biomechanics research discovery app.

Given a biomechanics topic, this app:
1. Fetches relevant papers from OpenAlex.
2. Scores and ranks papers by relevance and impact.
3. Produces a concise "state-of-the-art" summary based on recent trends.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
USER_AGENT = "BiomechanicsResearchScout/1.0 (educational-use)"
CURRENT_YEAR = dt.datetime.utcnow().year


@dataclass
class Paper:
    title: str
    year: int | None
    venue: str
    url: str
    cited_by_count: int
    concepts: list[str]
    authors: list[str]
    abstract: str


def _decode_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for token, idxs in inverted_index.items():
        for idx in idxs:
            positions[idx] = token
    return " ".join(token for _, token in sorted(positions.items()))


def fetch_articles(topic: str, max_results: int = 30, timeout_s: int = 20) -> list[Paper]:
    params = {
        "search": topic,
        "per-page": max(5, min(max_results, 50)),
        "sort": "relevance_score:desc",
    }
    query = urlencode(params)
    req = Request(f"{OPENALEX_WORKS_URL}?{query}", headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout_s) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results", [])
    papers: list[Paper] = []

    for item in results:
        primary_location = item.get("primary_location") or {}
        source = primary_location.get("source") or {}
        venue = source.get("display_name") or "Unknown venue"

        authorships = item.get("authorships") or []
        authors = [
            a.get("author", {}).get("display_name", "Unknown")
            for a in authorships[:5]
        ]

        concepts = [
            c.get("display_name", "")
            for c in (item.get("concepts") or [])
            if c.get("score", 0) >= 0.3
        ][:8]

        papers.append(
            Paper(
                title=item.get("display_name", "Untitled"),
                year=item.get("publication_year"),
                venue=venue,
                url=item.get("id", ""),
                cited_by_count=item.get("cited_by_count", 0),
                concepts=[c for c in concepts if c],
                authors=[a for a in authors if a],
                abstract=_decode_abstract(item.get("abstract_inverted_index")),
            )
        )

    return papers


def paper_score(paper: Paper, topic: str) -> float:
    """Composite score balancing topical match, recency, and impact."""
    topic_terms = {t.lower() for t in topic.split() if t.strip()}
    text_blob = f"{paper.title} {' '.join(paper.concepts)} {paper.abstract}".lower()
    term_hits = sum(1 for t in topic_terms if t in text_blob)
    topicality = term_hits / max(len(topic_terms), 1)

    if paper.year:
        age = max(CURRENT_YEAR - paper.year, 0)
        recency = math.exp(-age / 5.0)
    else:
        recency = 0.2

    impact = math.log1p(max(paper.cited_by_count, 0)) / 10.0

    return 0.5 * topicality + 0.3 * recency + 0.2 * impact


def summarize_state_of_art(papers: list[Paper], topic: str) -> str:
    if not papers:
        return "No papers found. Try a broader or alternate topic wording."

    scored = sorted(papers, key=lambda p: paper_score(p, topic), reverse=True)
    top_papers = scored[:5]

    recent_cutoff = CURRENT_YEAR - 3
    recent = [p for p in papers if p.year and p.year >= recent_cutoff]

    concept_counts = Counter(
        c.lower() for p in recent for c in p.concepts if c.strip()
    )
    top_concepts = [c for c, _ in concept_counts.most_common(6)]

    venue_counts = Counter(p.venue for p in papers if p.venue)
    top_venues = [v for v, _ in venue_counts.most_common(4)]

    lines = []
    lines.append(f"## State of the Art Snapshot: {topic}")
    lines.append("")
    lines.append(
        f"Analyzed **{len(papers)}** papers, including **{len(recent)}** from {recent_cutoff}-{CURRENT_YEAR}."
    )
    lines.append("")
    lines.append("### Emerging / Dominant Themes")
    if top_concepts:
        for c in top_concepts:
            lines.append(f"- {c.title()}")
    else:
        lines.append("- Not enough concept metadata to infer themes.")

    lines.append("")
    lines.append("### Influential Venues")
    for v in top_venues:
        lines.append(f"- {v}")

    lines.append("")
    lines.append("### High-Priority Papers to Read")
    for p in top_papers:
        year = p.year or "n.d."
        lines.append(
            f"- **{p.title}** ({year}) — {', '.join(p.authors[:3]) or 'Unknown authors'}; "
            f"{p.venue}; citations: {p.cited_by_count}."
        )
        if p.url:
            lines.append(f"  - {p.url}")

    lines.append("")
    lines.append("### Practical Next Steps")
    lines.append(
        "- Start with the high-priority papers above and follow their recent citing papers for frontier updates."
    )
    lines.append(
        "- Narrow your topic (e.g., specific tissue, movement, or sensing method) and re-run for a targeted SOTA brief."
    )
    lines.append(
        "- Validate algorithmic methods and datasets recurring across top concepts before selecting your project direction."
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find biomechanics research papers and summarize current state-of-the-art."
    )
    parser.add_argument("topic", help="Biomechanics topic, e.g. 'ACL injury prevention gait analysis'")
    parser.add_argument("--max-results", type=int, default=30, help="Number of papers to fetch (max 50)")
    parser.add_argument("--save-json", default="", help="Optional path to save raw structured results as JSON")
    args = parser.parse_args()

    try:
        papers = fetch_articles(args.topic, max_results=args.max_results)
    except URLError as exc:
        print("Could not reach OpenAlex API (network/proxy issue).")
        print(f"Details: {exc}")
        return

    report = summarize_state_of_art(papers, args.topic)
    print(report)

    if args.save_json:
        serializable = [
            {
                "title": p.title,
                "year": p.year,
                "venue": p.venue,
                "url": p.url,
                "cited_by_count": p.cited_by_count,
                "concepts": p.concepts,
                "authors": p.authors,
                "abstract": p.abstract,
            }
            for p in papers
        ]
        with open(args.save_json, "w", encoding="utf-8") as fh:
            json.dump(serializable, fh, indent=2)


if __name__ == "__main__":
    main()
