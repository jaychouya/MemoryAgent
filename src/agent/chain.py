"""Chain abstraction for composable operations."""

import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ChainNodeType(str, Enum):
    """Types of chain nodes."""
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    CONDITION = "condition"
    PARALLEL = "parallel"


@dataclass
class ChainContext:
    """Context passed through chain execution."""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value in context."""
        self.data[key] = value
    
    def update(self, data: Dict[str, Any]):
        """Update context data."""
        self.data.update(data)


class ChainNode:
    """A node in a chain."""
    
    def __init__(
        self,
        name: str,
        func: Callable[[ChainContext], Awaitable[ChainContext]],
        node_type: ChainNodeType = ChainNodeType.TRANSFORM
    ):
        self.name = name
        self.func = func
        self.node_type = node_type
    
    async def execute(self, context: ChainContext) -> ChainContext:
        """Execute this node."""
        try:
            return await self.func(context)
        except Exception as e:
            logger.error(f"Chain node '{self.name}' failed: {e}")
            context.errors.append(f"{self.name}: {str(e)}")
            return context


class Chain:
    """A chain of composable operations."""
    
    def __init__(self, name: str = "chain"):
        self.name = name
        self.nodes: List[ChainNode] = []
    
    def add(
        self,
        name: str,
        func: Callable[[ChainContext], Awaitable[ChainContext]],
        node_type: ChainNodeType = ChainNodeType.TRANSFORM
    ) -> "Chain":
        """Add a node to the chain."""
        node = ChainNode(name, func, node_type)
        self.nodes.append(node)
        return self
    
    def then(
        self,
        name: str,
        func: Callable[[ChainContext], Awaitable[ChainContext]]
    ) -> "Chain":
        """Add a transform node (alias for add)."""
        return self.add(name, func, ChainNodeType.TRANSFORM)
    
    def filter(
        self,
        name: str,
        func: Callable[[ChainContext], Awaitable[bool]]
    ) -> "Chain":
        """Add a filter node."""
        async def filter_wrapper(context: ChainContext) -> ChainContext:
            should_continue = await func(context)
            if not should_continue:
                context.metadata["filtered"] = True
            return context
        
        return self.add(name, filter_wrapper, ChainNodeType.FILTER)
    
    def parallel(self, *chains: "Chain") -> "Chain":
        """Add parallel chains."""
        async def parallel_executor(context: ChainContext) -> ChainContext:
            import asyncio
            
            tasks = [chain.execute(context) for chain in chains]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            merged_data = {}
            for result in results:
                if isinstance(result, ChainContext):
                    merged_data.update(result.data)
            
            context.data.update(merged_data)
            return context
        
        return self.add("parallel", parallel_executor, ChainNodeType.PARALLEL)
    
    async def execute(
        self,
        initial_data: Dict[str, Any] = None
    ) -> ChainContext:
        """Execute the chain."""
        context = ChainContext(data=initial_data or {})
        
        for node in self.nodes:
            context = await node.execute(context)
            
            # 检查是否被过滤
            if context.metadata.get("filtered"):
                logger.info(f"Chain '{self.name}' filtered at node '{node.name}'")
                break
        
        return context
    
    def __or__(self, other: "Chain") -> "Chain":
        """Combine chains with | operator."""
        combined = Chain(f"{self.name}|{other.name}")
        combined.nodes = self.nodes + other.nodes
        return combined


def chain(name: str = "chain") -> Chain:
    """Create a new chain."""
    return Chain(name)


async def run_chain(
    chain_instance: Chain,
    initial_data: Dict[str, Any] = None
) -> ChainContext:
    """Run a chain and return the result."""
    return await chain_instance.execute(initial_data)


class ChainBuilder:
    """Builder pattern for creating chains."""
    
    def __init__(self, name: str = "chain"):
        self.chain = Chain(name)
    
    def transform(
        self,
        name: str,
        func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> "ChainBuilder":
        """Add a transform step."""
        async def wrapper(context: ChainContext) -> ChainContext:
            result = await func(context.data)
            context.data.update(result)
            return context
        
        self.chain.add(name, wrapper, ChainNodeType.TRANSFORM)
        return self
    
    def filter(
        self,
        name: str,
        predicate: Callable[[Dict[str, Any]], Awaitable[bool]]
    ) -> "ChainBuilder":
        """Add a filter step."""
        async def filter_func(context: ChainContext) -> bool:
            return await predicate(context.data)
        
        self.chain.filter(name, filter_func)
        return self
    
    def build(self) -> Chain:
        """Build the chain."""
        return self.chain


def builder(name: str = "chain") -> ChainBuilder:
    """Create a new chain builder."""
    return ChainBuilder(name)
