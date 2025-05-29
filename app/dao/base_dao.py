from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Type, TypeVar, Generic, Optional, List, Any, Dict
from app.utils.logger import app_logger

T = TypeVar('T')

class BaseDAO(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
    
    def create(self, db: Session, obj_data: Dict[str, Any]) -> T:
        try:
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            app_logger.info(f"Created {self.model.__name__} with ID: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
        except SQLAlchemyError as e:
            app_logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            db.rollback()
            raise
    
   