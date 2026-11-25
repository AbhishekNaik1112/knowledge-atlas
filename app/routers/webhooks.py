"""GitHub push webhook — verify HMAC signature, then re-ingest the repo in the background."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request

from app.config import Settings, get_settings
from app.dependencies import get_repo_syncer, get_sync_repo
from app.models import SyncEventOut
from app.repository import SqlSyncEventRepository
from app.security import require_private_access
from app.webhook import RepoSyncer, verify_signature

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/github", status_code=202)
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    syncer: RepoSyncer = Depends(get_repo_syncer),
) -> dict[str, str]:
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=503, detail="webhook not configured")

    body = await request.body()
    if not verify_signature(settings.github_webhook_secret, body, x_hub_signature_256):
        logger.warning("Rejected GitHub webhook with invalid signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid json payload: {exc}") from exc
    background.add_task(syncer.sync, payload)
    return {"status": "accepted"}


@router.get(
    "/syncs",
    response_model=list[SyncEventOut],
    dependencies=[Depends(require_private_access)],
)
def list_sync_events(
    limit: int = Query(20, ge=1, le=100),
    syncs: SqlSyncEventRepository = Depends(get_sync_repo),
) -> list[SyncEventOut]:
    return [SyncEventOut.model_validate(e) for e in syncs.list(limit=limit)]
