from src.memory.recall_judge import filter_relevant_memories, judge_memories


def test_recall_judge_drops_superseded_memory():
    memories = [
        {
            "memory_id": "u1_user_old",
            "content": "我主要使用 Python",
            "memory_type": "user",
            "user_id": "u1",
            "superseded_by": "u1_user_new",
        },
        {
            "memory_id": "u1_user_new",
            "content": "我主要使用 Rust",
            "memory_type": "user",
            "user_id": "u1",
        },
    ]

    judged = judge_memories("主要使用什么", memories, user_id="u1")

    assert [m["memory_id"] for m in judged] == ["u1_user_new"]
    assert judged[0]["judge_score"] > 0
    assert judged[0]["judge_reason"]


def test_recall_judge_keeps_relevant_chinese_preference():
    judged = judge_memories(
        "我喜欢什么编程语言",
        [
            {
                "memory_id": "u1_user_lang",
                "content": "用户喜欢 Python 编程",
                "memory_type": "user",
                "user_id": "u1",
            },
            {
                "memory_id": "u1_reference_docs",
                "content": "文档地址在 docs/README.md",
                "memory_type": "reference",
                "user_id": "u1",
            },
        ],
        user_id="u1",
    )

    assert judged[0]["memory_id"] == "u1_user_lang"
    assert judged[0]["judge_score"] >= judged[-1]["judge_score"]


def test_recall_judge_drops_scope_mismatch():
    judged = judge_memories(
        "喜欢 Python",
        [
            {
                "memory_id": "u2_user_lang",
                "content": "用户喜欢 Python",
                "memory_type": "user",
                "user_id": "u2",
            }
        ],
        user_id="u1",
    )

    assert judged == []


def test_filter_relevant_memories_drops_zero_overlap():
    raw = [
        {
            "memory_id": "u1_user_pref",
            "content": "我偏好代码直接、少解释",
            "memory_type": "user",
            "user_id": "u1",
            "score": 0.2,
        },
        {
            "memory_id": "u1_user_math",
            "content": "用户想学习考研高数",
            "memory_type": "user",
            "user_id": "u1",
            "score": 0.1,
        },
    ]
    kept = filter_relevant_memories("这是什么原因", raw)
    assert kept == []
