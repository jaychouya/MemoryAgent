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
