from sqlalchemy import Column, Integer, String, Text, DECIMAL, DATE, JSON, TIMESTAMP, ForeignKey, BIGINT
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database.connection import Base

class FileUpload(Base):
    __tablename__ = "fileupload"

    file_upload_id = Column(Integer, primary_key=True, autoincrement=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(BIGINT)
    file_type = Column(String(10), nullable=False)
    storage_location = Column(String(50), nullable=False)
    upload_timestamp = Column(TIMESTAMP, default=func.current_timestamp())
    processing_status = Column(String(200), default='pending')
    processing_started_at = Column(TIMESTAMP)
    processing_completed_at = Column(TIMESTAMP)
    total_records_found = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    error_summary = Column(Text)
    unmapped_columns = Column(JSON, nullable=True)

    processing_logs = relationship("ProcessingLog", back_populates="file_upload")
    invoices = relationship("Invoice", back_populates="file_upload")
    vendors = relationship("Vendor", back_populates="file_upload")
    customers = relationship("Customer", back_populates="file_upload")
    payments = relationship("Payment", back_populates="file_upload")
    invoice_items = relationship("InvoiceItem", back_populates="file_upload")
    llm_data_caches = relationship("LLMDataCache", back_populates="file_upload")

class LLMDataCache(Base):
    __tablename__= "llm_data_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)
    data = Column(JSON)
    extracted_fields = Column(JSON)
    
    file_upload = relationship("FileUpload", back_populates="llm_data_caches")
class ProcessingLog(Base):
    __tablename__ = "processinglog"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)
    log_level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB)
    timestamp = Column(TIMESTAMP, default=func.current_timestamp())

    file_upload = relationship("FileUpload", back_populates="processing_logs")


class Invoice(Base):
    __tablename__ = "invoice"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String)
    issue_date = Column(DATE)
    due_date = Column(DATE)
    total_amount = Column(DECIMAL)
    vendor_id = Column(Integer, ForeignKey('vendor.vendor_id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.customer_id'), nullable=False)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)

    file_upload = relationship("FileUpload", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")


class Vendor(Base):
    __tablename__ = "vendor"

    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)

    file_upload = relationship("FileUpload", back_populates="vendors")
    invoices = relationship("Invoice", back_populates="vendor")


class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    customer_address = Column(Text)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)

    file_upload = relationship("FileUpload", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")


class Payment(Base):
    __tablename__ = "payment"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoice.invoice_id'), nullable=False)
    payment_date = Column(DATE)
    amount_paid = Column(DECIMAL)
    payment_method = Column(String)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)

    file_upload = relationship("FileUpload", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")


class InvoiceItem(Base):
    __tablename__ = "invoice_item"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoice.invoice_id'), nullable=False)
    description = Column(Text)
    quantity = Column(Integer)
    unit_price = Column(DECIMAL)
    total_price = Column(DECIMAL)
    file_upload_id = Column(Integer, ForeignKey('fileupload.file_upload_id'), nullable=False)

    file_upload = relationship("FileUpload", back_populates="invoice_items")
    invoice = relationship("Invoice", back_populates="invoice_items")
