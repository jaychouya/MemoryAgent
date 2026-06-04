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


@router.get("/integrations/status")
async def integrations_status():
    return get_integration_manager().get_sync_status()
