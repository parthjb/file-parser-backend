from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.dao.file_upload_dao import FileUploadDAO, ProcessingLogDAO
from app.bao.llm_mapping_bao import LLMMappingBAO
from app.utils.file_utils import FileProcessor
from app.utils.logger import app_logger
from app.database.connection import get_db_session
from app.schemas.file_schemas import DataInsertResponse, FieldMapping, MappingResult, ProcessingStats, Unmappings
from app.dao.data_inserting_dao import main as process_llm_mappings  


class FileProcessingBAO:
    def __init__(self):
        self.file_upload_dao = FileUploadDAO()
        self.processing_log_dao = ProcessingLogDAO()
        self.llm_mapping_bao = LLMMappingBAO()
        self.file_processor = FileProcessor()
        self.expected_schema = {
            'invoice': {
                'invoice_number': "String(20)",
                'issue_date': "Date",
                'due_date': "Date",
                'total_amount': "DECIMAL"
            },
            'vendor': {
                'vendor_name': "String",
                'email': "String",
                'phone': "String",
                'address': "Text"
            },
            'invoiceitem': {
                'description': "Text",
                'quantity': "Integer",
                'unit_price': "DECIMAL",
                'total_price': "DECIMAL"
            },
            'customer': {
                'customer_name': "String",
                'customer_email': "String",
                'customer_phone': "String",
                'customer_address': "Text"
            },
            'payment': {
                'payment_date': "Date",
                'amount_paid': "DECIMAL",
                'payment_method': "String"
            }
        }
    
    async def process_uploaded_file(self, file_upload_id: int) -> Dict[str, Any]:
        try:
            with get_db_session() as db:
                file_upload = self.file_upload_dao.get_by_id(db, file_upload_id)
                if not file_upload:
                    raise ValueError(f"File upload {file_upload_id} not found")
                                
                self.file_upload_dao.update_processing_status(db, file_upload_id, "Processing")                 
                self.processing_log_dao.create_log(db, file_upload_id, "INFO", "Started file processing")
                
                # if file_upload.file_type == "pdf":
                #     llm_result = await self.llm_mapping_bao.fetch_and_map_columns_with_llm(file_content)
                                
                extracted_context = await self._extract_columns(file_upload)

                extracted_columns = extracted_context["columns"]
                file_content = extracted_context["rows"]  
                
                llm_result = await self.llm_mapping_bao.map_columns_with_llm(extracted_columns, file_content)
                if not llm_result:
                    raise ValueError("LLM mapping returned empty result")
                
                llm_mappings = llm_result["mappings"]
                extra_columns = llm_result["unmapped_fields"]
                
                self.file_upload_dao.add_unmapped_columns(db, file_upload_id, unmapped_columns={
                    "unmapped_fields": extra_columns
                })

                mappingss_and_schema = {
                    "mappings": llm_mappings, 
                    "expected_schema": self.expected_schema,
                    "file_upload_id": file_upload_id
                }

                return mappingss_and_schema
                                                
        except Exception as e:
            app_logger.error(f"Error processing file {file_upload_id}: {str(e)}")
            with get_db_session() as db:
                self.file_upload_dao.update_processing_status(db, file_upload_id, "Failed", str(e))
                self.processing_log_dao.create_log(db, file_upload_id, "ERROR", f"Processing failed: {str(e)}")
            raise

        
    async def confirm_user_mappings(self, file_upload_id: int, confirmed_mappings: List[Dict[str, Any]]) -> DataInsertResponse:
        try:
            with get_db_session() as db:
                self.processing_log_dao.create_log(
                    db, file_upload_id, "INFO", "Starting database insertion with LLM mappings"
                )
                
                file_upload_obj = self.file_upload_dao.get_by_id(db, file_upload_id)
                
                extracted_context = await self._extract_columns(file_upload_obj)
                file_content = extracted_context["rows"]
                
                processed_mappings_list = []
                for mapping in confirmed_mappings:
                    if hasattr(mapping, 'source_field'):
                        processed_mappings_list.append({
                            'source_field': mapping.source_field,
                            'target_table': mapping.target_table,
                            'target_column': mapping.target_column
                        })
                    else:
                        processed_mappings_list.append(mapping)
                
                processed_mappings = {
                    'mappings': processed_mappings_list
                }
                
                
                processing_stats = process_llm_mappings(
                    file_content=file_content,
                    mappings=processed_mappings,
                    file_upload_id=file_upload_id,
                    db_session=db
                )
                
                self.processing_log_dao.create_log(
                    db, file_upload_id, "INFO", 
                    f"Database insertion completed. Success: {processing_stats['successful_records']}, "
                    f"Failed: {processing_stats['failed_records']}"
                )
                
                if processing_stats['failed_records'] == 0:
                    final_status = "Completed" 
                else:
                    final_status = "Partial success"
                self.file_upload_dao.update_processing_status(db, file_upload_id, final_status)
                
                field_mappings = []
                for mapping in processed_mappings_list:
                    field_mapping = FieldMapping(
                        source_field=mapping['source_field'],
                        target_table=mapping['target_table'],
                        target_column=mapping['target_column'],
                    )
                    field_mappings.append(field_mapping)
                
                mapping_result = MappingResult(mappings=field_mappings)
                
                unmapped_fields = []
                unmapped_fields = file_upload_obj.unmapped_columns.get('unmapped_fields', [])
                unmapped = Unmappings(unmapped_fields=unmapped_fields)

                processing_stats_obj = ProcessingStats(
                    total_records=processing_stats.get('total_records', 0),
                    successful_records=processing_stats.get('successful_records', 0),
                    failed_records=processing_stats.get('failed_records', 0),
                    errors=processing_stats.get('errors', [])
                )
                
                response = DataInsertResponse(
                    file_upload_id=file_upload_id,
                    extracted_columns=extracted_context["columns"],
                    mappings=mapping_result,  
                    unmapped=unmapped,
                    processing_stats=processing_stats_obj,
                    status=final_status
                )
                
                return response
                
        except Exception as e:
            try:
                with get_db_session() as db:
                    self.processing_log_dao.create_log(
                        db, file_upload_id, "ERROR", f"Error confirming mappings: {str(e)}"
                    )
                    self.file_upload_dao.update_processing_status(db, file_upload_id, "Failed")
            except:
                pass
        
            raise e

        
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