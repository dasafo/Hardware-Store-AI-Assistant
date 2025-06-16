#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.services.reindex_service import reindex_products
from app.models.reindex_models import ReindexRequest, ReindexResponse
from app.utils.auth import admin_guard

router = APIRouter(prefix="/api", tags=["admin"])

@router.post("/reindex", response_model=ReindexResponse, status_code=202)
def reindex_endpoint(
    payload: ReindexRequest,
    bg: BackgroundTasks,
    user=Depends(admin_guard)   # ⬅️ solo admin
):
    """
    Triggers a complete or incremental reindex process.
    
    - **skus**: List of specific SKUs to reindex (None for full reindex)
    - **force_full**: Force a complete reindex even if SKUs are provided
    
    Returns a 202 status indicating the job has been queued for background processing.
    """
    try:
        bg.add_task(reindex_products, payload)
        reindex_type = "full" if payload.force_full or payload.skus is None else f"incremental ({len(payload.skus)} products)"
        return {"status": "accepted", "detail": f"Reindex job queued: {reindex_type}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue reindex job: {str(e)}") 