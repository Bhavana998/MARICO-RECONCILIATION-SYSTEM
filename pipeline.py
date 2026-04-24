# pipeline.py
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ReconciliationEngine:
    def __init__(self, tolerance=0.02):
        self.tolerance = tolerance
        self.results = None
    
    def load_data(self):
        """Load data from CSV files"""
        print("📂 Loading data...")
        
        try:
            self.marico_df = pd.read_csv('data/raw/marico_invoices.csv')
            self.customer_df = pd.read_csv('data/raw/customer_claims.csv')
            
            print(f"   ✅ Loaded {len(self.marico_df)} Marico records")
            print(f"   ✅ Loaded {len(self.customer_df)} Customer records")
            return True
        except Exception as e:
            print(f"   ❌ Error loading data: {e}")
            return False
    
    def reconcile(self):
        """Perform reconciliation"""
        print("\n🔄 Running reconciliation...")
        
        # Merge datasets
        merged = self.marico_df.merge(
            self.customer_df,
            on='invoice_number',
            how='outer',
            suffixes=('_marico', '_customer'),
            indicator=True
        )
        
        results = []
        
        for _, row in merged.iterrows():
            marico_amt = row.get('amount_marico', 0)
            customer_amt = row.get('amount_customer', 0)
            invoice = row['invoice_number']
            customer = row.get('customer_id_marico', row.get('customer_id_customer', 'Unknown'))
            
            # Handle missing data
            if pd.isna(marico_amt) or marico_amt == 0:
                status = 'missing_in_marico'
                variance = 0
                marico_amt = 0
                confidence = 0
            elif pd.isna(customer_amt) or customer_amt == 0:
                status = 'missing_in_customer'
                variance = 0
                customer_amt = 0
                confidence = 0
            else:
                variance = customer_amt - marico_amt
                variance_pct = abs(variance / marico_amt)
                
                if variance_pct <= self.tolerance:
                    status = 'matched'
                    confidence = 1.0 - variance_pct
                elif variance_pct <= 0.10:
                    status = 'partial_match'
                    confidence = 0.7
                else:
                    status = 'mismatch'
                    confidence = 0.3
            
            # Determine discrepancy type
            disc_type = 'none'
            if status in ['partial_match', 'mismatch'] and variance != 0:
                if row.get('discrepancy_type') in ['price', 'deduction', 'claim']:
                    disc_type = row.get('discrepancy_type')
                else:
                    disc_type = 'amount_mismatch'
            
            results.append({
                'invoice_number': invoice,
                'customer_id': customer,
                'marico_amount': round(marico_amt, 2),
                'customer_amount': round(customer_amt, 2),
                'variance': round(variance, 2),
                'match_status': status,
                'discrepancy_type': disc_type,
                'confidence_score': round(confidence, 2),
                'pod_available': row.get('pod_available', False)
            })
        
        self.results = pd.DataFrame(results)
        print(f"   ✅ Reconciliation complete: {len(self.results)} transactions processed")
        return self.results
    
    def generate_report(self):
        """Generate summary report"""
        print("\n📊 Generating report...")
        
        # Create reports directory
        Path('data/reports').mkdir(exist_ok=True, parents=True)
        
        # Summary statistics
        summary = {
            'metric': [
                'Total Transactions',
                'Matched',
                'Partial Matches',
                'Mismatches',
                'Missing in Marico',
                'Missing in Customer',
                'Auto-Approval Eligible',
                'Total Variance'
            ],
            'value': [
                len(self.results),
                len(self.results[self.results['match_status'] == 'matched']),
                len(self.results[self.results['match_status'] == 'partial_match']),
                len(self.results[self.results['match_status'] == 'mismatch']),
                len(self.results[self.results['match_status'] == 'missing_in_marico']),
                len(self.results[self.results['match_status'] == 'missing_in_customer']),
                len(self.results[abs(self.results['variance']) < 5000]),
                f"₹{self.results['variance'].sum():,.2f}"
            ]
        }
        
        summary_df = pd.DataFrame(summary)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save results
        self.results.to_csv(f'data/reports/reconciliation_results_{timestamp}.csv', index=False)
        summary_df.to_csv(f'data/reports/summary_{timestamp}.csv', index=False)
        
        # Print summary
        print("\n" + "="*60)
        print("                    RECONCILIATION SUMMARY")
        print("="*60)
        
        for i, row in summary_df.iterrows():
            if row['metric'] == 'Total Variance':
                print(f"{row['metric']:25} : {row['value']}")
            else:
                print(f"{row['metric']:25} : {int(row['value']):,}")
        
        print("="*60)
        
        # Customer-wise breakdown
        print("\n📊 Top 5 Customers by Variance:")
        customer_variance = self.results.groupby('customer_id')['variance'].sum().sort_values(ascending=False).head(5)
        for customer, variance in customer_variance.items():
            print(f"   {customer:20} : ₹{variance:>15,.2f}")
        
        print("\n📊 Discrepancy Type Breakdown:")
        disc_counts = self.results[self.results['discrepancy_type'] != 'none']['discrepancy_type'].value_counts()
        for disc_type, count in disc_counts.items():
            print(f"   {disc_type:20} : {count:>5} transactions")
        
        return summary_df
    
    def auto_resolve_claims(self):
        """Auto-resolve eligible claims"""
        print("\n🤖 Auto-resolving claims...")
        
        eligible = self.results[
            (abs(self.results['variance']) < 5000) & 
            (self.results['match_status'].isin(['partial_match', 'mismatch']))
        ]
        
        auto_resolved = []
        for _, claim in eligible.iterrows():
            resolution = {
                'claim_id': f"CLM_{datetime.now().timestamp()}_{claim['invoice_number']}",
                'invoice_number': claim['invoice_number'],
                'customer_id': claim['customer_id'],
                'amount': abs(claim['variance']),
                'resolution': 'auto_approved',
                'action': 'create_credit_note' if claim['variance'] < 0 else 'raise_debit_note',
                'resolved_date': datetime.now().strftime('%Y-%m-%d')
            }
            auto_resolved.append(resolution)
        
        if auto_resolved:
            resolved_df = pd.DataFrame(auto_resolved)
            resolved_df.to_csv(f'data/reports/auto_resolved_claims_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', index=False)
            print(f"   ✅ Auto-resolved {len(auto_resolved)} claims (total amount: ₹{resolved_df['amount'].sum():,.2f})")
        else:
            print("   ℹ️ No claims eligible for auto-resolution")
        
        return auto_resolved

