"""
Plan Mode for MemoryAI Agent.

Implements Claude Code's plan-then-execute workflow:
- EnterPlanMode: Switch to read-only exploration
- ExitPlanMode: Return to normal mode after user approval
- Plan storage in .memoryai/plans/
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from src.agent.tools.base import ReadOnlyTool, ToolResult

logger = logging.getLogger(__name__)


class PlanModeManager:
    """
    Manages Plan Mode state and plan storage.
    
    Features:
    - Plan creation and storage
    - Mode switching (plan/execute)
    - Plan file management
    """
    
    def __init__(self, plans_dir: str = ".memoryai/plans"):
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self._current_plan: Optional[str] = None
        self._is_plan_mode: bool = False
    
    @property
    def is_plan_mode(self) -> bool:
        """Check if currently in plan mode."""
        return self._is_plan_mode
    
    def enter_plan_mode(self) -> str:
        """
        Enter plan mode.
        
        Returns:
            Confirmation message
        """
        self._is_plan_mode = True
        return "已进入计划模式。在此模式下，我只能读取和分析代码，不能进行修改。请描述您想要实现的功能，我会为您制定实施计划。"
    
    def exit_plan_mode(self) -> str:
        """
        Exit plan mode.
        
        Returns:
            Confirmation message
        """
        self._is_plan_mode = False
        plan_id = self._current_plan
        self._current_plan = None
        
        if plan_id:
            return f"已退出计划模式。计划 '{plan_id}' 已保存。现在可以开始实施。"
        return "已退出计划模式。现在可以开始实施。"
    
    async def create_plan(
        self,
        title: str,
        description: str,
        tasks: List[Dict]
    ) -> str:
        """
        Create a new implementation plan.
        
        Args:
            title: Plan title
            description: Plan description
            tasks: List of tasks with description and status
            
        Returns:
            Plan ID
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan_content = self._format_plan(plan_id, title, description, tasks)
        
        # Save plan file
        plan_path = self.plans_dir / f"{plan_id}.md"
        plan_path.write_text(plan_content, encoding="utf-8")
        
        self._current_plan = plan_id
        logger.info(f"Created plan: {plan_id}")
        
        return plan_id
    
    def get_plan(self, plan_id: str) -> Optional[str]:
        """Get plan content by ID."""
        plan_path = self.plans_dir / f"{plan_id}.md"
        if plan_path.exists():
            return plan_path.read_text(encoding="utf-8")
        return None
    
    def list_plans(self) -> List[Dict]:
        """List all saved plans."""
        plans = []
        
        for plan_path in self.plans_dir.glob("*.md"):
            plan_id = plan_path.stem
            content = plan_path.read_text(encoding="utf-8")
            
            # Extract title from content
            title = plan_id
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            
            plans.append({
                "id": plan_id,
                "title": title,
                "created": datetime.fromtimestamp(plan_path.stat().st_ctime).isoformat()
            })
        
        return sorted(plans, key=lambda p: p["created"], reverse=True)
    
    def _format_plan(
        self,
        plan_id: str,
        title: str,
        description: str,
        tasks: List[Dict]
    ) -> str:
        """Format plan as markdown."""
        lines = [
            f"# {title}",
            "",
            f"**计划ID:** {plan_id}",
            f"**创建时间:** {datetime.now().isoformat()}",
            "",
            "## 描述",
            "",
            description,
            "",
            "## 任务列表",
            ""
        ]
        
        for i, task in enumerate(tasks, 1):
            status = task.get("status", "pending")
            status_icon = "✅" if status == "completed" else "⬜"
            lines.append(f"{status_icon} {i}. {task.get('description', '')}")
        
        lines.extend([
            "",
            "---",
            "",
            "*此计划由 MemoryAI Agent 自动生成*"
        ])
        
        return "\n".join(lines)


class EnterPlanModeTool(ReadOnlyTool):
    """Tool to enter Plan Mode."""
    
    name = "enter_plan_mode"
    description = "进入计划模式，开始规划复杂任务"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def __init__(self, plan_manager: PlanModeManager):
        self.plan_manager = plan_manager
    
    async def execute(self, **kwargs) -> ToolResult:
        result = self.plan_manager.enter_plan_mode()
        return ToolResult(success=True, content=result)


class ExitPlanModeTool(ReadOnlyTool):
    """Tool to exit Plan Mode."""
    
    name = "exit_plan_mode"
    description = "退出计划模式，开始执行计划"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def __init__(self, plan_manager: PlanModeManager):
        self.plan_manager = plan_manager
    
    async def execute(self, **kwargs) -> ToolResult:
        result = self.plan_manager.exit_plan_mode()
        return ToolResult(success=True, content=result)


class CreatePlanTool(ReadOnlyTool):
    """Tool to create implementation plan."""
    
    name = "create_plan"
    description = "创建实施计划"
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "计划标题"
            },
            "description": {
                "type": "string",
                "description": "计划描述"
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "status": {"type": "string", "enum": ["pending", "completed"]}
                    }
                },
                "description": "任务列表"
            }
        },
        "required": ["title", "description", "tasks"]
    }
    
    def __init__(self, plan_manager: PlanModeManager):
        self.plan_manager = plan_manager
    
    async def execute(self, title: str, description: str, tasks: List[Dict], **kwargs) -> ToolResult:
        plan_id = await self.plan_manager.create_plan(title, description, tasks)
        return ToolResult(
            success=True,
            content=f"计划已创建: {plan_id}"
        )
