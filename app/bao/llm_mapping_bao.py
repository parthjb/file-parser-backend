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
        genai_key = settings.GENAI_API_KEY
        genai.configure(api_key=genai_key)
        self.expected_schema = {
            'invoice': {
                'invoice_number': String,
                'issue_date': Date,
                'due_date': Date,
                'total_amount': DECIMAL
            },
            'vendor': {
                'vendor_name': String,
                'email': String,
                'phone': String,
                'address': Text
            },
            'invoiceitem': {
                'description': Text,
                'quantity': Integer,
                'unit_price': DECIMAL,
                'total_price': DECIMAL
            },
            'customer': {
                'customer_name': String,
                'customer_email': String,
                'customer_phone': String,
                'customer_address': Text
            },
            'payment': {
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
            - invoice: {self.expected_schema['invoice']}
            - vendor: {self.expected_schema['vendor']}
            - invoiceitem: {self.expected_schema['invoiceitem']}
            - customer: {self.expected_schema['customer']}
            - payment: {self.expected_schema['payment']}

            Provide response ONLY in valid JSON format:
            {{
                "mappings": [
                    {{
                        "source_field": "extracted_column_name (datatype)",
                        "target_table": "table_name",
                        "target_column": "column_name (datatype)"
                    }}
                ],
                "unmapped_fields": ["field1", "field2"]
            }}

            Guidelines:
            - Consider common invoice terminology variations
            - Only return valid JSON, no additional text or explanations
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
            
            # app_logger.info(f"Raw LLM response: {response_text}")
            
            if not response_text:
                app_logger.warning("Empty response from LLM, using fallback mapping")

            result = json.loads(response_text)
            return result

        except Exception as e:
            app_logger.error(f"Error in LLM mapping: {str(e)}")
            return {"message": "LLM is not working"}
    
    
    async def fetch_and_map_columns_with_llm(self, file_context: List[Dict]) -> Dict[str, Any]:
        try:
            context = f"File context: {file_context}\n"
            
            prompt = f"""
            You are a smart data extraction and mapping engine.

            Given the following extracted **non-tabular PDF content** (it may come from forms or documents), do the following:
            1. Detect all potential fields (columns) and map them to appropriate database tables and columns.
            2. Extract actual values associated with those fields.
            3. Identify any important fields that couldn't be confidently mapped (unmapped_fields).

            Context (PDF content):
            -----------------------
            {context}
            -----------------------

            Database Schema Reference:
            - invoice: {self.expected_schema['invoice']}
            - vendor: {self.expected_schema['vendor']}
            - invoiceitem: {self.expected_schema['invoiceitem']}
            - customer: {self.expected_schema['customer']}
            - payment: {self.expected_schema['payment']}

            Output Required:
            Respond **only in valid JSON**. Do not include explanations.

            JSON Format:
            {{
                "mappings": [
                    {{
                        "source_field": "extracted_field_name (datatype)",
                        "target_table": "table_name",
                        "target_column": "column_name (datatype)"
                    }}
                ],
                "extracted_fields":["field1", "field2", ...],
                "unmapped_fields": ["field1", "field2", ...],
                "data": [
                    {{
                        "source_field_1": "value1",
                        "source_field_2": "value2",
                        ...
                    }}
                ]
            }}

            Guidelines:
            - Be intelligent and flexible: the text might not be clearly tabular.
            - Use common sense to match fields (e.g., "Inv No" → invoice_number).
            - Extract realistic field values from the text.
            - Ensure valid JSON format.
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
            
            # app_logger.info(f"Raw LLM response: {response_text}")
            
            if not response_text:
                app_logger.warning("Empty response from LLM, using fallback mapping")

            result = json.loads(response_text)
            return result

        except Exception as e:
            app_logger.error(f"Error in LLM mapping: {str(e)}")
            return {"message": "LLM is not working"}