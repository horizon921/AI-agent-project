# backend/api/model_management_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.core import models
from backend.core.database import get_db
from backend.api.model_management_service import ModelManagementService

router = APIRouter(
    prefix="/api/management",
    tags=["Model Management"],
)

def get_model_management_service():
    return ModelManagementService()

# Provider Endpoints
@router.post("/providers/", response_model=models.ProviderRead)
def create_provider(
    provider: models.ProviderCreate,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    # Check if base_url already exists
    existing_provider = db.query(models.Provider).filter(models.Provider.base_url == provider.base_url).first()
    if existing_provider:
        raise HTTPException(status_code=400, detail="Provider with this base_url already exists")
    return service.create_provider(db=db, provider=provider)

@router.get("/providers/", response_model=List[models.ProviderRead])
def read_providers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    return service.get_providers(db, skip=skip, limit=limit)

@router.get("/providers/{provider_id}", response_model=models.ProviderRead)
def read_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    db_provider = service.get_provider(db, provider_id=provider_id)
    if db_provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return db_provider

@router.put("/providers/{provider_id}", response_model=models.ProviderRead)
def update_provider(
    provider_id: int,
    provider: models.ProviderCreate,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    return service.update_provider(db=db, provider_id=provider_id, provider_update=provider)

@router.delete("/providers/{provider_id}", response_model=models.ProviderRead)
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    db_provider = service.delete_provider(db, provider_id=provider_id)
    if db_provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return db_provider


# Model Endpoints
@router.post("/providers/{provider_id}/models/", response_model=models.AIModelRead)
def create_model_for_provider(
    provider_id: int,
    model: models.AIModelCreate,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    return service.create_model_for_provider(db=db, model=model, provider_id=provider_id)

@router.get("/models/", response_model=List[models.AIModelRead])
def read_all_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    """
    Get a list of all AI models from all providers.
    """
    return service.get_all_models(db, skip=skip, limit=limit)

@router.get("/models/{model_id}", response_model=models.AIModelRead)
def read_model(
    model_id: int,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    db_model = service.get_model(db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model

@router.put("/models/{model_id}", response_model=models.AIModelRead)
def update_model(
    model_id: int,
    model: models.AIModelCreate,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    return service.update_model(db=db, model_id=model_id, model_update=model)

@router.delete("/models/{model_id}", response_model=models.AIModelRead)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    service: ModelManagementService = Depends(get_model_management_service)
):
    db_model = service.delete_model(db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model