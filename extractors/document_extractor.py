# src/extractors/document_extractor.py
import pytesseract
import pdfplumber
from PIL import Image
import re
from typing import Dict, Optional
import pandas as pd

class DocumentExtractor:
    """Extract text data from invoices, PODs, and claims"""
    
    def __init__(self, tesseract_path: str = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text and data from PDF invoices"""
        
        extracted_data = {
            'invoice_number': None,
            'invoice_date': None,
            'amount': None,
            'customer_name': None,
            'full_text': ''
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text()
                full_text += text + '\n'
            
            extracted_data['full_text'] = full_text
            
            # Extract key fields using regex patterns
            extracted_data['invoice_number'] = self._extract_invoice_number(full_text)
            extracted_data['amount'] = self._extract_amount(full_text)
            extracted_data['invoice_date'] = self._extract_date(full_text)
        
        return extracted_data
    
    def extract_from_image(self, image_path: str) -> Dict:
        """Extract text from scanned document images"""
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        return {
            'full_text': text,
            'invoice_number': self._extract_invoice_number(text),
            'amount': self._extract_amount(text)
        }
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number using pattern matching"""
        patterns = [
            r'INV[-_\s]?\d{5,10}',
            r'Invoice\s*[#:]?\s*(\d+)',
            r'INV-\d{8}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amounts"""
        patterns = [
            r'Total\s*[A-Z]{3}\s*([\d,]+\.?\d*)',
            r'Amount\s*Due:\s*([\d,]+\.?\d*)',
            r'(?:Grand|Invoice)\s*Total[\s:]*([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date in various formats"""
        patterns = [
            r'Invoice\s*Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Date:\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def batch_process_documents(self, folder_path: str) -> pd.DataFrame:
        """Process multiple documents in batch"""
        import os
        from glob import glob
        
        results = []
        files = glob(f"{folder_path}/**/*.*", recursive=True)
        
        for file_path in files:
            if file_path.endswith('.pdf'):
                data = self.extract_from_pdf(file_path)
            elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                data = self.extract_from_image(file_path)
            else:
                continue
            
            data['source_file'] = file_path
            results.append(data)
        
        return pd.DataFrame(results)