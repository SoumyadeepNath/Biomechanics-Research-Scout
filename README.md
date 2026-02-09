# Biomechanics Research Scout

A lightweight Python app that takes a biomechanics topic and returns:

1. Relevant research articles (via OpenAlex)
2. A quick **state-of-the-art** snapshot (themes, venues, and top papers)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python biomechanics_research_app.py "ACL injury prevention gait analysis"
```

## Options

```bash
python biomechanics_research_app.py "muscle synergies in running" --max-results 40 --save-json results.json
```

## How it works

- Queries OpenAlex for the topic.
- Computes a composite score for each paper using topicality, recency, and citation impact.
- Produces a concise Markdown-style SOTA summary.

## Notes

- OpenAlex metadata quality varies by paper.
- The output is meant for rapid scouting, not a systematic review.

- If your environment blocks outbound network access, API retrieval will fail gracefully with a helpful error message.
