import os
from pathlib import Path
import aiofiles
from typing import  Dict, Any, List
import PyPDF2
import openpyxl
import pandas as pd
from docx import Document
from pathlib import Path
from app.config import settings
from app.utils.logger import app_logger
from supabase import create_client, Client

class FileProcessor:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        self.cloud_dir = Path(settings.CLOUD_UPLOAD_DIR)
        self.cloud_dir.mkdir(exist_ok=True)
        self.supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

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
    
    async def save_file_to_cloud(self, file_content: bytes, filename: str) -> str:
        try:
            self.supabase_client.storage.from_('uploaded-files').upload(filename, file_content)
            app_logger.info(f"Saved file to cloud: {filename}")
            return filename
        except Exception as e:
            app_logger.error(f"Error saving file to cloud {filename}: {str(e)}")
            raise

    def download_file_from_cloud(self, filename: str) -> str:
        try:
            response = self.supabase_client.storage.from_('uploaded-files').download(filename)
            file_content = response
            file_path = Path(self.cloud_dir) / Path(filename).name
            with open(file_path, 'wb') as f:
                f.write(file_content)
            app_logger.info(f"Downloaded file from cloud: {filename}")
            return str(file_path)
        except Exception as e:
            app_logger.error(f"Error downloading file from cloud {filename}: {str(e)}")
            raise

    def extract_text_from_pdf(self, file_path_or_name: str, storage_location: str) -> str:
        try:
            if storage_location == 'cloud':
                file_path_or_name = self.download_file_from_cloud(file_path_or_name)
                
            text = ""
            with open(file_path_or_name, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            app_logger.info(f"Extracted text from PDF: {file_path_or_name}")
            return text
        except Exception as e:
            app_logger.error(f"Error extracting text from PDF {file_path_or_name}: {str(e)}")
            raise

    def extract_text_from_docx(self, file_path_or_name: str, storage_location: str) -> str:
        try:
            if storage_location == 'cloud':
                file_path_or_name = self.download_file_from_cloud(file_path_or_name)
                
            doc = Document(file_path_or_name)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            app_logger.info(f"Extracted text from DOCX: {file_path_or_name}")
            return text
        except Exception as e:
            app_logger.error(f"Error extracting text from DOCX {file_path_or_name}: {str(e)}")
            raise
    
    def extract_data_from_csv(self, file_path_or_name: str, storage_location: str) -> Dict[str, Any]:
        try:
            if storage_location == 'cloud':
                file_path_or_name = self.download_file_from_cloud(file_path_or_name)

            df = pd.read_csv(file_path_or_name)
            data = {
                'columns': df.columns.tolist(),
                'rows': df.to_dict('records'),
                'total_rows': len(df)
            }
            app_logger.info(f"Extracted data from CSV: {file_path_or_name} ({len(df)} rows)")
            return data
        except Exception as e:
            app_logger.error(f"Error extracting data from CSV {file_path_or_name}: {str(e)}")
            raise
    
    def extract_data_from_excel(self, file_path_or_name: str, storage_location: str) -> Dict[str, Any]:
        try:
            if storage_location == 'cloud':
                file_path_or_name = self.download_file_from_cloud(file_path_or_name)

            df = pd.read_excel(file_path_or_name)
            data = {
                'columns': df.columns.tolist(),
                'rows': df.to_dict('records'),
                'total_rows': len(df)
            }
            app_logger.info(f"Extracted data from Excel: {file_path_or_name} ({len(df)} rows)")
            return data
        except Exception as e:
            app_logger.error(f"Error extracting data from Excel {file_path_or_name}: {str(e)}")
            raise
    
    def extract_data_from_tsv(self, file_path_or_name: str, storage_location: str) -> Dict[str, Any]:
        try:
            if storage_location == 'cloud':
                file_path_or_name = self.download_file_from_cloud(file_path_or_name)

            df = pd.read_csv(file_path_or_name, sep='\t')
            data = {
                'columns': df.columns.tolist(),
                'rows': df.to_dict('records'),
                'total_rows': len(df)
            }
            app_logger.info(f"Extracted data from TSV: {file_path_or_name} ({len(df)} rows)")
            return data
        except Exception as e:
            app_logger.error(f"Error extracting data from TSV {file_path_or_name}: {str(e)}")
            raise
    

    
    
    
    
    
   