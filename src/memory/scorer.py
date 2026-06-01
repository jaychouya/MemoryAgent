"""Memory scorer for evaluating importance."""

import re
from typing import Dict


class MemoryScorer:
    """
    Score memory importance.
    
    Scoring factors:
    - Content length (longer = more important)
    - Keyword presence (preference words, action words)
    - Memory type (feedback > user > project > reference)
    - Specificity (specific > vague)
    """
    
    # 类型权重
    TYPE_WEIGHTS = {
        "feedback": 0.9,  # 行为反馈最重要
        "user": 0.8,      # 用户偏好次之
        "project": 0.7,   # 项目动态
        "reference": 0.6  # 外部引用
    }
    
    # 关键词权重
    KEYWORD_WEIGHTS = {
        # 偏好词
        "喜欢": 0.1, "讨厌": 0.1, "偏好": 0.1, "习惯": 0.1,
        # 行为词
        "不要": 0.15, "必须": 0.15, "应该": 0.1, "避免": 0.15,
        # 时间词
        "截止": 0.1, "deadline": 0.1, "紧急": 0.15,
        # 重要词
        "重要": 0.1, "关键": 0.1, "核心": 0.1
    }
    
    def score(self, content: str, memory_type: str) -> float:
        """
        Score memory importance.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        
        # 1. 类型基础分
        score += self.TYPE_WEIGHTS.get(memory_type, 0.5) * 0.3
        
        # 2. 内容长度分（对数缩放）
        length_score = min(1.0, len(content) / 100)  # 100字满分
        score += length_score * 0.2
        
        # 3. 关键词分
        keyword_score = 0.0
        for keyword, weight in self.KEYWORD_WEIGHTS.items():
            if keyword in content:
                keyword_score += weight
        keyword_score = min(1.0, keyword_score)
        score += keyword_score * 0.3
        
        # 4. 具体性分（包含数字、专有名词等）
        specificity_score = 0.0
        if re.search(r'\d+', content):  # 包含数字
            specificity_score += 0.3
        if re.search(r'[A-Z][a-z]+', content):  # 包含专有名词
            specificity_score += 0.3
        if len(content) > 20:  # 足够详细
            specificity_score += 0.4
        specificity_score = min(1.0, specificity_score)
        score += specificity_score * 0.2
        
        return min(1.0, score)
