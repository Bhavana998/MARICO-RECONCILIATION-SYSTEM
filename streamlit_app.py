# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# Page config
st.set_page_config(
    page_title="Marico Reconciliation System",
    page_icon="🏭",
    layout="wide"
)

# Custom CSS for dark mode
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
    border-radius: 10px;
    padding: 20px;
    border: 1px solid #2d2d3d;
}
.metric-card .value {
    color: #64ffda;
    font-size: 28px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Session state
if 'marico_data' not in st.session_state:
    st.session_state.marico_data = None
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = None
if 'results' not in st.session_state:
    st.session_state.results = None

st.title("🏭 Marico - Customer Reconciliation System")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## 🎛️ Settings")
    tolerance = st.slider("Matching Tolerance (%)", 0, 10, 2) / 100
    st.markdown("---")
    st.markdown("### 📤 Upload Files")
    
    marico_file = st.file_uploader("Marico Data (CSV/Excel)", type=['csv', 'xlsx'])
    customer_file = st.file_uploader("Customer Data (CSV/Excel)", type=['csv', 'xlsx'])

# Main tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔄 Reconcile", "📋 Instructions"])

# Tab 1: Dashboard
with tab1:
    if st.session_state.results is not None:
        df = st.session_state.results
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", len(df))
        with col2:
            st.metric("Matched", len(df[df['status'] == 'matched']))
        with col3:
            st.metric("Mismatches", len(df[df['status'] == 'mismatch']))
        with col4:
            st.metric("Total Variance", f"₹{df['variance'].sum():,.0f}")
        
        # Chart
        st.subheader("Match Status")
        status_counts = df['status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index, hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.subheader("Results")
        st.dataframe(df, use_container_width=True)
        
        # Download
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "reconciliation_results.csv")
    else:
        st.info("No results yet. Go to Reconcile tab to run reconciliation.")

# Tab 2: Reconcile
with tab2:
    if marico_file and customer_file:
        # Load data
        if marico_file.name.endswith('.csv'):
            marico_df = pd.read_csv(marico_file)
        else:
            marico_df = pd.read_excel(marico_file)
        
        if customer_file.name.endswith('.csv'):
            customer_df = pd.read_csv(customer_file)
        else:
            customer_df = pd.read_excel(customer_file)
        
        st.success(f"Loaded {len(marico_df)} Marico records and {len(customer_df)} customer records")
        
        # Find invoice column
        inv_col_m = None
        for col in marico_df.columns:
            if 'invoice' in col.lower() or 'inv' in col.lower():
                inv_col_m = col
                break
        
        inv_col_c = None
        for col in customer_df.columns:
            if 'invoice' in col.lower() or 'inv' in col.lower():
                inv_col_c = col
                break
        
        if inv_col_m and inv_col_c:
            if st.button("🚀 Run Reconciliation", type="primary"):
                with st.spinner("Processing..."):
                    results = []
                    customer_dict = {str(row[inv_col_c]): row for _, row in customer_df.iterrows()}
                    
                    for _, row in marico_df.iterrows():
                        invoice = str(row[inv_col_m])
                        marico_amt = float(row.iloc[1]) if len(row) > 1 else 0
                        
                        if invoice in customer_dict:
                            cust_row = customer_dict[invoice]
                            cust_amt = float(cust_row.iloc[1]) if len(cust_row) > 1 else 0
                            variance = cust_amt - marico_amt
                            
                            if abs(variance) / marico_amt <= tolerance:
                                status = 'matched'
                            elif abs(variance) / marico_amt <= 0.10:
                                status = 'partial_match'
                            else:
                                status = 'mismatch'
                        else:
                            status = 'missing'
                            variance = -marico_amt
                            cust_amt = 0
                        
                        results.append({
                            'invoice_number': invoice,
                            'marico_amount': round(marico_amt, 2),
                            'customer_amount': round(cust_amt, 2),
                            'variance': round(variance, 2),
                            'status': status
                        })
                    
                    st.session_state.results = pd.DataFrame(results)
                    st.success(f"Reconciliation complete! Processed {len(results)} transactions")
                    st.balloons()
        else:
            st.warning("Could not find invoice number columns. Ensure your files have 'invoice_number' or similar column.")
    else:
        st.info("Please upload both Marico and Customer data files in the sidebar.")

# Tab 3: Instructions
with tab3:
    st.markdown("""
    ### How to Use
    
    1. **Upload Files** in the sidebar
       - Marico Data: SAP export with invoice numbers and amounts
       - Customer Data: Customer claims/transactions
    
    2. **Adjust Tolerance** in sidebar (default 2%)
    
    3. **Click Run Reconciliation**
    
    4. **View Results** in Dashboard tab
    
    ### File Format Examples
    
    **Marico Data (CSV):**
    ```csv
    invoice_number,amount,customer_id
    INV-001,150000,RELIANCE
    INV-002,250000,AMAZON