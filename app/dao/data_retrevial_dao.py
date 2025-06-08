from sqlalchemy.orm import Session
from app.database.models import Invoice, InvoiceItem, Vendor, Customer, Payment
from app.database.connection import get_db
from app.utils.logger import app_logger
class DataRetrivalDAO:
    def __init__(self):
        pass
    
    async def get_all_data_by_file_id(self, session: Session, file_upload_id: int):
        try:
            if session is None:
                session = next(get_db())

            app_logger.info(f"Retrieving data for file_upload_id: {file_upload_id}")
            
            vendors = session.query(Vendor).filter(
                Vendor.file_upload_id == file_upload_id
            ).all()
            
            customers = session.query(Customer).filter(
                Customer.file_upload_id == file_upload_id
            ).all()
            
            invoices = session.query(Invoice).filter(
                Invoice.file_upload_id == file_upload_id
            ).all()
            
            payments = session.query(Payment).filter(
                Payment.file_upload_id == file_upload_id
            ).all()
          
            invoice_items = session.query(InvoiceItem).filter(
                InvoiceItem.file_upload_id == file_upload_id
            ).all()
            
            app_logger.info(f"Retrieved {len(invoices)} invoices, {len(vendors)} vendors, "
                           f"{len(customers)} customers, {len(payments)} payments, "
                           f"and {len(invoice_items)} invoice items for file_upload_id: {file_upload_id}")
            
            return {
                'invoices': invoices,
                'vendors': vendors,
                'customers': customers,
                'payments': payments,
                'invoice_items': invoice_items
            }
                    
        except Exception as e:
            raise e