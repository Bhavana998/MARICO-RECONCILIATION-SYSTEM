# src/extractors/customer_extractor.py
import pandas as pd
from typing import Dict, Optional
import requests
import json

class CustomerDataExtractor:
    """Extract data from customer portals (various formats)"""
    
    def __init__(self, customers_config: Dict):
        self.customers = customers_config
    
    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """Extract from CSV - most common format"""
        df = pd.read_csv(file_path)
        
        # Standardize column names
        column_mapping = {
            'Invoice No.': 'invoice_number',
            'Invoice Date': 'invoice_date',
            'Customer ID': 'customer_id',
            'Amount': 'amount',
            'Claim Amount': 'claim_amount'
        }
        
        df = df.rename(columns=column_mapping)
        df['source'] = 'customer_portal'
        return df
    
    def extract_from_excel(self, file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """Extract from Excel with multiple sheets"""
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            # Auto-detect the correct sheet
            xl = pd.ExcelFile(file_path)
            df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0])
        
        return df
    
    def extract_via_api(self, customer_id: str, api_config: Dict) -> pd.DataFrame:
        """Extract via customer's API if available"""
        
        headers = {
            'Authorization': f"Bearer {api_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{api_config['base_url']}/claims",
            headers=headers,
            params={'customer_id': customer_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['claims'])
        else:
            raise Exception(f"API Error: {response.status_code}")