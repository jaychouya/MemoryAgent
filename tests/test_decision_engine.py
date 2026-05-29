import pytest
from unittest.mock import AsyncMock
from src.agent.decision import DecisionEngine, Decision, DecisionBoundary
from src.backend.models.memory import MemorySearchResult, LongTermMemoryItem


class TestDecisionBoundary:
    def test_autonomous_action_classification(self):
        """Test that autonomous actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("memory_search") == "AUTONOMOUS"
        assert boundary.get_type("response_generation") == "AUTONOMOUS"
    
    def test_confirm_required_action_classification(self):
        """Test that confirm-required actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("memory_delete") == "CONFIRM_REQUIRED"
        assert boundary.get_type("preference_update") == "CONFIRM_REQUIRED"
    
    def test_forbidden_action_classification(self):
        """Test that forbidden actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("financial_transaction") == "FORBIDDEN"
    
    def test_unknown_action_defaults_to_confirm(self):
        """Test that unknown actions default to requiring confirmation."""
        boundary = DecisionBoundary()
        assert boundary.get_type("unknown_action") == "CONFIRM_REQUIRED"


class TestDecisionEngine:
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock memory manager."""
        mock = AsyncMock()
        mock.retrieve.return_value = [
            MemorySearchResult(
                memory=LongTermMemoryItem(
                    user_id="user1",
                    content="Prefers coffee",
                    category="food"
                ),
                score=0.9
            )
        ]
        return mock
    
    @pytest.fixture
    def decision_engine(self, mock_memory_manager):
        """Create decision engine with mock dependencies."""
        return DecisionEngine(
            memory_manager=mock_memory_manager,
            llm_service=AsyncMock()
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_action_execution(self, decision_engine):
        """Test that autonomous actions are executed without confirmation."""
        decision = await decision_engine.decide(
            user_input="What do I like to drink?",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "execute"
        assert len(decision.memories_used) > 0
    
    @pytest.mark.asyncio
    async def test_forbidden_action_refusal(self, decision_engine):
        """Test that forbidden actions are refused."""
        decision = await decision_engine.decide(
            user_input="Transfer money from my account",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "refuse"
    
    @pytest.mark.asyncio
    async def test_confirm_required_action(self, decision_engine):
        """Test that confirm-required actions ask for confirmation."""
        decision = await decision_engine.decide(
            user_input="Delete all my memories",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "confirm"
        assert decision.question is not None
