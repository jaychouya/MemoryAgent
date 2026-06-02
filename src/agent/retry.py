"""Error retry mechanism with exponential backoff."""

import asyncio
import logging
import time
from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetryPolicy:
    """Retry policy configuration."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def record_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(self, policy: RetryPolicy = None):
        self.policy = policy or RetryPolicy()
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        delay = self.policy.base_delay * (self.policy.exponential_base ** attempt)
        return min(delay, self.policy.max_delay)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.policy.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.policy.max_retries + 1} attempts failed: {e}"
                    )
        
        raise last_exception


class RetryWithCircuitBreaker:
    """Retry manager with circuit breaker integration."""
    
    def __init__(
        self,
        retry_policy: RetryPolicy = None,
        circuit_breaker: CircuitBreaker = None
    ):
        self.retry_manager = RetryManager(retry_policy)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute with retry and circuit breaker."""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")
        
        try:
            result = await self.retry_manager.execute_with_retry(
                func, *args, **kwargs
            )
            self.circuit_breaker.record_success()
            return result
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
