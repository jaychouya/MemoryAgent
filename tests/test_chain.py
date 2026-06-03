"""Tests for chain abstraction."""
import pytest
from src.agent.chain import (
    Chain,
    ChainNode,
    ChainContext,
    ChainNodeType,
    ChainBuilder,
    chain,
    builder,
    run_chain
)


def test_chain_creates():
    """Chain 应该能创建。"""
    c = chain("test")
    assert c is not None
    assert c.name == "test"


def test_chain_add_node():
    """Chain.add 应该添加节点。"""
    c = chain("test")
    
    async def transform(ctx: ChainContext) -> ChainContext:
        return ctx
    
    c.add("step1", transform)
    
    assert len(c.nodes) == 1
    assert c.nodes[0].name == "step1"


def test_chain_then():
    """Chain.then 应该添加转换节点。"""
    c = chain("test")
    
    async def transform(ctx: ChainContext) -> ChainContext:
        return ctx
    
    c.then("step1", transform)
    
    assert len(c.nodes) == 1
    assert c.nodes[0].node_type == ChainNodeType.TRANSFORM


def test_chain_filter():
    """Chain.filter 应该添加过滤节点。"""
    c = chain("test")
    
    async def predicate(ctx: ChainContext) -> bool:
        return True
    
    c.filter("filter1", predicate)
    
    assert len(c.nodes) == 1
    assert c.nodes[0].node_type == ChainNodeType.FILTER


@pytest.mark.asyncio
async def test_chain_execute():
    """Chain.execute 应该执行链。"""
    c = chain("test")
    
    async def add_value(ctx: ChainContext) -> ChainContext:
        ctx.set("result", 42)
        return ctx
    
    c.then("add", add_value)
    
    result = await c.execute({"input": 10})
    
    assert result.get("result") == 42
    assert result.get("input") == 10


@pytest.mark.asyncio
async def test_chain_multiple_nodes():
    """Chain 应该支持多个节点。"""
    c = chain("test")
    
    async def step1(ctx: ChainContext) -> ChainContext:
        ctx.set("step1", True)
        return ctx
    
    async def step2(ctx: ChainContext) -> ChainContext:
        ctx.set("step2", True)
        return ctx
    
    c.then("step1", step1).then("step2", step2)
    
    result = await c.execute()
    
    assert result.get("step1") is True
    assert result.get("step2") is True


@pytest.mark.asyncio
async def test_chain_filter_stops():
    """Chain.filter 应该在条件不满足时停止。"""
    c = chain("test")
    
    async def should_continue(ctx: ChainContext) -> bool:
        return ctx.get("continue", False)
    
    async def after_filter(ctx: ChainContext) -> ChainContext:
        ctx.set("executed", True)
        return ctx
    
    c.filter("check", should_continue).then("after", after_filter)
    
    result = await c.execute({"continue": False})
    
    assert result.get("executed") is None
    assert result.metadata.get("filtered") is True


@pytest.mark.asyncio
async def test_chain_or_operator():
    """Chain 应该支持 | 操作符。"""
    c1 = chain("chain1")
    c2 = chain("chain2")
    
    async def step1(ctx: ChainContext) -> ChainContext:
        ctx.set("step1", True)
        return ctx
    
    async def step2(ctx: ChainContext) -> ChainContext:
        ctx.set("step2", True)
        return ctx
    
    c1.then("step1", step1)
    c2.then("step2", step2)
    
    combined = c1 | c2
    
    result = await combined.execute()
    
    assert result.get("step1") is True
    assert result.get("step2") is True


@pytest.mark.asyncio
async def test_chain_error_handling():
    """Chain 应该处理错误。"""
    c = chain("test")
    
    async def failing_step(ctx: ChainContext) -> ChainContext:
        raise ValueError("Test error")
    
    async def after_error(ctx: ChainContext) -> ChainContext:
        ctx.set("after_error", True)
        return ctx
    
    c.then("fail", failing_step).then("after", after_error)
    
    result = await c.execute()
    
    assert len(result.errors) > 0
    assert "Test error" in result.errors[0]
    assert result.get("after_error") is True


def test_chain_context():
    """ChainContext 应该管理数据。"""
    ctx = ChainContext()
    
    ctx.set("key", "value")
    assert ctx.get("key") == "value"
    
    ctx.update({"a": 1, "b": 2})
    assert ctx.get("a") == 1
    assert ctx.get("b") == 2


def test_chain_context_default():
    """ChainContext.get 应该返回默认值。"""
    ctx = ChainContext()
    
    assert ctx.get("missing") is None
    assert ctx.get("missing", "default") == "default"


def test_chain_node_execute():
    """ChainNode.execute 应该执行函数。"""
    async def transform(ctx: ChainContext) -> ChainContext:
        ctx.set("executed", True)
        return ctx
    
    node = ChainNode("test", transform)
    
    import asyncio
    ctx = asyncio.run(node.execute(ChainContext()))
    
    assert ctx.get("executed") is True


def test_chain_builder():
    """ChainBuilder 应该构建链。"""
    async def transform(data: dict) -> dict:
        return {"result": data.get("input", 0) * 2}
    
    c = builder("test").transform("double", transform).build()
    
    assert len(c.nodes) == 1


@pytest.mark.asyncio
async def test_chain_builder_execute():
    """ChainBuilder 构建的链应该能执行。"""
    async def transform(data: dict) -> dict:
        return {"result": data.get("input", 0) * 2}
    
    c = builder("test").transform("double", transform).build()
    
    result = await c.execute({"input": 21})
    
    assert result.get("result") == 42


@pytest.mark.asyncio
async def test_run_chain():
    """run_chain 应该执行链。"""
    c = chain("test")
    
    async def add_value(ctx: ChainContext) -> ChainContext:
        ctx.set("result", 42)
        return ctx
    
    c.then("add", add_value)
    
    result = await run_chain(c, {"input": 10})
    
    assert result.get("result") == 42
