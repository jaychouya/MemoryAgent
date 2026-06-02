"""Multi-agent coordination system."""

import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class AgentRole:
    """Definition of an agent role."""
    name: str
    capabilities: List[str]
    system_prompt: str
    description: str = ""


@dataclass
class AgentMessage:
    """Message between agents."""
    sender: str
    receiver: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubAgent:
    """A sub-agent with specific role."""
    
    def __init__(
        self,
        role: AgentRole,
        llm_service=None
    ):
        self.role = role
        self.llm = llm_service
        self.messages: List[AgentMessage] = []
    
    async def execute(self, task: str) -> str:
        """Execute a task."""
        logger.info(f"Agent {self.role.name} executing: {task[:50]}...")
        
        # If LLM service available, use it
        if self.llm:
            try:
                response = await self.llm.generate_response(
                    message=task,
                    system_prompt=self.role.system_prompt
                )
                return response.get("content", "")
            except Exception as e:
                logger.error(f"Agent {self.role.name} failed: {e}")
                return f"Error: {e}"
        
        # Fallback: return task acknowledgment
        return f"Agent {self.role.name} received task: {task}"
    
    def receive_message(self, message: AgentMessage):
        """Receive a message from another agent."""
        self.messages.append(message)
        logger.debug(f"Agent {self.role.name} received message from {message.sender}")


class MultiAgentOrchestrator:
    """Orchestrates multiple agents."""
    
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.message_history: List[AgentMessage] = []
    
    def add_agent(self, agent: SubAgent):
        """Add an agent to the orchestrator."""
        self.agents[agent.role.name] = agent
        logger.info(f"Added agent: {agent.role.name}")
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent."""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Removed agent: {name}")
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[SubAgent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self.agents.keys())
    
    async def delegate(self, task: str, agent_name: str) -> str:
        """Delegate a task to a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return f"Error: Agent '{agent_name}' not found"
        
        result = await agent.execute(task)
        return result
    
    async def coordinate(self, task: str) -> str:
        """Coordinate multiple agents to complete a task."""
        if not self.agents:
            return "Error: No agents available"
        
        # Simple coordination: use first available agent
        agent_name = list(self.agents.keys())[0]
        return await self.delegate(task, agent_name)
    
    def send_message(
        self,
        sender: str,
        receiver: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Send a message between agents."""
        if sender not in self.agents or receiver not in self.agents:
            return False
        
        message = AgentMessage(
            sender=sender,
            receiver=receiver,
            content=content,
            metadata=metadata or {}
        )
        
        self.message_history.append(message)
        self.agents[receiver].receive_message(message)
        
        logger.debug(f"Message sent: {sender} -> {receiver}")
        return True
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """Get message history."""
        return [
            {
                "sender": msg.sender,
                "receiver": msg.receiver,
                "content": msg.content,
                "metadata": msg.metadata
            }
            for msg in self.message_history
        ]


class OrchestratorWorkerPattern:
    """Orchestrator-Worker coordination pattern."""
    
    def __init__(self, orchestrator: MultiAgentOrchestrator):
        self.orchestrator = orchestrator
    
    async def execute(self, task: str, worker_names: List[str]) -> Dict[str, str]:
        """Execute task using orchestrator-worker pattern."""
        results = {}
        
        # Delegate to each worker
        for worker_name in worker_names:
            result = await self.orchestrator.delegate(task, worker_name)
            results[worker_name] = result
        
        return results
    
    async def execute_sequential(
        self,
        task: str,
        worker_names: List[str]
    ) -> str:
        """Execute task sequentially through workers."""
        current_result = task
        
        for worker_name in worker_names:
            current_result = await self.orchestrator.delegate(
                current_result,
                worker_name
            )
        
        return current_result
