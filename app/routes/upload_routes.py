from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
import magic
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database.connection import get_db
from app.dao.file_upload_dao import FileUploadDAO
from app.bao.file_processing_bao import FileProcessingBAO
from app.utils.file_utils import FileProcessor
from app.schemas.file_schemas import FileUploadResponse, ProcessingStatus
from app.config import settings
from app.utils.logger import app_logger

router = APIRouter(prefix="/upload", tags=["File Upload"])

@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
            )
        
        content = await file.read()  
        # mime = magic.Magic(mime=True)
        # mime_type = mime.from_buffer(content)

        # if mime_type not in settings.ALLOWED_MIME_TYPES:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"File type {mime_type} not allowed. Allowed types: {settings.ALLOWED_MIME_TYPES}"
        #     )
            
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        file_processor = FileProcessor()
        file_path = await file_processor.save_file(content, file.filename)
        
        
        file_upload_dao = FileUploadDAO()
        upload_data = {
            'original_filename': file.filename,
            'file_path': file_path,
            'file_size': len(content),
            'file_type': file_extension,
            'processing_status': 'pending'
        }
        
        file_upload = file_upload_dao.create(db, upload_data)
        
        processing_bao = FileProcessingBAO()
        response = await processing_bao.process_uploaded_file(file_upload.file_upload_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

