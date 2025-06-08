from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.database.connection import get_db
from app.dao.file_upload_dao import FileUploadDAO
from app.dao.data_retrevial_dao import DataRetrivalDAO
from app.utils.logger import app_logger

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    try:
        file_upload_dao = FileUploadDAO()
        
        recent_uploads = file_upload_dao.get_all_with_stats(db, limit=200)
        
        total_files = len(recent_uploads)
        completed_files = len([f for f in recent_uploads if f.processing_status == 'Completed'])
        failed_files = len([f for f in recent_uploads if f.processing_status == 'Failed'])
        partial_files = len([f for f in recent_uploads if f.processing_status == 'Partial success'])
        
        return {
            'total_files_uploaded': total_files,
            'completed_processing': completed_files,
            'failed_processing': failed_files,
            'partial_files': partial_files,
            'recent_uploads': [
                {
                    'file_upload_id': f.file_upload_id,
                    'filename': f.original_filename,
                    'status': f.processing_status,
                    'storage_location': f.storage_location,
                    'records_processed': f.successful_records or 0,
                    'file_size': f.file_size,
                    'file_type': f.file_type,
                    'upload_timestamp': f.upload_timestamp,
                    'total_records_found': f.total_records_found,
                    'failed_records': f.failed_records,
                    'error_summary': f.error_summary,
                    'unmapped_columns': f.unmapped_columns or [],
                }
                for f in recent_uploads
            ]
        }
    except Exception as e:
        app_logger.error(f"Error getting dashboard overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/processing-summary/{file_upload_id}")
async def get_processing_summary(file_upload_id: int, db: Session = Depends(get_db)):
    try:
        data_dao = DataRetrivalDAO()
        summary = await data_dao.get_all_data_by_file_id(db, file_upload_id)
        return summary
    except Exception as e:
        app_logger.error(f"Error getting processing summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

