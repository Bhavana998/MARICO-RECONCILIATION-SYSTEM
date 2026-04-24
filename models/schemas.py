cat > src/models/schemas.py << 'EOF'
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

class TransactionType(str, Enum):
    INVOICE = "invoice"
    PAYMENT = "payment"
    CLAIM = "claim"
    CREDIT_NOTE = "credit_note"
    DEDUCTION = "deduction"

class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    UNMATCHED = "unmatched"
    UNDER_REVIEW = "under_review"

class DiscrepancyType(str, Enum):
    PRICE = "price_discrepancy"
    QUANTITY = "quantity_discrepancy"
    MISSING_POD = "missing_pod"
    CLAIM_DISPUTE = "claim_dispute"
    LOGISTICS_DEDUCTION = "logistics_deduction"
    DAMAGE_CLAIM = "damage_claim"
    PROMOTION_SETTLEMENT = "promotion_settlement"

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: datetime
    customer_id: str
    customer_name: str
    amount: Decimal = Field(decimal_places=2)
    tax_amount: Decimal = Field(default=0, decimal_places=2)
    status: str
    document_path: Optional[str] = None
    source_system: str = "SAP"
    
class CustomerClaim(BaseModel):
    claim_id: str
    customer_id: str
    invoice_reference: Optional[str] = None
    claim_type: str
    claim_amount: Decimal = Field(decimal_places=2)
    claim_date: datetime
    status: str
    supporting_docs: Optional[List[str]] = None
    
class ReconciliationResult(BaseModel):
    match_id: str
    invoice_number: str
    customer_id: str
    marico_amount: Decimal
    customer_amount: Decimal
    variance: Decimal
    match_status: MatchStatus
    discrepancy_type: Optional[DiscrepancyType]
    confidence_score: float = Field(ge=0, le=1)
    resolution_status: str = "open"
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None
EOF