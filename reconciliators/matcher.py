# src/reconciliators/matcher.py
import pandas as pd
import numpy as np
import recordlinkage as rl
from fuzzywuzzy import fuzz
from typing import Tuple, List, Dict
from datetime import datetime, timedelta
from ..models.schemas import ReconciliationResult, MatchStatus

class InvoiceMatcher:
    """Core matching engine for invoice reconciliation"""
    
    def __init__(self, tolerance_percentage: float = 0.02):
        """
        Args:
            tolerance_percentage: Acceptable variance (e.g., 0.02 = 2%)
        """
        self.tolerance = tolerance_percentage
    
    def reconcile(self, 
                  marico_df: pd.DataFrame, 
                  customer_df: pd.DataFrame) -> pd.DataFrame:
        """
        Main reconciliation function
        """
        results = []
        
        # Clean and prepare data
        marico_df = self._clean_data(marico_df, 'marico')
        customer_df = self._clean_data(customer_df, 'customer')
        
        # Step 1: Exact matching on invoice number
        exact_matches = self._exact_invoice_match(marico_df, customer_df)
        
        # Step 2: Fuzzy matching for tricky invoices
        fuzzy_matches = self._fuzzy_invoice_match(marico_df, customer_df)
        
        # Step 3: Amount-based matching for unmatched
        amount_matches = self._amount_based_match(marico_df, customer_df)
        
        # Combine all matches and classify
        all_matches = pd.concat([exact_matches, fuzzy_matches, amount_matches])
        
        for _, match in all_matches.iterrows():
            result = self._classify_match(match)
            results.append(result.dict())
        
        return pd.DataFrame(results)
    
    def _clean_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Standardize data formats"""
        # Standardize numeric columns
        numeric_cols = ['amount', 'tax_amount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Standardize date columns
        if 'invoice_date' in df.columns:
            df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['invoice_number'], keep='first')
        
        df['source'] = source
        return df
    
    def _exact_invoice_match(self, marico_df: pd.DataFrame, 
                             customer_df: pd.DataFrame) -> pd.DataFrame:
        """Find exact matches by invoice number"""
        
        merged = marico_df.merge(
            customer_df,
            on='invoice_number',
            how='inner',
            suffixes=('_marico', '_customer')
        )
        
        merged['match_type'] = 'exact_invoice'
        return merged
    
    def _fuzzy_invoice_match(self, marico_df: pd.DataFrame, 
                             customer_df: pd.DataFrame, 
                             threshold: int = 85) -> pd.DataFrame:
        """Find matches using fuzzy string matching on invoice numbers"""
        
        matches = []
        
        for _, marico_row in marico_df.iterrows():
            marico_inv = str(marico_row['invoice_number']).strip()
            
            for _, cust_row in customer_df.iterrows():
                cust_inv = str(cust_row['invoice_number']).strip()
                
                # Calculate similarity
                similarity = fuzz.ratio(marico_inv, cust_inv)
                
                if similarity >= threshold:
                    match = pd.Series({
                        'invoice_number': marico_inv,
                        'invoice_number_marico': marico_inv,
                        'invoice_number_customer': cust_inv,
                        'fuzzy_score': similarity,
                        **{f"{col}_marico": marico_row[col] for col in marico_df.columns},
                        **{f"{col}_customer": cust_row[col] for col in customer_df.columns}
                    })
                    matches.append(match)
        
        if matches:
            matches_df = pd.DataFrame(matches)
            matches_df['match_type'] = 'fuzzy_invoice'
            return matches_df
        else:
            return pd.DataFrame()
    
    def _amount_based_match(self, marico_df: pd.DataFrame, 
                            customer_df: pd.DataFrame) -> pd.DataFrame:
        """Match based on invoice amount and date proximity"""
        # Use blocking strategy for efficiency[citation:6]
        indexer = rl.Index()
        
        # Block by customer to reduce comparisons
        indexer.block('customer_id')
        
        # Create candidate pairs
        candidate_links = indexer.index(marico_df, customer_df)
        
        # Compare amounts
        compare_cl = rl.Compare()
        compare_cl.numeric('amount_marico', 'amount_customer', 
                          method='gauss',  # Gaussian similarity
                          threshold=2.5,   # Standard deviations
                          label='amount')
        
        compare_cl.date('invoice_date_marico', 'invoice_date_customer',
                       method='linear', offset=5,  # Allow 5 days difference
                       label='date_diff')
        
        # Compute similarity scores
        features = compare_cl.compute(candidate_links, marico_df, customer_df)
        
        # Filter good matches
        matches = features[features['amount'] > 0.8]  # 80% amount similarity
        
        if len(matches) == 0:
            return pd.DataFrame()
        
        # Convert to DataFrame
        match_indices = matches.index.values
        match_rows = []
        
        for idx in match_indices:
            marico_idx, cust_idx = idx
            marico_row = marico_df.loc[marico_idx]
            cust_row = customer_df.loc[cust_idx]
            
            match_row = pd.Series({
                'invoice_number': marico_row['invoice_number'],
                'match_type': 'amount_based',
                **{f"{col}_marico": marico_row[col] for col in marico_df.columns},
                **{f"{col}_customer": cust_row[col] for col in customer_df.columns}
            })
            match_rows.append(match_row)
        
        return pd.DataFrame(match_rows)
    
    def _classify_match(self, match: pd.Series) -> ReconciliationResult:
        """Classify the match type and discrepancy"""
        
        amount_marico = match.get('amount_marico', 0)
        amount_customer = match.get('amount_customer', 0)
        variance = amount_customer - amount_marico
        
        # Calculate variance percentage
        if amount_marico != 0:
            variance_pct = abs(variance / amount_marico)
        else:
            variance_pct = 1.0 if variance != 0 else 0
        
        # Determine match status
        if variance_pct <= self.tolerance:
            match_status = MatchStatus.MATCHED
            discrepancy_type = None
            confidence = 1.0 - variance_pct
        elif variance_pct <= 0.10:  # 10% variance
            match_status = MatchStatus.PARTIAL
            discrepancy_type = self._identify_discrepancy_type(match)
            confidence = 0.7
        else:
            match_status = MatchStatus.MISMATCH
            discrepancy_type = self._identify_discrepancy_type(match)
            confidence = 0.3
        
        # Check for missing documents
        if 'pod_available' in match and not match['pod_available']:
            discrepancy_type = 'missing_pod'
            match_status = MatchStatus.UNDER_REVIEW
        
        return ReconciliationResult(
            match_id=f"match_{match['invoice_number']}_{datetime.now().timestamp()}",
            invoice_number=match['invoice_number'],
            customer_id=match.get('customer_id_marico', match.get('customer_id_customer', 'unknown')),
            marico_amount=amount_marico,
            customer_amount=amount_customer,
            variance=variance,
            match_status=match_status,
            discrepancy_type=discrepancy_type,
            confidence_score=confidence
        )
    
    def _identify_discrepancy_type(self, match: pd.Series) -> str:
        """Identify the type of discrepancy based on available data"""
        
        # Check for price vs quantity discrepancy
        if 'quantity_marico' in match and 'quantity_customer' in match:
            if match['quantity_marico'] != match['quantity_customer']:
                return 'quantity_discrepancy'
        
        # Check for claims/deductions
        if 'claim_amount' in match and match['claim_amount'] > 0:
            return 'claim_dispute'
        
        if 'logistics_deduction' in match and match['logistics_deduction'] > 0:
            return 'logistics_deduction'
        
        return 'price_discrepancy'