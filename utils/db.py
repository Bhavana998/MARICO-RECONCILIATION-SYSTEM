# src/utils/db.py
import duckdb  # Lightweight, perfect for analytics[citation:5]
import pandas as pd
from typing import Optional
from pathlib import Path

class DatabaseManager:
    """Manage local DuckDB database for reconciliation data"""
    
    def __init__(self, db_path: str = "data/marico_recon.duckdb"):
        self.db_path = db_path
        self.conn = self._create_connection()
        self._initialize_schema()
    
    def _create_connection(self):
        Path(self.db_path).parent.mkdir(exist_ok=True, parents=True)
        return duckdb.connect(self.db_path)
    
    def _initialize_schema(self):
        """Create tables if they don't exist"""
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_matches (
                match_id VARCHAR PRIMARY KEY,
                invoice_number VARCHAR,
                customer_id VARCHAR,
                marico_amount DECIMAL(15,2),
                customer_amount DECIMAL(15,2),
                variance DECIMAL(15,2),
                match_status VARCHAR,
                discrepancy_type VARCHAR,
                confidence_score FLOAT,
                resolution_status VARCHAR,
                created_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS claim_resolutions (
                claim_id VARCHAR PRIMARY KEY,
                discrepancy_type VARCHAR,
                status VARCHAR,
                auto_approvable BOOLEAN,
                expected_resolution_date DATE,
                reviewer_notes VARCHAR
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY,
                run_date TIMESTAMP,
                matches_count INTEGER,
                matched_count INTEGER,
                mismatch_count INTEGER
            )
        """)
    
    def save_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = 'append'):
        """Save DataFrame to database"""
        
        if if_exists == 'replace':
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        self.conn.register('df_temp', df)
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df_temp LIMIT 0")
        self.conn.execute(f"INSERT INTO {table_name} SELECT * FROM df_temp")
        self.conn.unregister('df_temp')
    
    def query(self, query_string: str) -> pd.DataFrame:
        """Execute query and return results as DataFrame"""
        return self.conn.execute(query_string).df()
    
    def get_open_reconcilations(self) -> pd.DataFrame:
        """Get all unresolved reconciliations"""
        return self.query("""
            SELECT * FROM reconciliation_matches 
            WHERE resolution_status != 'resolved'
            ORDER BY variance DESC
        """)