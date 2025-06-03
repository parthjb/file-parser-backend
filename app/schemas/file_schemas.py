from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MappingItem(BaseModel):
    source_field: str
    target_table: str
    target_column: str

class FieldMapping(BaseModel):
    source_field: str
    target_table: str
    target_column: str

class MappingRequest(BaseModel):
    mappings: List[MappingItem]

class MappingResult(BaseModel):
    mappings: List[FieldMapping]

class Unmappings(BaseModel):
    unmapped_fields: List[str] = Field(default_factory=list)

class ProcessingStats(BaseModel):
    total_records: int = Field(default=0, ge=0)
    successful_records: int = Field(default=0, ge=0)
    failed_records: int = Field(default=0, ge=0)
    errors: List[str] = Field(default_factory=list)

class DataInsertResponse(BaseModel):
    file_upload_id: int
    extracted_columns: List[str] = Field(default_factory=list)
    mappings: MappingResult
    unmapped: Unmappings
    processing_stats: ProcessingStats
    status: str

class ProcessingLogResponse(BaseModel):
    log_level: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ExpectedTableSchema(RootModel[Dict[str, str]]):
    pass

class FullMappingSchema(BaseModel):
    mappings: List[MappingItem]
    expected_schema: Dict[str, ExpectedTableSchema]
    file_upload_id: int