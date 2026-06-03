"""Evaluation framework for measuring agent performance."""

import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"
    COST = "cost"


@dataclass
class Metric:
    """A single metric measurement."""
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    evaluation_id: str
    task_id: str
    metrics: List[Metric]
    score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "task_id": self.task_id,
            "metrics": [
                {
                    "metric_id": m.metric_id,
                    "type": m.metric_type.value,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.metrics
            ],
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class MetricCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self):
        self.metrics: List[Metric] = []
    
    def record(
        self,
        metric_type: MetricType,
        value: float,
        metadata: Dict[str, Any] = None
    ) -> Metric:
        """Record a metric."""
        metric = Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:8]}",
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        return metric
    
    def get_metrics(
        self,
        metric_type: MetricType = None,
        limit: int = 100
    ) -> List[Metric]:
        """Get metrics, optionally filtered by type."""
        filtered = self.metrics
        if metric_type:
            filtered = [m for m in filtered if m.metric_type == metric_type]
        
        return filtered[-limit:]
    
    def get_average(
        self,
        metric_type: MetricType,
        limit: int = 100
    ) -> Optional[float]:
        """Get average value for a metric type."""
        metrics = self.get_metrics(metric_type, limit)
        if not metrics:
            return None
        
        return sum(m.value for m in metrics) / len(metrics)
    
    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()


class Evaluator:
    """Evaluates agent performance."""
    
    # 评分权重
    DEFAULT_WEIGHTS = {
        MetricType.ACCURACY: 0.3,
        MetricType.SUCCESS_RATE: 0.3,
        MetricType.LATENCY: 0.1,
        MetricType.TOKEN_USAGE: 0.1,
        MetricType.USER_SATISFACTION: 0.2
    }
    
    def __init__(self, storage_dir: str = ".memoryai/evaluations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.collector = MetricCollector()
        self.results: List[EvaluationResult] = []
        self._load_results()
    
    def _load_results(self):
        """Load evaluation results from disk."""
        results_file = self.storage_dir / "results.json"
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text())
                for item in data:
                    metrics = [
                        Metric(
                            metric_id=m["metric_id"],
                            metric_type=MetricType(m["type"]),
                            value=m["value"],
                            timestamp=datetime.fromisoformat(m["timestamp"])
                        )
                        for m in item.get("metrics", [])
                    ]
                    
                    result = EvaluationResult(
                        evaluation_id=item["evaluation_id"],
                        task_id=item["task_id"],
                        metrics=metrics,
                        score=item["score"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        metadata=item.get("metadata", {})
                    )
                    self.results.append(result)
            except Exception as e:
                logger.error(f"Failed to load evaluation results: {e}")
    
    def _save_results(self):
        """Save evaluation results to disk."""
        results_file = self.storage_dir / "results.json"
        data = [r.to_dict() for r in self.results]
        results_file.write_text(json.dumps(data, indent=2))
    
    def evaluate(
        self,
        task_id: str,
        metrics: Dict[MetricType, float] = None,
        weights: Dict[MetricType, float] = None
    ) -> EvaluationResult:
        """Evaluate agent performance."""
        # 使用提供的指标或从收集器获取
        if metrics:
            metric_list = [
                Metric(
                    metric_id=f"metric_{uuid.uuid4().hex[:8]}",
                    metric_type=mt,
                    value=value,
                    timestamp=datetime.now()
                )
                for mt, value in metrics.items()
            ]
        else:
            metric_list = self.collector.get_metrics()
        
        # 计算综合分数
        weights = weights or self.DEFAULT_WEIGHTS
        score = self._calculate_score(metric_list, weights)
        
        result = EvaluationResult(
            evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            metrics=metric_list,
            score=score,
            timestamp=datetime.now()
        )
        
        self.results.append(result)
        self._save_results()
        
        logger.info(f"Evaluation complete: {result.evaluation_id} (score: {score:.2f})")
        return result
    
    def _calculate_score(
        self,
        metrics: List[Metric],
        weights: Dict[MetricType, float]
    ) -> float:
        """Calculate weighted score."""
        if not metrics:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weight = weights.get(metric.metric_type, 0.1)
            weighted_sum += metric.value * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def get_evaluation(
        self,
        evaluation_id: str
    ) -> Optional[EvaluationResult]:
        """Get evaluation by ID."""
        for result in self.results:
            if result.evaluation_id == evaluation_id:
                return result
        return None
    
    def get_task_evaluations(
        self,
        task_id: str,
        limit: int = 10
    ) -> List[EvaluationResult]:
        """Get evaluations for a task."""
        task_results = [
            r for r in self.results
            if r.task_id == task_id
        ]
        
        task_results.sort(key=lambda r: r.timestamp, reverse=True)
        return task_results[:limit]
    
    def get_average_score(
        self,
        task_id: str = None,
        limit: int = 100
    ) -> Optional[float]:
        """Get average evaluation score."""
        results = self.results
        if task_id:
            results = [r for r in results if r.task_id == task_id]
        
        if not results:
            return None
        
        return sum(r.score for r in results[-limit:]) / len(results[-limit:])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        total = len(self.results)
        
        if total == 0:
            return {
                "total_evaluations": 0,
                "average_score": None,
                "by_task": {}
            }
        
        # 按任务统计
        by_task = {}
        for result in self.results:
            task_id = result.task_id
            if task_id not in by_task:
                by_task[task_id] = {"count": 0, "total_score": 0.0}
            by_task[task_id]["count"] += 1
            by_task[task_id]["total_score"] += result.score
        
        # 计算平均分
        for task_id in by_task:
            count = by_task[task_id]["count"]
            by_task[task_id]["average_score"] = by_task[task_id]["total_score"] / count
        
        total_score = sum(r.score for r in self.results)
        
        return {
            "total_evaluations": total,
            "average_score": total_score / total,
            "by_task": by_task
        }
    
    def clear(self):
        """Clear all results."""
        self.results.clear()
        self._save_results()


class BenchmarkSuite:
    """Suite of benchmark tests."""
    
    def __init__(self, name: str):
        self.name = name
        self.tests: List[Dict[str, Any]] = []
    
    def add_test(
        self,
        name: str,
        test_func: Callable,
        expected_result: Any = None
    ):
        """Add a benchmark test."""
        self.tests.append({
            "name": name,
            "test_func": test_func,
            "expected_result": expected_result
        })
    
    async def run(self, evaluator: Evaluator) -> List[EvaluationResult]:
        """Run all benchmark tests."""
        results = []
        
        for test in self.tests:
            try:
                # 运行测试
                result = await test["test_func"]()
                
                # 计算准确度
                accuracy = 1.0
                if test["expected_result"] is not None:
                    accuracy = 1.0 if result == test["expected_result"] else 0.0
                
                # 评估
                eval_result = evaluator.evaluate(
                    task_id=f"benchmark_{self.name}_{test['name']}",
                    metrics={
                        MetricType.ACCURACY: accuracy,
                        MetricType.SUCCESS_RATE: 1.0
                    }
                )
                
                results.append(eval_result)
                
            except Exception as e:
                logger.error(f"Benchmark test '{test['name']}' failed: {e}")
        
        return results


# 全局评估器实例
_evaluator: Optional[Evaluator] = None


def get_evaluator() -> Evaluator:
    """Get or create global evaluator."""
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator()
    return _evaluator
