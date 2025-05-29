import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import Base
from app.database.models import (
    FileUpload, ProcessingLog, Invoice, Vendor, 
    Customer, Payment, InvoiceItem
)
from app.utils.logger import app_logger

class LLMMappingProcessor:
    
    def __init__(self, db_session: Session, file_upload_id: int):
        self.db_session = db_session
        self.file_upload_id = file_upload_id
        self.processing_stats = {
            'total_records': 0,
            'successful_records': 0,
            'failed_records': 0,
            'errors': []
        }
    
    def transform_data_by_mappings(self, record: Dict[str, Any], mappings: Dict) -> Dict[str, Dict[str, Any]]:
        """
        Transform a single record according to LLM mappings, grouping by target tables.
        
        Args:
            record: Single record from file content
            mappings: LLM mapping configuration
            
        Returns:
            Dictionary grouped by target tables with mapped data
        """
        transformed_data = {
            'vendors': {},
            'customers': {},
            'invoices': {},
            'payments': {},
            'invoiceitems': {}
        }
        
        try:
            for mapping in mappings['mappings']:
                source_field = mapping['source_field']
                target_table = mapping['target_table']
                target_column = mapping['target_column']
                
                if source_field in record:
                    value = record[source_field]
                    transformed_data[target_table][target_column] = value
                    
        except Exception as e:
            app_logger.error(f"Error transforming record: {e}")
            raise
            
        return transformed_data
    
    def create_vendor(self, vendor_data: Dict[str, Any]) -> int:
        try:
            vendor = Vendor(
                vendor_name=vendor_data.get('vendor_name'),
                email=vendor_data.get('email'),
                phone=vendor_data.get('phone'),
                address=vendor_data.get('address'),
                file_upload_id=self.file_upload_id
            )
            
            self.db_session.add(vendor)
            self.db_session.flush() 
            
            app_logger.info(f"Created vendor: {vendor.vendor_name} with ID: {vendor.vendor_id}")
            return vendor.vendor_id
            
        except Exception as e:
            app_logger.error(f"Error creating vendor: {e}")
            raise
    
    def create_customer(self, customer_data: Dict[str, Any]) -> int:
        try:
            customer = Customer(
                customer_name=customer_data.get('customer_name'),
                customer_email=customer_data.get('customer_email'),
                customer_phone=customer_data.get('customer_phone'),
                customer_address=customer_data.get('customer_address'),
                file_upload_id=self.file_upload_id
            )
            
            self.db_session.add(customer)
            self.db_session.flush()
            
            app_logger.info(f"Created customer: {customer.customer_name} with ID: {customer.customer_id}")
            return customer.customer_id
            
        except Exception as e:
            app_logger.error(f"Error creating customer: {e}")
            raise
    
    def create_invoice(self, invoice_data: Dict[str, Any], vendor_id: int, customer_id: int) -> int:
        try:
            invoice = Invoice(
                invoice_number=invoice_data.get('invoice_number'),
                issue_date=invoice_data.get('issue_date'),
                due_date=invoice_data.get('due_date'),
                total_amount=invoice_data.get('total_amount'),
                vendor_id=vendor_id,
                customer_id=customer_id,
                file_upload_id=self.file_upload_id
            )
            
            self.db_session.add(invoice)
            self.db_session.flush()
            
            app_logger.info(f"Created invoice: {invoice.invoice_number} with ID: {invoice.invoice_id}")
            return invoice.invoice_id
            
        except Exception as e:
            app_logger.error(f"Error creating invoice: {e}")
            raise
    
    def create_invoice_item(self, item_data: Dict[str, Any], invoice_id: int) -> None:
        try:
            invoice_item = InvoiceItem(
                invoice_id=invoice_id,
                description=item_data.get('description'),
                quantity=item_data.get('quantity'),
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price'),
                file_upload_id=self.file_upload_id
            )
            
            self.db_session.add(invoice_item)
            app_logger.info(f"Created invoice item: {item_data.get('description')}")
            
        except Exception as e:
            app_logger.error(f"Error creating invoice item: {e}")
            raise
    
    def create_payment(self, payment_data: Dict[str, Any], invoice_id: int) -> None:
        try:
            payment = Payment(
                invoice_id=invoice_id,
                payment_date=payment_data.get('payment_date'),
                amount_paid=payment_data.get('amount_paid'),
                payment_method=payment_data.get('payment_method'),
                file_upload_id=self.file_upload_id
            )
            
            self.db_session.add(payment)
            app_logger.info(f"Created payment: {payment_data.get('payment_method')} - {payment_data.get('amount_paid')}")
            
        except Exception as e:
            app_logger.error(f"Error creating payment: {e}")
            raise
    
    def log_processing_event(self, level: str, message: str, details: Dict = None):
        try:
            log_entry = ProcessingLog(
                file_upload_id=self.file_upload_id,
                log_level=level,
                message=message,
                details=details
            )
            self.db_session.add(log_entry)
            
        except Exception as e:
            app_logger.error(f"Error logging to database: {e}")
    
    def process_single_record(self, record: Dict[str, Any], mappings: Dict) -> bool:
        """
        Process a single record and insert into database with proper foreign key relationships.
        """
        try:
            transformed_data = self.transform_data_by_mappings(record, mappings)
            vendor_id = self.create_vendor(transformed_data['vendors'])
            customer_id = self.create_customer(transformed_data['customers'])
            invoice_id = self.create_invoice(transformed_data['invoices'], vendor_id, customer_id)
            if transformed_data['invoiceitems']:
                self.create_invoice_item(transformed_data['invoiceitems'], invoice_id)
            if transformed_data['payments']:
                self.create_payment(transformed_data['payments'], invoice_id)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to process record {record.get('invoice_number', 'Unknown')}: {str(e)}"
            app_logger.error(error_msg)
            self.processing_stats['errors'].append(error_msg)
            self.log_processing_event('ERROR', error_msg, {'record': record})
            return False
    
    def process_batch(self, file_content: List[Dict[str, Any]], mappings: Dict) -> Dict[str, int]:
        """
        Process a batch of records.
        
        Args:
            file_content: List of records from file
            mappings: LLM mapping configuration
            
        Returns:
            Processing statistics
        """
        app_logger.info(f"Starting batch processing of {len(file_content)} records")
        
        self.processing_stats['total_records'] = len(file_content)
        
        file_upload = self.db_session.query(FileUpload).filter(
            FileUpload.file_upload_id == self.file_upload_id
        ).first()
        
        if file_upload:
            file_upload.processing_status = 'processing'
            file_upload.processing_started_at = datetime.now()
            file_upload.total_records_found = len(file_content)
        
        try:
            for idx, record in enumerate(file_content, 1):
                app_logger.info(f"Processing record {idx}/{len(file_content)}")
                
                try:
                    success = self.process_single_record(record, mappings)
                    if success:
                        self.processing_stats['successful_records'] += 1
                        self.db_session.commit()
                        app_logger.info(f"Successfully processed and committed record {idx}")
                    else:
                        self.processing_stats['failed_records'] += 1
                        self.db_session.rollback()
                        
                except Exception as e:
                    app_logger.error(f"Error processing record {idx}: {e}")
                    self.processing_stats['failed_records'] += 1
                    self.db_session.rollback()
            
            if file_upload:
                file_upload.processing_status = 'completed'
                file_upload.processing_completed_at = datetime.now()
                file_upload.successful_records = self.processing_stats['successful_records']
                file_upload.failed_records = self.processing_stats['failed_records']
                if self.processing_stats['errors']:
                    file_upload.error_summary = '; '.join(self.processing_stats['errors'][:5])  # First 5 errors
                
                self.db_session.commit()
            
            app_logger.info(f"Batch processing completed. Success: {self.processing_stats['successful_records']}, "
                       f"Failed: {self.processing_stats['failed_records']}")
            
        except Exception as e:
            app_logger.error(f"Critical error during batch processing: {e}")
            self.db_session.rollback()
            
            if file_upload:
                file_upload.processing_status = 'failed'
                file_upload.error_summary = str(e)
                self.db_session.commit()
            
            raise
        
        return self.processing_stats


def main(file_content: List[Dict[str, Any]], mappings: Dict, file_upload_id: int, db_session: Session):
    """
    Main function to orchestrate the LLM mapping and database insertion process.
    
    Args:
        file_content: List of records from processed file
        mappings: LLM mapping configuration
        file_upload_id: ID of the file upload record
        db_session: Database session
    """
    
    app_logger.info("Starting LLM mapping database integration process")
    
    try:
        processor = LLMMappingProcessor(db_session, file_upload_id)
        
        stats = processor.process_batch(file_content, mappings)
        
        app_logger.info("Processing completed successfully")
        app_logger.info(f"Total records: {stats['total_records']}")
        app_logger.info(f"Successful: {stats['successful_records']}")
        app_logger.info(f"Failed: {stats['failed_records']}")
        
        return stats
        
    except Exception as e:
        app_logger.error(f"Main process failed: {e}")
        raise