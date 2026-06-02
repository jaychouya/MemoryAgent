"""Tests for multi-agent coordination."""
import pytest
from src.agent.multi_agent import (
    AgentRole,
    SubAgent,
    MultiAgentOrchestrator,
    OrchestratorWorkerPattern
)


@pytest.mark.asyncio
async def test_subagent_executes_task():
    """SubAgent 应该能执行任务。"""
    role = AgentRole(
        name="worker",
        capabilities=["text"],
        system_prompt="You are a worker"
    )
    
    agent = SubAgent(role=role)
    result = await agent.execute("test task")
    
    assert "worker" in result
    assert "test task" in result


def test_orchestrator_adds_agent():
    """Orchestrator 应该能添加 agent。"""
    orchestrator = MultiAgentOrchestrator()
    
    role = AgentRole(
        name="worker",
        capabilities=["text"],
        system_prompt="You are a worker"
    )
    agent = SubAgent(role=role)
    
    orchestrator.add_agent(agent)
    
    assert "worker" in orchestrator.list_agents()


@pytest.mark.asyncio
async def test_orchestrator_delegates_task():
    """Orchestrator 应该能委派任务。"""
    orchestrator = MultiAgentOrchestrator()
    
    role = AgentRole(
        name="worker",
        capabilities=["text"],
        system_prompt="You are a worker"
    )
    agent = SubAgent(role=role)
    orchestrator.add_agent(agent)
    
    result = await orchestrator.delegate("test task", "worker")
    
    assert "worker" in result


def test_orchestrator_sends_message():
    """Orchestrator 应该能发送消息。"""
    orchestrator = MultiAgentOrchestrator()
    
    role1 = AgentRole(name="sender", capabilities=[], system_prompt="")
    role2 = AgentRole(name="receiver", capabilities=[], system_prompt="")
    
    orchestrator.add_agent(SubAgent(role=role1))
    orchestrator.add_agent(SubAgent(role=role2))
    
    result = orchestrator.send_message("sender", "receiver", "Hello")
    
    assert result is True
    assert len(orchestrator.get_message_history()) == 1


@pytest.mark.asyncio
async def test_orchestrator_worker_pattern():
    """Orchestrator-Worker 模式应该能工作。"""
    orchestrator = MultiAgentOrchestrator()
    
    role = AgentRole(name="worker", capabilities=[], system_prompt="")
    orchestrator.add_agent(SubAgent(role=role))
    
    pattern = OrchestratorWorkerPattern(orchestrator)
    results = await pattern.execute("test task", ["worker"])
    
    assert "worker" in results
    assert "test task" in results["worker"]


@pytest.mark.asyncio
async def test_orchestrator_worker_sequential():
    """Orchestrator-Worker 顺序执行应该能工作。"""
    orchestrator = MultiAgentOrchestrator()
    
    role1 = AgentRole(name="step1", capabilities=[], system_prompt="")
    role2 = AgentRole(name="step2", capabilities=[], system_prompt="")
    
    orchestrator.add_agent(SubAgent(role=role1))
    orchestrator.add_agent(SubAgent(role=role2))
    
    pattern = OrchestratorWorkerPattern(orchestrator)
    result = await pattern.execute_sequential("task", ["step1", "step2"])
    
    assert "task" in result
