import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.backend.models.memory import MemorySearchResult

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions the agent can take."""
    EXECUTE = "execute"
    CONFIRM = "confirm"
    REFUSE = "refuse"


@dataclass
class Decision:
    """Represents an agent decision."""
    
    action: ActionType
    reason: str = ""
    plan: Optional[Dict[str, Any]] = None
    memories_used: List[MemorySearchResult] = field(default_factory=list)
    question: Optional[str] = None
    info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize decision to dictionary."""
        return {
            "action": self.action.value,
            "reason": self.reason,
            "plan": self.plan,
            "memories_count": len(self.memories_used),
            "question": self.question,
            "info": self.info
        }


class DecisionBoundary:
    """
    Defines boundaries for agent autonomous actions.
    
    This is a core component for trustworthy AI - it ensures
    the agent only acts autonomously within defined limits.
    """
    
    # Actions the agent can take without asking
    AUTONOMOUS = {
        "memory_search",
        "context_retrieval",
        "response_generation",
        "memory_consolidation",
        "information_lookup"
    }
    
    # Actions that require user confirmation
    CONFIRM_REQUIRED = {
        "memory_delete",
        "preference_update",
        "external_api_call",
        "file_operation",
        "settings_change"
    }
    
    # Actions the agent must never take autonomously
    FORBIDDEN = {
        "financial_transaction",
        "personal_data_export",
        "account_modification",
        "security_change"
    }
    
    def get_type(self, action: str) -> str:
        """
        Get the boundary type for an action.
        
        Args:
            action: Action name
            
        Returns:
            "AUTONOMOUS", "CONFIRM_REQUIRED", or "FORBIDDEN"
        """
        if action in self.AUTONOMOUS:
            return "AUTONOMOUS"
        elif action in self.FORBIDDEN:
            return "FORBIDDEN"
        else:
            # Default to requiring confirmation for unknown actions
            return "CONFIRM_REQUIRED"
    
    def is_allowed(self, action: str) -> bool:
        """Check if an action is allowed at all."""
        return action not in self.FORBIDDEN


class DecisionEngine:
    """
    Agent decision engine with autonomy boundaries.
    
    Responsibilities:
    - Classify user intent
    - Check action against boundaries
    - Retrieve relevant memories
    - Generate execution plans
    """
    
    def __init__(self, memory_manager, llm_service):
        """
        Initialize decision engine.
        
        Args:
            memory_manager: Memory manager instance
            llm_service: LLM service for intent classification
        """
        self.memory = memory_manager
        self.llm = llm_service
        self.boundary = DecisionBoundary()
    
    async def decide(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Decision:
        """
        Make a decision based on user input and context.
        
        Args:
            user_input: User's message
            context: Current context (user_id, session_id, etc.)
            
        Returns:
            Decision object with action and supporting info
        """
        # 1. Classify intent
        intent = await self._classify_intent(user_input)
        
        # 2. Check boundary
        boundary_type = self.boundary.get_type(intent["action"])
        
        # 3. Handle based on boundary type
        if boundary_type == "FORBIDDEN":
            return Decision(
                action=ActionType.REFUSE,
                reason="此操作需要用户明确授权，我无法自主执行。"
            )
        
        if boundary_type == "CONFIRM_REQUIRED":
            return Decision(
                action=ActionType.CONFIRM,
                question=f"我准备执行：{intent['description']}，确认吗？",
                info=intent
            )
        
        # 4. For AUTONOMOUS actions, retrieve memories and plan
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        
        relevant_memories = []
        if user_id:
            relevant_memories = await self.memory.retrieve(
                user_id=user_id,
                query=user_input,
                session_id=session_id,
                top_k=5
            )
        
        # 5. Generate execution plan
        plan = await self._make_plan(intent, relevant_memories, context)
        
        return Decision(
            action=ActionType.EXECUTE,
            plan=plan,
            memories_used=relevant_memories,
            reason=f"自主执行：{intent['description']}"
        )
    
    async def _classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent.
        
        Simplified version - in production, use LLM for classification.
        """
        input_lower = user_input.lower()
        
        if any(kw in input_lower for kw in ["transfer", "money", "account", "转账", "账户"]):
            return {
                "action": "financial_transaction",
                "description": "金融交易",
                "confidence": 0.9
            }
        elif any(kw in input_lower for kw in ["delete", "remove", "删除"]):
            return {
                "action": "memory_delete",
                "description": "删除记忆",
                "confidence": 0.8
            }
        elif any(kw in input_lower for kw in ["remember", "记住", "learn"]):
            return {
                "action": "memory_store",
                "description": "存储新记忆",
                "confidence": 0.9
            }
        elif any(kw in input_lower for kw in ["what", "how", "why", "什么", "怎么", "为什么"]):
            return {
                "action": "memory_search",
                "description": "搜索记忆",
                "confidence": 0.85
            }
        else:
            return {
                "action": "response_generation",
                "description": "生成回复",
                "confidence": 0.7
            }
    
    async def _make_plan(
        self,
        intent: Dict[str, Any],
        memories: List[MemorySearchResult],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate execution plan.
        
        Args:
            intent: Classified intent
            memories: Relevant memories
            context: Current context
            
        Returns:
            Execution plan
        """
        return {
            "intent": intent,
            "memories_to_use": [m.memory.content for m in memories[:3]],
            "steps": [
                "Retrieve relevant context",
                "Generate response",
                "Update memory if needed"
            ]
        }
