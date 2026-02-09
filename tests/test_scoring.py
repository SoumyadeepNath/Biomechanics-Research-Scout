from biomechanics_research_app import Paper, paper_score


def make_paper(title: str, year: int, citations: int, concepts: list[str]) -> Paper:
    return Paper(
        title=title,
        year=year,
        venue="Test Journal",
        url="https://example.com",
        cited_by_count=citations,
        concepts=concepts,
        authors=["A. Author"],
        abstract="",
    )


def test_score_prefers_topic_and_recency():
    topic = "gait biomechanics"
    highly_relevant_recent = make_paper(
        "Gait biomechanics with wearable sensors", 2024, 30, ["Gait", "Biomechanics"]
    )
    older_less_relevant = make_paper(
        "Bone density study", 2014, 300, ["Orthopedics"]
    )

    assert paper_score(highly_relevant_recent, topic) > paper_score(older_less_relevant, topic)


def test_score_increases_with_citations_when_other_factors_equal():
    topic = "tendon mechanics"
    low = make_paper("Tendon mechanics", 2022, 10, ["Tendon", "Mechanics"])
    high = make_paper("Tendon mechanics", 2022, 200, ["Tendon", "Mechanics"])

    assert paper_score(high, topic) > paper_score(low, topic)
