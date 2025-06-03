import os
import aiofiles
from typing import  Dict, Any, List
import PyPDF2
import pandas as pd
from docx import Document
from pathlib import Path
from app.config import settings
from app.utils.logger import app_logger

class FileProcessor:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_file(self, file_content: bytes, filename: str) -> str:
        try:
            file_path = self.upload_dir / filename
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            app_logger.info(f"Saved file: {filename}")
            return str(file_path)
        except Exception as e:
            app_logger.error(f"Error saving file {filename}: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            app_logger.info(f"Extracted text from PDF: {file_path}")
            return text
        except Exception as e:
            app_logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def extract_text_from_docx(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            app_logger.info(f"Extracted text from DOCX: {file_path}")
            return text
        except Exception as e:
            app_logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            raise
    
    def extract_data_from_csv(self, file_path: str) -> Dict[str, Any]:
        try:
            df = pd.read_csv(file_path)
            data = {
                'columns': df.columns.tolist(),
                'rows': df.to_dict('records'),
                'total_rows': len(df)
            }
            app_logger.info(f"Extracted data from CSV: {file_path} ({len(df)} rows)")
            return data
        except Exception as e:
            app_logger.error(f"Error extracting data from CSV {file_path}: {str(e)}")
            raise
    
    def extract_columns_from_text(self, text: str) -> List[str]:
        """Extract potential column names from text using simple heuristics"""
        try:
            # Simple approach - look for common invoice patterns
            potential_columns = []
            lines = text.split('\n')
            
            # Common invoice field patterns
            patterns = [
                'invoice', 'date', 'amount', 'total', 'subtotal', 'tax',
                'vendor', 'supplier', 'customer', 'quantity', 'price',
                'description', 'item', 'due', 'payment', 'terms'
            ]
            
            for line in lines:
                line_lower = line.lower().strip()
                for pattern in patterns:
                    if pattern in line_lower and len(line.strip()) < 50:
                        potential_columns.append(line.strip())
            
            # Remove duplicates and return
            unique_columns = list(set(potential_columns))
            app_logger.info(f"Extracted {len(unique_columns)} potential columns from text")
            return unique_columns
        except Exception as e:
            app_logger.error(f"Error extracting columns from text: {str(e)}")
            raise
    
    
    
   