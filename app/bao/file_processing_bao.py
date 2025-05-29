from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.dao.file_upload_dao import FileUploadDAO, ProcessingLogDAO
from app.bao.llm_mapping_bao import LLMMappingBAO
from app.utils.file_utils import FileProcessor
from app.utils.logger import app_logger
from app.database.connection import get_db_session
from app.dao.data_inserting_dao import main as process_llm_mappings  # Import the main function


class FileProcessingBAO:
    def __init__(self):
        self.file_upload_dao = FileUploadDAO()
        self.processing_log_dao = ProcessingLogDAO()
        self.llm_mapping_bao = LLMMappingBAO()
        self.file_processor = FileProcessor()
        
    async def process_uploaded_file(self, file_upload_id: int) -> Dict[str, Any]:
        """Process uploaded file and extract mappings"""
        try:
            with get_db_session() as db:
                file_upload = self.file_upload_dao.get_by_id(db, file_upload_id)
                if not file_upload:
                    raise ValueError(f"File upload {file_upload_id} not found")
                                
                self.file_upload_dao.update_processing_status(db, file_upload_id, "processing")
                                
                self.processing_log_dao.create_log(
                    db, file_upload_id, "INFO", "Started file processing"
                )
                                
                extracted_context = await self._extract_columns(file_upload)
                print("File content:", extracted_context)
                extracted_columns = extracted_context["columns"]
                file_content = extracted_context["rows"]  
                
                llm_result = await self.llm_mapping_bao.map_columns_with_llm(extracted_columns, file_content)
                if not llm_result:
                    raise ValueError("LLM mapping returned empty result")
                
                llm_mappings = llm_result["mappings"]
                mappingss = {"mappings": llm_mappings}
                print("LLM result:", llm_mappings)
                
                try:
                    self.processing_log_dao.create_log(
                        db, file_upload_id, "INFO", "Starting database insertion with LLM mappings"
                    )
                    
                    processing_stats = process_llm_mappings(
                        file_content=file_content,
                        mappings=mappingss,
                        file_upload_id=file_upload_id,
                        db_session=db
                    )
                    
                    self.processing_log_dao.create_log(
                        db, file_upload_id, "INFO", 
                        f"Database insertion completed. Success: {processing_stats['successful_records']}, "
                        f"Failed: {processing_stats['failed_records']}"
                    )
                    
                    final_status = "completed" if processing_stats['failed_records'] == 0 else "partial_success"
                    self.file_upload_dao.update_processing_status(db, file_upload_id, final_status)
                    
                    print({
                              'file_upload_id': file_upload_id,
                              'extracted_columns': extracted_columns,
                              'mappings': llm_result,
                              'processing_stats': processing_stats,
                              'status': final_status
                          })
                    
                    return {
                        'file_upload_id': file_upload_id,
                        'extracted_columns': extracted_columns,
                        'mappings': llm_result,
                        'processing_stats': processing_stats,
                        'status': final_status
                    }
                    
                except Exception as db_error:
                    app_logger.error(f"Error during database insertion for file {file_upload_id}: {str(db_error)}")
                    self.processing_log_dao.create_log(
                        db, file_upload_id, "ERROR", f"Database insertion failed: {str(db_error)}"
                    )
                    # Update status to failed
                    self.file_upload_dao.update_processing_status(
                        db, file_upload_id, "failed", str(db_error)
                    )
                    raise
                                                
        except Exception as e:
            app_logger.error(f"Error processing file {file_upload_id}: {str(e)}")
            with get_db_session() as db:
                self.file_upload_dao.update_processing_status(
                    db, file_upload_id, "failed", str(e)
                )
                self.processing_log_dao.create_log(
                    db, file_upload_id, "ERROR", f"Processing failed: {str(e)}"
                )
            raise
        
    async def _extract_columns(self, file_upload) -> Dict[str, Any]:
        file_path = file_upload.file_path
        file_type = file_upload.file_type.lower()
                
        try:
            if file_type == 'csv':
                data = self.file_processor.extract_data_from_csv(file_path)
                return data
            elif file_type == 'pdf':
                text = self.file_processor.extract_text_from_pdf(file_path)
                return self.file_processor.extract_columns_from_text(text)
            elif file_type in ['docx', 'doc']:
                text = self.file_processor.extract_text_from_docx(file_path)
                return self.file_processor.extract_columns_from_text(text)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            app_logger.error(f"Error extracting columns from {file_path}: {str(e)}")
            raise
    
    