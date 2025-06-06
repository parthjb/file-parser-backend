from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import LLMDataCache
from app.utils.logger import app_logger
from app.dao.base_dao import BaseDAO

class LLMExtractedDataDAO(BaseDAO[LLMDataCache]):
  def __init__(self):
    super().__init__(LLMDataCache)
  
  def insert_data(self, db: Session, file_upload_id: int, data: dict, extracted_fields: dict):
    try:
      extracted_data = {
        'file_upload_id': file_upload_id,
        'data':data,
        'extracted_fields':extracted_fields
      }
      app_logger.info(f"Successfully stored LLM extracted data for file_id: {file_upload_id}")
      return self.create(db, extracted_data)
    except SQLAlchemyError as e:
      app_logger.error(f"Error while storing LLM extracted data for file_id {file_upload_id}: {str(e)}")
      
  def get_data_by_id(self, db: Session, file_upload_id: int):
    try:
      return db.query(LLMDataCache).filter(LLMDataCache.file_upload_id == file_upload_id).first()
    except SQLAlchemyError as e:
      app_logger.error(f"Error while retrieving LLM extracted data for file_id {file_upload_id}: {str(e)}")