from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from app.database.models import FileUpload, ProcessingLog
from app.dao.base_dao import BaseDAO
from app.utils.logger import app_logger

class FileUploadDAO(BaseDAO[FileUpload]):
    def __init__(self):
        super().__init__(FileUpload)
    
    def get_by_id(self, db: Session, file_upload_id: int) -> Optional[FileUpload]:
        try:
            return db.query(FileUpload).filter(FileUpload.file_upload_id == file_upload_id).first()
        except SQLAlchemyError as e:
            app_logger.error(f"Error getting file upload by ID {file_upload_id}: {str(e)}")
            raise
    
    def update_processing_status(self, db: Session, file_upload_id: int, status: str, 
                               error_summary: Optional[str] = None) -> Optional[FileUpload]:
        try:
            file_upload = self.get_by_id(db, file_upload_id)
            if file_upload:
                file_upload.processing_status = status
                if error_summary:
                    file_upload.error_summary = error_summary
                db.commit()
                db.refresh(file_upload)
                app_logger.info(f"Updated file upload {file_upload_id} status to {status}")
            return file_upload
        except SQLAlchemyError as e:
            app_logger.error(f"Error updating file upload status: {str(e)}")
            db.rollback()
            raise
        
    def add_unmapped_columns(self, db: Session, file_upload_id: int, unmapped_columns: dict) -> Optional[FileUpload]:
        try:
            file_upload = self.get_by_id(db, file_upload_id)
            if file_upload:
                file_upload.unmapped_columns = unmapped_columns
                db.commit()
                db.refresh(file_upload)
                app_logger.info(f"Added unmapped columns for file_upload_id {file_upload_id}")
                return file_upload
            else:
                app_logger.warning(f"No FileUpload found for ID {file_upload_id}")
                return None
        except SQLAlchemyError as e:
            app_logger.error(f"Error adding unmapped columns for file_upload_id {file_upload_id}: {str(e)}")
            db.rollback()
            raise
    
    def get_all_with_stats(self, db: Session, skip: int = 0, limit: int = 100) -> List[FileUpload]:
        """Get all file uploads with processing stats"""
        try:
            return db.query(FileUpload).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            app_logger.error(f"Error getting file uploads with stats: {str(e)}")
            raise
    

class ProcessingLogDAO(BaseDAO[ProcessingLog]):
    def __init__(self):
        super().__init__(ProcessingLog)
    
    def create_log(self, db: Session, file_upload_id: int, level: str, 
                   message: str, details: Optional[dict] = None) -> ProcessingLog:
        try:
            log_data = {
                'file_upload_id': file_upload_id,
                'log_level': level,
                'message': message,
                'details': details
            }
            return self.create(db, log_data)
        except SQLAlchemyError as e:
            app_logger.error(f"Error creating processing log: {str(e)}")
            raise
    
    
