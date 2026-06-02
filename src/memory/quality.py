"""Memory quality management - scoring, cleanup, and conflict detection."""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MemoryQualityScore:
    """Quality score for a memory."""
    relevance: float = 0.0
    freshness: float = 0.0
    specificity: float = 0.0
    importance: float = 0.0
    overall: float = 0.0


class MemoryQualityManager:
    """Manages memory quality - scoring, cleanup, and conflict detection."""
    
    # 低质量记忆的阈值
    LOW_QUALITY_THRESHOLD = 0.3
    # 过期记忆的天数
    STALE_DAYS = 30
    # 冲突检测的相似度阈值
    SIMILARITY_THRESHOLD = 0.8
    
    def __init__(self, storage_dir: str = "memories"):
        self.storage_dir = Path(storage_dir)
    
    def score_memory(self, memory: Dict[str, Any]) -> MemoryQualityScore:
        """Score a memory based on multiple factors."""
        content = memory.get("content", "")
        metadata = memory.get("metadata", {})
        created_at = memory.get("created_at")
        
        # 相关性评分（基于内容长度和关键词）
        relevance = self._score_relevance(content)
        
        # 新鲜度评分（基于创建时间）
        freshness = self._score_freshness(created_at)
        
        # 具体性评分（基于内容细节）
        specificity = self._score_specificity(content)
        
        # 重要性评分（基于元数据）
        importance = self._score_importance(metadata)
        
        # 综合评分
        overall = (relevance * 0.3 + freshness * 0.2 + 
                   specificity * 0.3 + importance * 0.2)
        
        return MemoryQualityScore(
            relevance=relevance,
            freshness=freshness,
            specificity=specificity,
            importance=importance,
            overall=overall
        )
    
    def _score_relevance(self, content: str) -> float:
        """Score relevance based on content quality."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # 长度评分（太短或太长都扣分）
        length = len(content)
        if length < 10:
            score += 0.2
        elif length < 50:
            score += 0.5
        elif length < 200:
            score += 0.8
        else:
            score += 0.6
        
        # 关键词评分
        keywords = ["喜欢", "偏好", "习惯", "不要", "必须", "重要", "关键"]
        for keyword in keywords:
            if keyword in content:
                score += 0.1
        
        return min(1.0, score)
    
    def _score_freshness(self, created_at: Optional[str]) -> float:
        """Score freshness based on creation time."""
        if not created_at:
            return 0.5
        
        try:
            if isinstance(created_at, str):
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created = created_at
            
            age_days = (datetime.now() - created.replace(tzinfo=None)).days
            
            if age_days < 1:
                return 1.0
            elif age_days < 7:
                return 0.9
            elif age_days < 30:
                return 0.7
            elif age_days < 90:
                return 0.5
            else:
                return 0.3
        except:
            return 0.5
    
    def _score_specificity(self, content: str) -> float:
        """Score specificity based on content details."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # 包含数字
        if re.search(r'\d+', content):
            score += 0.2
        
        # 包含专有名词（大写字母开头的词）
        if re.search(r'[A-Z][a-z]+', content):
            score += 0.2
        
        # 包含具体描述
        if len(content) > 50:
            score += 0.3
        
        # 包含时间信息
        time_patterns = ["今天", "昨天", "明天", "下周", "下个月", "截止"]
        for pattern in time_patterns:
            if pattern in content:
                score += 0.1
                break
        
        return min(1.0, score)
    
    def _score_importance(self, metadata: Dict[str, Any]) -> float:
        """Score importance based on metadata."""
        if not metadata:
            return 0.5
        
        score = 0.5
        
        # 用户标记的重要性
        if "importance" in metadata:
            try:
                score = float(metadata["importance"])
            except:
                pass
        
        # 记忆类型权重
        type_weights = {
            "feedback": 0.9,  # 行为反馈最重要
            "user": 0.8,      # 用户偏好次之
            "project": 0.7,   # 项目动态
            "reference": 0.6  # 外部引用
        }
        
        memory_type = metadata.get("type", "")
        if memory_type in type_weights:
            score = (score + type_weights[memory_type]) / 2
        
        return min(1.0, score)
    
    def detect_conflicts(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicting memories."""
        conflicts = []
        
        for i, mem1 in enumerate(memories):
            for j, mem2 in enumerate(memories[i+1:], i+1):
                if self._are_conflicting(mem1, mem2):
                    conflicts.append({
                        "memory1": mem1,
                        "memory2": mem2,
                        "reason": "内容冲突"
                    })
        
        return conflicts
    
    def _are_conflicting(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> bool:
        """Check if two memories are conflicting."""
        content1 = mem1.get("content", "").lower()
        content2 = mem2.get("content", "").lower()
        
        # 简单的冲突检测
        # 检查是否有相反的表述
        opposite_pairs = [
            ("喜欢", "讨厌"),
            ("偏好", "避免"),
            ("必须", "不要"),
            ("开启", "关闭"),
            ("启用", "禁用")
        ]
        
        for word1, word2 in opposite_pairs:
            if word1 in content1 and word2 in content2:
                # 检查是否讨论同一主题
                if self._same_topic(content1, content2):
                    return True
            if word2 in content1 and word1 in content2:
                if self._same_topic(content1, content2):
                    return True
        
        return False
    
    def _same_topic(self, content1: str, content2: str) -> bool:
        """Check if two contents are about the same topic."""
        # 提取关键词（中文和英文）
        words1 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content2))
        
        # 计算交集比例
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union)
        return similarity > 0.3
    
    def get_low_quality_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get memories with low quality scores."""
        low_quality = []
        
        for memory in memories:
            score = self.score_memory(memory)
            if score.overall < self.LOW_QUALITY_THRESHOLD:
                low_quality.append({
                    "memory": memory,
                    "score": score,
                    "reasons": self._get_low_quality_reasons(score)
                })
        
        return low_quality
    
    def _get_low_quality_reasons(self, score: MemoryQualityScore) -> List[str]:
        """Get reasons why memory is low quality."""
        reasons = []
        
        if score.relevance < 0.3:
            reasons.append("内容相关性低")
        if score.freshness < 0.3:
            reasons.append("记忆过期")
        if score.specificity < 0.3:
            reasons.append("内容不够具体")
        if score.importance < 0.3:
            reasons.append("重要性低")
        
        return reasons
    
    def get_stale_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get memories that are stale (old)."""
        stale = []
        cutoff_date = datetime.now() - timedelta(days=self.STALE_DAYS)
        
        for memory in memories:
            created_at = memory.get("created_at")
            if not created_at:
                continue
            
            try:
                if isinstance(created_at, str):
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created = created_at
                
                if created.replace(tzinfo=None) < cutoff_date:
                    stale.append(memory)
            except:
                continue
        
        return stale
    
    def cleanup_memories(
        self,
        memories: List[Dict[str, Any]],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Cleanup low quality and stale memories."""
        low_quality = self.get_low_quality_memories(memories)
        stale = self.get_stale_memories(memories)
        
        # 合并需要清理的记忆
        to_cleanup = []
        seen_ids = set()
        
        for item in low_quality:
            memory = item["memory"]
            memory_id = memory.get("id", "")
            if memory_id not in seen_ids:
                to_cleanup.append({
                    "memory": memory,
                    "reasons": item["reasons"]
                })
                seen_ids.add(memory_id)
        
        for memory in stale:
            memory_id = memory.get("id", "")
            if memory_id not in seen_ids:
                to_cleanup.append({
                    "memory": memory,
                    "reasons": ["记忆过期"]
                })
                seen_ids.add(memory_id)
        
        result = {
            "total_memories": len(memories),
            "low_quality_count": len(low_quality),
            "stale_count": len(stale),
            "to_cleanup_count": len(to_cleanup),
            "dry_run": dry_run,
            "to_cleanup": to_cleanup
        }
        
        if not dry_run:
            # 实际清理逻辑（这里只是标记，实际删除需要调用存储层）
            result["cleaned"] = len(to_cleanup)
        
        return result