def main():
    print("\n" + "="*60)
    print("     MARICO RECONCILIATION SYSTEM")
    print("="*60 + "\n")
    
    # Initialize engine
    engine = ReconciliationEngine(tolerance=0.02)
    
    # Load data
    if not engine.load_data():
        print("\n❌ Please run 'python generate_data.py' first to create sample data")
        return
    
    # Run reconciliation
    results = engine.reconcile()
    
    # Generate report
    summary = engine.generate_report()
    
    # Auto-resolve claims
    auto_resolved = engine.auto_resolve_claims()
    
    # Save master file
    master_file = f'data/reports/master_reconciliation_{datetime.now().strftime("%Y%m%d")}.xlsx'
    try:
        with pd.ExcelWriter(master_file, engine='openpyxl') as writer:
            results.to_excel(writer, sheet_name='Reconciliation Results', index=False)
            summary.to_excel(writer, sheet_name='Summary', index=False)
        print(f"\n💾 Master file saved: {master_file}")
    except Exception as e:
        print(f"\n⚠️ Could not create Excel file: {e}")
        print(f"   CSV files saved in data/reports/")
    
    print("\n✅ Pipeline execution complete!")
    print("\n📋 Next steps:")
    print("   1. Run: streamlit run dashboard.py")
    print("   2. Or open the CSV files in data/reports/")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()