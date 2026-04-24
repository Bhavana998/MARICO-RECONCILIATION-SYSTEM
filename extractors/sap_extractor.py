# src/extractors/sap_extractor.py
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional
import yaml
from datetime import datetime

class SAPExtractor:
    """Extract data from SAP ERP (AR, SD, FI modules)"""
    
    def __init__(self, config_path: str = "config/sap_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Connect to SAP HANA or S/4HANA
        self.engine = self._create_connection()
    
    def _create_connection(self):
        """Create database connection - works with SAP HANA or S/4HANA"""
        conn_string = (
            f"saphana://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}"
        )
        return create_engine(conn_string)
    
    def extract_invoices(self, 
                        date_from: datetime, 
                        date_to: datetime) -> pd.DataFrame:
        """Extract invoice data from SAP SD module"""
        
        query = """
        SELECT 
            VBRK.VBELN as invoice_number,
            VBRK.FKDAT as invoice_date,
            VBRK.KUNAG as customer_id,
            KNA1.NAME1 as customer_name,
            VBRK.NETWR as amount,
            VBRK.MWSBK as tax_amount,
            VBRK.WAERK as currency,
            VBRK.VBELN as document_number
        FROM VBRK  -- Billing Document Header
        LEFT JOIN KNA1 ON VBRK.KUNAG = KNA1.KUNNR  -- Customer Master
        WHERE VBRK.FKDAT BETWEEN :date_from AND :date_to
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(
                text(query),
                conn,
                params={"date_from": date_from, "date_to": date_to}
            )
        
        df['source'] = 'SAP'
        return df
    
    def extract_outstanding_claims(self) -> pd.DataFrame:
        """Extract unsettled claims and deductions from FI"""
        
        query = """
        SELECT 
            BKPF.BELNR as document_number,
            BKPF.BUDAT as posting_date,
            BSEG.KOART as account_type,
            BSEG.WRBTR as amount,
            BSEG.SGTXT as description,
            BSEG.ZUONR as assignment_number
        FROM BKPF  -- Accounting Document Header
        JOIN BSEG ON BKPF.BELNR = BSEG.BELNR 
                 AND BKPF.GJAHR = BSEG.GJAHR
        WHERE BKPF.BLART = 'RE'  -- Invoice type
        AND BSEG.SHKZG = 'S'     -- Debit
        AND BSEG.UMSKZ = ''      -- Open items
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        return df