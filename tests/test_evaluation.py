"""Tests for evaluation framework."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.agent.evaluation import (
    Evaluator,
    MetricCollector,
    Metric,
    MetricType,
    EvaluationResult,
    BenchmarkSuite,
    get_evaluator
)


@pytest.fixture
def evaluator():
    """Create a temporary evaluator."""
    temp_dir = tempfile.mkdtemp()
    eval = Evaluator(storage_dir=temp_dir)
    yield eval
    shutil.rmtree(temp_dir)


def test_evaluator_creates():
    """Evaluator 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        eval = Evaluator(storage_dir=temp_dir)
        assert eval is not None


def test_metric_collector_record():
    """MetricCollector.record 应该记录指标。"""
    collector = MetricCollector()
    
    metric = collector.record(
        metric_type=MetricType.ACCURACY,
        value=0.95
    )
    
    assert metric is not None
    assert metric.metric_type == MetricType.ACCURACY
    assert metric.value == 0.95


def test_metric_collector_get_metrics():
    """MetricCollector.get_metrics 应该获取指标。"""
    collector = MetricCollector()
    
    collector.record(MetricType.ACCURACY, 0.9)
    collector.record(MetricType.LATENCY, 100.0)
    collector.record(MetricType.ACCURACY, 0.95)
    
    metrics = collector.get_metrics(MetricType.ACCURACY)
    
    assert len(metrics) == 2


def test_metric_collector_get_average():
    """MetricCollector.get_average 应该计算平均值。"""
    collector = MetricCollector()
    
    collector.record(MetricType.ACCURACY, 0.9)
    collector.record(MetricType.ACCURACY, 0.8)
    collector.record(MetricType.ACCURACY, 0.7)
    
    avg = collector.get_average(MetricType.ACCURACY)
    
    assert abs(avg - 0.8) < 0.01


def test_evaluate(evaluator):
    """evaluate 应该评估性能。"""
    result = evaluator.evaluate(
        task_id="task_1",
        metrics={
            MetricType.ACCURACY: 0.9,
            MetricType.SUCCESS_RATE: 0.95
        }
    )
    
    assert result is not None
    assert result.task_id == "task_1"
    assert result.score > 0


def test_evaluate_with_collector(evaluator):
    """evaluate 应该使用收集器的指标。"""
    evaluator.collector.record(MetricType.ACCURACY, 0.9)
    evaluator.collector.record(MetricType.SUCCESS_RATE, 0.95)
    
    result = evaluator.evaluate(task_id="task_1")
    
    assert result is not None
    assert len(result.metrics) == 2


def test_get_evaluation(evaluator):
    """get_evaluation 应该获取评估结果。"""
    result = evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.9}
    )
    
    retrieved = evaluator.get_evaluation(result.evaluation_id)
    
    assert retrieved is not None
    assert retrieved.evaluation_id == result.evaluation_id


def test_get_task_evaluations(evaluator):
    """get_task_evaluations 应该获取任务的评估结果。"""
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.9}
    )
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.95}
    )
    evaluator.evaluate(
        task_id="task_2",
        metrics={MetricType.ACCURACY: 0.8}
    )
    
    results = evaluator.get_task_evaluations("task_1")
    
    assert len(results) == 2


def test_get_average_score(evaluator):
    """get_average_score 应该计算平均分。"""
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.9}
    )
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.8}
    )
    
    avg = evaluator.get_average_score("task_1")
    
    assert avg is not None
    assert avg > 0


def test_get_stats(evaluator):
    """get_stats 应该返回统计信息。"""
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.9}
    )
    evaluator.evaluate(
        task_id="task_2",
        metrics={MetricType.ACCURACY: 0.8}
    )
    
    stats = evaluator.get_stats()
    
    assert stats["total_evaluations"] == 2
    assert stats["average_score"] is not None
    assert "task_1" in stats["by_task"]


def test_evaluation_result_to_dict():
    """EvaluationResult.to_dict 应该转换为字典。"""
    metrics = [
        Metric(
            metric_id="m1",
            metric_type=MetricType.ACCURACY,
            value=0.9,
            timestamp=datetime.now()
        )
    ]
    
    result = EvaluationResult(
        evaluation_id="eval_1",
        task_id="task_1",
        metrics=metrics,
        score=0.9,
        timestamp=datetime.now()
    )
    
    data = result.to_dict()
    
    assert data["evaluation_id"] == "eval_1"
    assert data["task_id"] == "task_1"
    assert len(data["metrics"]) == 1


def test_benchmark_suite():
    """BenchmarkSuite 应该能创建。"""
    suite = BenchmarkSuite("test_suite")
    
    assert suite is not None
    assert suite.name == "test_suite"


def test_benchmark_suite_add_test():
    """BenchmarkSuite.add_test 应该添加测试。"""
    suite = BenchmarkSuite("test_suite")
    
    async def test_func():
        return True
    
    suite.add_test("test1", test_func, expected_result=True)
    
    assert len(suite.tests) == 1


@pytest.mark.asyncio
async def test_benchmark_suite_run(evaluator):
    """BenchmarkSuite.run 应该运行测试。"""
    suite = BenchmarkSuite("test_suite")
    
    async def test_func():
        return True
    
    suite.add_test("test1", test_func, expected_result=True)
    
    results = await suite.run(evaluator)
    
    assert len(results) == 1
    assert results[0].score > 0


def test_evaluator_clear(evaluator):
    """clear 应该清空结果。"""
    evaluator.evaluate(
        task_id="task_1",
        metrics={MetricType.ACCURACY: 0.9}
    )
    
    assert len(evaluator.results) == 1
    
    evaluator.clear()
    
    assert len(evaluator.results) == 0


def test_get_evaluator_singleton():
    """get_evaluator 应该返回单例。"""
    eval1 = get_evaluator()
    eval2 = get_evaluator()
    
    assert eval1 is eval2
