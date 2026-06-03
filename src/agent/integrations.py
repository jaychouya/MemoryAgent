"""External integration framework for connecting to third-party services."""

import logging
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class IntegrationType(str, Enum):
    """Types of integrations."""
    EMAIL = "email"
    CALENDAR = "calendar"
    DOCUMENT = "document"
    CODE = "code"
    CHAT = "chat"
    STORAGE = "storage"


class AuthType(str, Enum):
    """Authentication types."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    TOKEN = "token"


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    integration_id: str
    name: str
    integration_type: IntegrationType
    auth_type: AuthType
    base_url: str
    description: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationCredentials:
    """Credentials for an integration."""
    integration_id: str
    credentials: Dict[str, str]
    expires_at: Optional[datetime] = None


@dataclass
class SyncResult:
    """Result of a sync operation."""
    integration_id: str
    success: bool
    items_synced: int = 0
    errors: List[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=datetime.now)


class IntegrationProvider:
    """Base class for integration providers."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.credentials: Optional[IntegrationCredentials] = None
    
    def set_credentials(self, credentials: IntegrationCredentials):
        """Set credentials for this provider."""
        self.credentials = credentials
    
    async def test_connection(self) -> bool:
        """Test if connection is working."""
        raise NotImplementedError
    
    async def fetch_data(
        self,
        query: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch data from the integration."""
        raise NotImplementedError
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Send data to the integration."""
        raise NotImplementedError


class EmailIntegration(IntegrationProvider):
    """Email integration (Gmail, Outlook, etc.)."""
    
    async def test_connection(self) -> bool:
        """Test email connection."""
        # 实际实现会检查 OAuth token 或 API key
        return self.credentials is not None
    
    async def fetch_data(
        self,
        query: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch emails."""
        # 实际实现会调用 Gmail/Outlook API
        logger.info(f"Fetching emails with query: {query}")
        return []
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Send email."""
        logger.info(f"Sending email: {data.get('subject', '')}")
        return True
    
    async def fetch_recent_emails(
        self,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch recent emails."""
        return await self.fetch_data(limit=max_results)


class CalendarIntegration(IntegrationProvider):
    """Calendar integration (Google Calendar, Outlook, etc.)."""
    
    async def test_connection(self) -> bool:
        """Test calendar connection."""
        return self.credentials is not None
    
    async def fetch_data(
        self,
        query: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch calendar events."""
        logger.info(f"Fetching calendar events")
        return []
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Create calendar event."""
        logger.info(f"Creating event: {data.get('title', '')}")
        return True
    
    async def fetch_upcoming_events(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Fetch upcoming events."""
        return await self.fetch_data()


class DocumentIntegration(IntegrationProvider):
    """Document integration (Notion, Google Docs, etc.)."""
    
    async def test_connection(self) -> bool:
        """Test document connection."""
        return self.credentials is not None
    
    async def fetch_data(
        self,
        query: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch documents."""
        logger.info(f"Fetching documents")
        return []
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Create or update document."""
        logger.info(f"Creating document: {data.get('title', '')}")
        return True
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents."""
        return await self.fetch_data(query={"search": query}, limit=limit)


class CodeIntegration(IntegrationProvider):
    """Code integration (GitHub, GitLab, etc.)."""
    
    async def test_connection(self) -> bool:
        """Test code platform connection."""
        return self.credentials is not None
    
    async def fetch_data(
        self,
        query: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch code data (repos, PRs, issues)."""
        logger.info(f"Fetching code data")
        return []
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Create issue, PR, etc."""
        logger.info(f"Creating code item")
        return True
    
    async def fetch_recent_commits(
        self,
        repo: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch recent commits."""
        return await self.fetch_data(query={"repo": repo}, limit=limit)
    
    async def fetch_open_issues(
        self,
        repo: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch open issues."""
        return await self.fetch_data(
            query={"repo": repo, "state": "open"},
            limit=limit
        )


class IntegrationManager:
    """Manages all integrations."""
    
    # 预定义的集成配置
    PRESET_INTEGRATIONS = {
        "gmail": IntegrationConfig(
            integration_id="gmail",
            name="Gmail",
            integration_type=IntegrationType.EMAIL,
            auth_type=AuthType.OAUTH2,
            base_url="https://gmail.googleapis.com/gmail/v1",
            description="Google 邮件服务"
        ),
        "google_calendar": IntegrationConfig(
            integration_id="google_calendar",
            name="Google Calendar",
            integration_type=IntegrationType.CALENDAR,
            auth_type=AuthType.OAUTH2,
            base_url="https://www.googleapis.com/calendar/v3",
            description="Google 日历服务"
        ),
        "notion": IntegrationConfig(
            integration_id="notion",
            name="Notion",
            integration_type=IntegrationType.DOCUMENT,
            auth_type=AuthType.TOKEN,
            base_url="https://api.notion.com/v1",
            description="Notion 文档和数据库"
        ),
        "github": IntegrationConfig(
            integration_id="github",
            name="GitHub",
            integration_type=IntegrationType.CODE,
            auth_type=AuthType.TOKEN,
            base_url="https://api.github.com",
            description="GitHub 代码托管平台"
        ),
        "slack": IntegrationConfig(
            integration_id="slack",
            name="Slack",
            integration_type=IntegrationType.CHAT,
            auth_type=AuthType.OAUTH2,
            base_url="https://slack.com/api",
            description="Slack 团队沟通平台"
        )
    }
    
    def __init__(self, config_dir: str = ".memoryai/integrations"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.providers: Dict[str, IntegrationProvider] = {}
        self.credentials: Dict[str, IntegrationCredentials] = {}
        
        # 加载预设集成
        self.integrations.update(self.PRESET_INTEGRATIONS)
        
        # 加载保存的凭证
        self._load_credentials()
    
    def _load_credentials(self):
        """Load saved credentials."""
        creds_file = self.config_dir / "credentials.json"
        if creds_file.exists():
            try:
                data = json.loads(creds_file.read_text())
                for integration_id, creds in data.items():
                    self.credentials[integration_id] = IntegrationCredentials(
                        integration_id=integration_id,
                        credentials=creds.get("credentials", {}),
                        expires_at=datetime.fromisoformat(creds["expires_at"]) if creds.get("expires_at") else None
                    )
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")
    
    def _save_credentials(self):
        """Save credentials to disk."""
        creds_file = self.config_dir / "credentials.json"
        data = {}
        for integration_id, creds in self.credentials.items():
            data[integration_id] = {
                "credentials": creds.credentials,
                "expires_at": creds.expires_at.isoformat() if creds.expires_at else None
            }
        creds_file.write_text(json.dumps(data, indent=2))
    
    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of available integrations."""
        return [
            {
                "id": config.integration_id,
                "name": config.name,
                "type": config.integration_type.value,
                "description": config.description,
                "enabled": config.enabled,
                "connected": config.integration_id in self.credentials
            }
            for config in self.integrations.values()
        ]
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration config by ID."""
        return self.integrations.get(integration_id)
    
    def connect_integration(
        self,
        integration_id: str,
        credentials: Dict[str, str]
    ) -> bool:
        """Connect to an integration with credentials."""
        if integration_id not in self.integrations:
            logger.error(f"Unknown integration: {integration_id}")
            return False
        
        config = self.integrations[integration_id]
        
        # 保存凭证
        self.credentials[integration_id] = IntegrationCredentials(
            integration_id=integration_id,
            credentials=credentials
        )
        self._save_credentials()
        
        # 创建 provider
        provider = self._create_provider(config)
        if provider:
            provider.set_credentials(self.credentials[integration_id])
            self.providers[integration_id] = provider
        
        logger.info(f"Connected to {config.name}")
        return True
    
    def disconnect_integration(self, integration_id: str) -> bool:
        """Disconnect from an integration."""
        if integration_id in self.credentials:
            del self.credentials[integration_id]
            self._save_credentials()
        
        if integration_id in self.providers:
            del self.providers[integration_id]
        
        logger.info(f"Disconnected from {integration_id}")
        return True
    
    def _create_provider(
        self,
        config: IntegrationConfig
    ) -> Optional[IntegrationProvider]:
        """Create an integration provider."""
        provider_map = {
            IntegrationType.EMAIL: EmailIntegration,
            IntegrationType.CALENDAR: CalendarIntegration,
            IntegrationType.DOCUMENT: DocumentIntegration,
            IntegrationType.CODE: CodeIntegration,
        }
        
        provider_class = provider_map.get(config.integration_type)
        if provider_class:
            return provider_class(config)
        
        return None
    
    def get_provider(
        self,
        integration_id: str
    ) -> Optional[IntegrationProvider]:
        """Get an integration provider."""
        return self.providers.get(integration_id)
    
    async def sync_integration(
        self,
        integration_id: str
    ) -> SyncResult:
        """Sync data from an integration."""
        provider = self.get_provider(integration_id)
        if not provider:
            return SyncResult(
                integration_id=integration_id,
                success=False,
                errors=["Integration not connected"]
            )
        
        try:
            # 测试连接
            if not await provider.test_connection():
                return SyncResult(
                    integration_id=integration_id,
                    success=False,
                    errors=["Connection test failed"]
                )
            
            # 获取数据
            data = await provider.fetch_data()
            
            return SyncResult(
                integration_id=integration_id,
                success=True,
                items_synced=len(data)
            )
            
        except Exception as e:
            logger.error(f"Sync failed for {integration_id}: {e}")
            return SyncResult(
                integration_id=integration_id,
                success=False,
                errors=[str(e)]
            )
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status for all integrations."""
        return {
            "connected": list(self.credentials.keys()),
            "available": list(self.integrations.keys())
        }


# 全局集成管理器实例
_integration_manager: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    """Get or create global integration manager."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager
