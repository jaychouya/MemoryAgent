from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any

from src.agent.integrations import get_integration_manager

router = APIRouter()


class ConnectIntegrationRequest(BaseModel):
    integration_id: str
    credentials: Dict[str, str] = Field(default_factory=dict)


@router.get("/integrations")
async def list_integrations() -> List[Dict[str, Any]]:
    return get_integration_manager().get_available_integrations()


@router.post("/integrations/connect")
async def connect_integration(body: ConnectIntegrationRequest):
    ok = get_integration_manager().connect_integration(
        body.integration_id,
        body.credentials,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Unknown integration")
    return {"status": "connected", "integration_id": body.integration_id}


@router.post("/integrations/{integration_id}/disconnect")
async def disconnect_integration(integration_id: str):
    get_integration_manager().disconnect_integration(integration_id)
    return {"status": "disconnected", "integration_id": integration_id}


@router.post("/integrations/{integration_id}/sync")
async def sync_integration(integration_id: str):
    result = await get_integration_manager().sync_integration(integration_id)
    return {
        "integration_id": result.integration_id,
        "success": result.success,
        "items_synced": result.items_synced,
        "errors": result.errors,
    }


class NotifyIntegrationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.post("/integrations/{integration_id}/notify")
async def notify_integration(integration_id: str, body: NotifyIntegrationRequest):
    manager = get_integration_manager()
    provider = manager.get_provider(integration_id)
    if not provider:
        raise HTTPException(status_code=400, detail="Integration not connected")
    ok = await provider.send_data({"text": body.message})
    if not ok:
        raise HTTPException(status_code=502, detail="Notify failed")
    return {"status": "sent", "integration_id": integration_id}


@router.post("/integrations/{integration_id}/test")
async def test_integration(integration_id: str):
    manager = get_integration_manager()
    provider = manager.get_provider(integration_id)
    if not provider:
        raise HTTPException(status_code=400, detail="Integration not connected")
    ok = await provider.test_connection()
    if not ok:
        raise HTTPException(status_code=502, detail="Connection test failed")
    return {"status": "ok", "integration_id": integration_id}


@router.get("/integrations/status")
async def integrations_status():
    return get_integration_manager().get_sync_status()
