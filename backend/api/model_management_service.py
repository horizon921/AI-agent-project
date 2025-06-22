# backend/api/model_management_service.py
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.core import models

class ModelManagementService:
    # Provider methods
    def get_provider(self, db: Session, provider_id: int) -> Optional[models.Provider]:
        return db.query(models.Provider).filter(models.Provider.id == provider_id).first()

    def get_providers(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.Provider]:
        return db.query(models.Provider).offset(skip).limit(limit).all()

    def create_provider(self, db: Session, provider: models.ProviderCreate) -> models.Provider:
        db_provider = models.Provider(**provider.dict())
        db.add(db_provider)
        db.commit()
        db.refresh(db_provider)
        return db_provider

    def update_provider(self, db: Session, provider_id: int, provider_update: models.ProviderCreate) -> Optional[models.Provider]:
        db_provider = self.get_provider(db, provider_id)
        if db_provider:
            update_data = provider_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_provider, key, value)
            db.commit()
            db.refresh(db_provider)
        return db_provider

    def delete_provider(self, db: Session, provider_id: int) -> Optional[models.Provider]:
        db_provider = self.get_provider(db, provider_id)
        if db_provider:
            db.delete(db_provider)
            db.commit()
        return db_provider

    # AI Model methods
    def get_model(self, db: Session, model_id: int) -> Optional[models.AIModel]:
        return db.query(models.AIModel).filter(models.AIModel.id == model_id).first()

    def get_all_models(self, db: Session, skip: int = 0, limit: int = 1000) -> List[models.AIModel]:
        """Gets all models from all providers."""
        return db.query(models.AIModel).offset(skip).limit(limit).all()

    def get_models_by_provider(self, db: Session, provider_id: int) -> List[models.AIModel]:
        return db.query(models.AIModel).filter(models.AIModel.provider_id == provider_id).all()

    def create_model_for_provider(self, db: Session, model: models.AIModelCreate, provider_id: int) -> models.AIModel:
        db_model = models.AIModel(**model.dict(), provider_id=provider_id)
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return db_model

    def update_model(self, db: Session, model_id: int, model_update: models.AIModelCreate) -> Optional[models.AIModel]:
        db_model = self.get_model(db, model_id)
        if db_model:
            update_data = model_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_model, key, value)
            db.commit()
            db.refresh(db_model)
        return db_model

    def delete_model(self, db: Session, model_id: int) -> Optional[models.AIModel]:
        db_model = self.get_model(db, model_id)
        if db_model:
            db.delete(db_model)
            db.commit()
        return db_model