"""Auto write-back observer after conversations."""

import logging
from src.memory.manager import MemoryManager
from src.memory.auto_write import extract_candidates
from src.memory.write_pipeline import TurnWriteOutcome, persist_turn_memories
from src.utils.config import settings

logger = logging.getLogger(__name__)


class MemoryObserver:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    async def observe_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_id: str,
        session_id: str = None,
        project_id: str = None,
    ) -> TurnWriteOutcome:
        if not settings.MEMORY_EXTRACT_ENABLED:
            return TurnWriteOutcome()
        return await persist_turn_memories(
            self.memory,
            user_message,
            assistant_message,
            user_id,
            session_id=session_id,
            project_id=project_id,
        )
