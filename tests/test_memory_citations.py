from src.memory.citations import build_citations, MemoryCitation


def test_build_citations_from_retrieve_dict():
    results = [
        {
            "memory_id": "user1_user_abc",
            "memory_type": "user",
            "description": "偏好",
            "content": "用户喜欢 Python",
            "score": 0.85,
            "age_days": 2,
            "is_stale": True,
            "source_session_id": "sess-1",
            "source_quote": "用户说过喜欢 Python",
            "evidence_level": "L1",
            "judge_reason": "overlap,not_superseded",
        }
    ]
    citations = build_citations(results, selection_reason="keyword+vector")
    assert len(citations) == 1
    c = citations[0]
    assert isinstance(c, MemoryCitation)
    assert c.memory_id == "user1_user_abc"
    assert c.score == 0.85
    assert c.is_stale is True
    assert "Python" in c.content_snippet
    assert c.source_session_id == "sess-1"
    assert c.source_quote == "用户说过喜欢 Python"
    assert c.judge_reason == "overlap,not_superseded"
