# generate_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Create directories
os.makedirs('data/raw', exist_ok=True)

print("="*60)
print("GENERATING SAMPLE DATA")
print("="*60)

# Set random seed
np.random.seed(42)
random.seed(42)

# Generate sample Marico invoices
num_invoices = 500
start_date = datetime(2024, 1, 1)

marico_data = []
customers = ['RELIANCE_001', 'AMAZON_002', 'FLIPKART_003', 'DMART_004', 'BIGBASKET_005']

for i in range(num_invoices):
    invoice_date = start_date + timedelta(days=random.randint(0, 90))
    customer = random.choice(customers)
    amount = random.uniform(5000, 500000)
    
    marico_data.append({
        'invoice_number': f'INV_{2024}_{i+1000}',
        'invoice_date': invoice_date.strftime('%Y-%m-%d'),
        'customer_id': customer,
        'customer_name': customer.split('_')[0].title(),
        'amount': round(amount, 2),
        'tax_amount': round(amount * 0.18, 2),
        'status': 'paid' if random.random() > 0.3 else 'pending'
    })

marico_df = pd.DataFrame(marico_data)

# Generate sample customer data with mismatches
customer_data = []
for _, row in marico_df.iterrows():
    has_mismatch = random.random() < 0.3
    
    if has_mismatch:
        discrepancy_type = random.choice(['price', 'deduction', 'claim'])
        
        if discrepancy_type == 'price':
            amount = row['amount'] * random.uniform(0.9, 0.98)
        elif discrepancy_type == 'deduction':
            amount = row['amount'] - random.uniform(1000, 10000)
        else:
            amount = row['amount'] - random.uniform(500, 5000)
    else:
        amount = row['amount']
    
    customer_data.append({
        'invoice_number': row['invoice_number'],
        'invoice_date': row['invoice_date'],
        'customer_id': row['customer_id'],
        'amount': round(amount, 2),
        'claim_amount': round(row['amount'] - amount, 2) if has_mismatch else 0,
        'discrepancy_type': discrepancy_type if has_mismatch else 'none',
        'pod_available': random.random() > 0.1
    })

customer_df = pd.DataFrame(customer_data)

# Save to CSV
marico_df.to_csv('data/raw/marico_invoices.csv', index=False)
customer_df.to_csv('data/raw/customer_claims.csv', index=False)

print(f"\n✅ Created {len(marico_df)} Marico invoices")
print(f"✅ Created {len(customer_df)} Customer records")
print(f"📊 Mismatch rate: {(customer_df['claim_amount'] > 0).sum() / len(customer_df) * 100:.1f}%")
print("\n" + "="*60)
print("✅ Data generation complete!")
print("Next step: Run 'streamlit run enhanced_dashboard.py'")
print("="*60)