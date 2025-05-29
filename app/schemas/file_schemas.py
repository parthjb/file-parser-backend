from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# class FileUploadResponse(BaseModel):
#     file_upload_id: int
#     original_filename: str
#     file_size: int
#     file_type: str
#     processing_status: ProcessingStatus
#     upload_timestamp: datetime
    
#     class Config:
#         from_attributes = True

class FieldMapping(BaseModel):
    source_field: str
    target_table: str
    target_column: str
    confidence: float

class MappingResult(BaseModel):
    mappings: List[FieldMapping]
    unmapped_fields: List[str]

class ProcessingStats(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[str]

class FileUploadResponse(BaseModel):
    file_upload_id: int
    extracted_columns: List[str]
    mappings: MappingResult
    processing_stats: ProcessingStats
    status: str

class ProcessingLogResponse(BaseModel):
    log_level: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True