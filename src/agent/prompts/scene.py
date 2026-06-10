"""Detect chat scene for prompt branching."""

import re
from typing import Literal

Scene = Literal["exam", "general"]

_EXAM_HINTS = re.compile(
    r"考研|真题|讲义|高等数学|概率论|线性代数|二重积分|三重积分|"
    r"极限|微分|积分|求导|矩阵|特征值|拉格朗日|贝叶斯|"
    r"\\int|\\frac|题目\d|##\s*题目",
    re.I,
)


def detect_scene(user_message: str) -> Scene:
    text = (user_message or "").strip()
    if not text:
        return "general"
    if _EXAM_HINTS.search(text):
        return "exam"
    return "general"
