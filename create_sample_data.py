# create_sample_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Generate sample Marico invoices
num_invoices = 1000
start_date = datetime(2024, 1, 1)

marico_data = []
customers = ['RELIANCE_001', 'AMAZON_002', 'FLIPKART_003', 'DMART_004', 'BIGBASKET_005']

for i in range(num_invoices):
    invoice_date = start_date + timedelta(days=random.randint(0, 90))
    customer = random.choice(customers)
    amount = random.uniform(5000, 500000)
    
    marico_data.append({
        'invoice_number': f'INV_{2024}_{i+1000}',
        'invoice_date': invoice_date,
        'customer_id': customer,
        'customer_name': customer.split('_')[0].title(),
        'amount': round(amount, 2),
        'tax_amount': round(amount * 0.18, 2),
        'status': 'paid' if random.random() > 0.3 else 'pending',
        'source_system': 'SAP'
    })

marico_df = pd.DataFrame(marico_data)

# Generate sample customer data (with some mismatches)
customer_data = []
for _, row in marico_df.iterrows():
    # Create discrepancies (30% of transactions have some mismatch)
    has_mismatch = random.random() < 0.3
    
    if has_mismatch:
        # Create different types of discrepancies
        discrepancy_type = random.choice(['price', 'quantity', 'deduction', 'claim'])
        
        if discrepancy_type == 'price':
            amount = row['amount'] * random.uniform(0.9, 0.98)
        elif discrepancy_type == 'deduction':
            amount = row['amount'] - random.uniform(1000, 10000)
        else:
            amount = row['amount']
    else:
        amount = row['amount']
    
    customer_data.append({
        'invoice_number': row['invoice_number'],
        'invoice_date': row['invoice_date'],
        'customer_id': row['customer_id'],
        'amount': round(amount, 2),
        'claim_amount': round(row['amount'] - amount, 2) if has_mismatch else 0,
        'discrepancy_type': discrepancy_type if has_mismatch else None,
        'pod_available': random.random() > 0.1
    })

customer_df = pd.DataFrame(customer_data)

# Save to CSV files
marico_df.to_csv('data/raw/marico_invoices.csv', index=False)
customer_df.to_csv('data/raw/customer_claims.csv', index=False)

print(f"✅ Created {len(marico_df)} Marico invoices")
print(f"✅ Created {len(customer_df)} Customer records")
print(f"📊 Mismatch rate: {(customer_df['claim_amount'] > 0).sum() / len(customer_df) * 100:.1f}%")