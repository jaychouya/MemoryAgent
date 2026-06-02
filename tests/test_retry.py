"""Tests for retry mechanism."""
import pytest
import asyncio
from src.agent.retry import (
    RetryPolicy,
    RetryManager,
    CircuitBreaker,
    CircuitState,
    RetryWithCircuitBreaker
)


@pytest.mark.asyncio
async def test_retry_succeeds_on_first_try():
    """应该在第一次尝试成功时返回结果。"""
    manager = RetryManager(RetryPolicy(max_retries=3))
    
    call_count = 0
    
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await manager.execute_with_retry(success_func)
    
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_retries_on_failure():
    """应该在失败时重试。"""
    manager = RetryManager(RetryPolicy(max_retries=3, base_delay=0.1))
    
    call_count = 0
    
    async def fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("fail")
        return "success"
    
    result = await manager.execute_with_retry(fail_then_succeed)
    
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exponential_backoff():
    """应该使用指数退避延迟。"""
    policy = RetryPolicy(max_retries=3, base_delay=1.0, exponential_base=2.0)
    manager = RetryManager(policy)
    
    assert manager.calculate_delay(0) == 1.0
    assert manager.calculate_delay(1) == 2.0
    assert manager.calculate_delay(2) == 4.0


@pytest.mark.asyncio
async def test_retry_max_delay():
    """应该限制最大延迟。"""
    policy = RetryPolicy(max_retries=3, base_delay=1.0, max_delay=5.0)
    manager = RetryManager(policy)
    
    assert manager.calculate_delay(10) == 5.0


def test_circuit_breaker_starts_closed():
    """断路器应该初始状态为关闭。"""
    breaker = CircuitBreaker()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.can_execute() is True


def test_circuit_breaker_opens_on_failures():
    """断路器应该在失败次数达到阈值后打开。"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    for _ in range(3):
        breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.can_execute() is False


def test_circuit_breaker_resets_on_success():
    """断路器应该在成功后重置。"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.failure_count == 2
    
    breaker.record_success()
    assert breaker.failure_count == 0
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_retry_with_circuit_breaker():
    """应该结合重试和断路器。"""
    manager = RetryWithCircuitBreaker(
        retry_policy=RetryPolicy(max_retries=2, base_delay=0.1),
        circuit_breaker=CircuitBreaker(failure_threshold=3)
    )
    
    call_count = 0
    
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await manager.execute(success_func)
    
    assert result == "success"
    assert call_count == 1
