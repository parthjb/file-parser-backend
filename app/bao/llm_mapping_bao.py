import openai
from openai import AsyncOpenAI
import google.generativeai as genai
import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import String, Integer, Float, DECIMAL, Text, Date
from app.config import settings
from app.utils.logger import app_logger

class LLMMappingBAO:
    def __init__(self):
        genai.configure(api_key="api-key")
        self.expected_schema = {
            'invoices': {
                'invoice_number': String(20),
                'issue_date': Date,
                'due_date': Date,
                'total_amount': DECIMAL
            },
            'vendors': {
                'vendor_name': String,
                'email': String,
                'phone': String,
                'address': Text
            },
            'invoiceitems': {
                'description': Text,
                'quantity': Integer,
                'unit_price': DECIMAL,
                'total_price': DECIMAL
            },
            'customers': {
                'customer_name': String,
                'customer_email': String,
                'customer_phone': String,
                'customer_address': Text
            },
            'payments': {
                'payment_date': Date,
                'amount_paid': DECIMAL,
                'payment_method': String
            }
        }


    async def map_columns_with_llm(self, extracted_columns: List[str], file_context: List[Dict]) -> Dict[str, Any]:
        try:
            context = f"File context: {file_context}\n"
            
            prompt = f"""
            {context}
            Map the following extracted column names to the appropriate database schema fields.

            Extracted columns: {extracted_columns}

            Available database schema:
            - invoices: {self.expected_schema['invoices']}
            - vendors: {self.expected_schema['vendors']}
            - invoiceitems: {self.expected_schema['invoiceitems']}
            - customers: {self.expected_schema['customers']}
            - payments: {self.expected_schema['payments']}

            Provide response ONLY in valid JSON format with confidence scores (0.0-1.0):
            {{
                "mappings": [
                    {{
                        "source_field": "extracted_column_name",
                        "target_table": "table_name",
                        "target_column": "column_name",
                        "confidence": 1.0
                    }}
                ],
                "unmapped_fields": ["field1", "field2"]
            }}

            Guidelines:
            - Consider common invoice terminology variations
            - Only return valid JSON, no additional text or explanations
            - Use confidence scores between 0.0 and 1.0
            """

            model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2000,
                    "response_mime_type": "application/json"
                }
            )

            response_text = response.text.strip() if response.text else ""
            
            app_logger.info(f"Raw LLM response: {response_text}")
            
            if not response_text:
                app_logger.warning("Empty response from LLM, using fallback mapping")

            result = json.loads(response_text)
            return result

        except Exception as e:
            app_logger.error(f"Error in LLM mapping: {str(e)}")
            return {"message": "LLM is not working"}