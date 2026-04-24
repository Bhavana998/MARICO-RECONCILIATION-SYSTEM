# src/reconciliators/claim_resolver.py
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ClaimResolver:
    """Handle claim and deduction resolution"""
    
    def __init__(self, resolution_rules: Dict = None):
        self.rules = resolution_rules or self._default_rules()
    
    def _default_rules(self) -> Dict:
        return {
            'promotion_settlement': {
                'auto_approve_limit': 5000,
                'required_docs': ['promotion_proof', 'customer_signoff'],
                'resolution_days': 5
            },
            'logistics_deduction': {
                'auto_approve_limit': 1000,
                'required_docs': ['delivery_note', 'pod'],
                'resolution_days': 3
            },
            'damage_claim': {
                'auto_approve_limit': 2500,
                'required_docs': ['damage_report', 'photographic_evidence'],
                'resolution_days': 7
            },
            'price_discrepancy': {
                'auto_approve_limit': 2000,
                'required_docs': ['price_agreement'],
                'resolution_days': 10
            }
        }
    
    def resolve_claim(self, claim_data: pd.Series) -> Dict:
        """Resolve a single claim based on rules"""
        
        claim_type = claim_data.get('discrepancy_type', 'price_discrepancy')
        rule = self.rules.get(claim_type, self.rules['price_discrepancy'])
        
        resolution = {
            'claim_id': claim_data.get('claim_id', f"CLM_{datetime.now().timestamp()}"),
            'discrepancy_type': claim_type,
            'status': 'pending_review',
            'recommended_action': None,
            'auto_approvable': False,
            'reviewer_notes': []
        }
        
        amount = abs(claim_data.get('variance', 0))
        
        # Auto-approval logic
        if amount <= rule['auto_approve_limit'] and self._has_required_docs(claim_data, rule):
            resolution['status'] = 'auto_approved'
            resolution['auto_approvable'] = True
            resolution['recommended_action'] = 'create_credit_note'
            resolution['reviewer_notes'].append(f"Auto-approved under {claim_type} rules")
        else:
            if amount > rule['auto_approve_limit']:
                resolution['reviewer_notes'].append(f"Amount {amount} exceeds auto-approve limit of {rule['auto_approve_limit']}")
            
            if not self._has_required_docs(claim_data, rule):
                missing = [doc for doc in rule['required_docs'] if not self._doc_available(claim_data, doc)]
                resolution['reviewer_notes'].append(f"Missing documents: {', '.join(missing)}")
        
        # Calculate resolution timeline
        resolution['expected_resolution_date'] = datetime.now() + timedelta(days=rule['resolution_days'])
        
        return resolution
    
    def _has_required_docs(self, claim_data: pd.Series, rule: Dict) -> bool:
        """Check if all required documents are available"""
        return all(self._doc_available(claim_data, doc) for doc in rule['required_docs'])
    
    def _doc_available(self, claim_data: pd.Series, doc_type: str) -> bool:
        """Check availability of specific document type"""
        doc_mapping = {
            'promotion_proof': 'promotion_document',
            'customer_signoff': 'signed_agreement',
            'delivery_note': 'delivery_note_url',
            'pod': 'pod_available',
            'damage_report': 'damage_report_url',
            'photographic_evidence': 'photos_available',
            'price_agreement': 'price_contract_url'
        }
        
        col_name = doc_mapping.get(doc_type, doc_type)
        return claim_data.get(col_name, False) is not False