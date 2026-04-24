# enhanced_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import hashlib
from datetime import datetime
import base64

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Marico Reconciliation System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Mode
def apply_dark_mode():
    st.markdown("""
    <style>
    /* Dark mode styles */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Main container */
    .main .block-container {
        background-color: #0e1117;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1a1c23;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #2d2d3d;
    }
    
    .metric-card h3 {
        color: #8892b0;
        font-size: 14px;
        margin-bottom: 10px;
    }
    
    .metric-card .value {
        color: #64ffda;
        font-size: 28px;
        font-weight: bold;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #4a4a5a;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background: #1a1c23;
    }
    
    /* Success message */
    .success-message {
        background-color: #1e3a3a;
        border-left: 4px solid #00ff9d;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    /* Data table */
    .dataframe {
        background-color: #1a1c23;
        color: #ffffff;
    }
    
    .dataframe th {
        background-color: #2a2a3e;
        color: #64ffda;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00c6fb 0%, #005bea 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,198,251,0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a1c23;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2a2a3e;
        border-radius: 5px;
        padding: 8px 16px;
        color: #8892b0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #00c6fb 0%, #005bea 100%);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Session state initialization
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'uploaded_marico_data' not in st.session_state:
    st.session_state.uploaded_marico_data = None
if 'uploaded_customer_data' not in st.session_state:
    st.session_state.uploaded_customer_data = None
if 'reconciliation_results' not in st.session_state:
    st.session_state.reconciliation_results = None
if 'scanned_docs' not in st.session_state:
    st.session_state.scanned_docs = []

# Apply dark mode
if st.session_state.dark_mode:
    apply_dark_mode()

# Title
st.title("🏭 Marico - Reconciliation System")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/data-configuration.png", width=80)
    st.markdown("## 🎛️ Controls")
    
    # Dark mode toggle
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    
    st.markdown("---")
    
    # Data source selection
    data_source = st.radio(
        "📊 Data Source",
        ["📁 Sample Data", "📤 Upload CSV", "📸 Scanned Documents"],
        index=0
    )
    
    st.markdown("---")
    
    # Settings
    st.markdown("### ⚙️ Settings")
    tolerance = st.slider(
        "Matching Tolerance (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Percentage variance allowed for matching"
    ) / 100
    
    auto_approve_limit = st.number_input(
        "💰 Auto-approval Limit (₹)",
        min_value=0,
        max_value=50000,
        value=5000,
        step=1000
    )

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "📤 Upload & Reconcile", 
    "📸 Document Scanner",
    "📋 History"
])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    if st.session_state.reconciliation_results is not None:
        df = st.session_state.reconciliation_results
        
        # Key Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_transactions = len(df)
        total_variance = df['variance'].sum()
        matched_count = len(df[df['match_status'] == 'matched'])
        mismatch_count = len(df[df['match_status'] == 'mismatch'])
        blocked_capital = df[df['match_status'].isin(['mismatch', 'partial_match'])]['variance'].abs().sum()
        
        with col1:
            st.metric("📊 Total Transactions", f"{total_transactions:,}")
        with col2:
            st.metric("💰 Total Variance", f"₹{total_variance:,.0f}")
        with col3:
            st.metric("✅ Matched", f"{matched_count:,}", 
                     delta=f"{(matched_count/total_transactions)*100:.0f}%" if total_transactions > 0 else None)
        with col4:
            st.metric("⚠️ Mismatches", f"{mismatch_count:,}")
        with col5:
            st.metric("🔒 Blocked Capital", f"₹{blocked_capital:,.0f}")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Match Status Distribution")
            status_counts = df['match_status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_sequence=['#00ff9d', '#ffd93d', '#ff6b6b', '#6c5ce7'],
                hole=0.3
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Variance by Customer")
            customer_var = df.groupby('customer_id')['variance'].sum().sort_values(ascending=False).head(10)
            if len(customer_var) > 0:
                fig = px.bar(
                    x=customer_var.values,
                    y=customer_var.index,
                    orientation='h',
                    color=customer_var.values,
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Data Table
        st.subheader("📋 Detailed Results")
        st.dataframe(
            df.head(100),
            use_container_width=True,
            hide_index=True
        )
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name=f"reconciliation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("👋 No data loaded yet. Go to the 'Upload & Reconcile' tab to get started!")

# ==================== TAB 2: UPLOAD & RECONCILE ====================
with tab2:
    st.header("📤 Upload Your Data Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Marico Data (SAP Export)")
        marico_file = st.file_uploader(
            "Upload Marico invoices CSV/Excel",
            type=['csv', 'xlsx', 'xls'],
            key="marico_upload"
        )
        
        if marico_file is not None:
            try:
                if marico_file.name.endswith('.csv'):
                    marico_df = pd.read_csv(marico_file)
                else:
                    marico_df = pd.read_excel(marico_file)
                
                st.session_state.uploaded_marico_data = marico_df
                st.success(f"✅ Loaded {len(marico_df)} records from {marico_file.name}")
                
                with st.expander("Preview Marico Data"):
                    st.dataframe(marico_df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    with col2:
        st.subheader("🏪 Customer Data")
        customer_file = st.file_uploader(
            "Upload Customer claims/transactions",
            type=['csv', 'xlsx', 'xls'],
            key="customer_upload"
        )
        
        if customer_file is not None:
            try:
                if customer_file.name.endswith('.csv'):
                    customer_df = pd.read_csv(customer_file)
                else:
                    customer_df = pd.read_excel(customer_file)
                
                st.session_state.uploaded_customer_data = customer_df
                st.success(f"✅ Loaded {len(customer_df)} records from {customer_file.name}")
                
                with st.expander("Preview Customer Data"):
                    st.dataframe(customer_df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # Sample data option
    st.markdown("---")
    st.subheader("📁 Or Use Sample Data")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Load Sample Data", use_container_width=True):
            try:
                if Path('data/raw/marico_invoices.csv').exists():
                    st.session_state.uploaded_marico_data = pd.read_csv('data/raw/marico_invoices.csv')
                    st.session_state.uploaded_customer_data = pd.read_csv('data/raw/customer_claims.csv')
                    st.success("✅ Sample data loaded successfully!")
                else:
                    st.warning("Sample data not found. Run 'python generate_data.py' first.")
            except Exception as e:
                st.error(f"Error loading sample data: {e}")
    
    # Run reconciliation button
    st.markdown("---")
    st.subheader("🔄 Run Reconciliation")
    
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("🚀 START RECONCILIATION", use_container_width=True, type="primary"):
            if st.session_state.uploaded_marico_data is not None and st.session_state.uploaded_customer_data is not None:
                with st.spinner("Processing reconciliation..."):
                    marico_df = st.session_state.uploaded_marico_data
                    customer_df = st.session_state.uploaded_customer_data
                    
                    # Find invoice number column
                    inv_col_marico = None
                    for col in marico_df.columns:
                        if 'invoice' in col.lower() or 'inv' in col.lower():
                            inv_col_marico = col
                            break
                    
                    inv_col_customer = None
                    for col in customer_df.columns:
                        if 'invoice' in col.lower() or 'inv' in col.lower():
                            inv_col_customer = col
                            break
                    
                    # Find amount columns
                    amount_col_marico = None
                    for col in marico_df.columns:
                        if 'amount' in col.lower() or 'total' in col.lower():
                            amount_col_marico = col
                            break
                    
                    amount_col_customer = None
                    for col in customer_df.columns:
                        if 'amount' in col.lower() or 'total' in col.lower():
                            amount_col_customer = col
                            break
                    
                    if inv_col_marico is None or inv_col_customer is None:
                        st.error("Could not find invoice number columns. Please ensure your files have 'invoice_number' or similar column.")
                    else:
                        # Perform matching
                        results = []
                        customer_dict = {}
                        for _, row in customer_df.iterrows():
                            key = str(row[inv_col_customer]).strip()
                            customer_dict[key] = row
                        
                        for _, marico_row in marico_df.iterrows():
                            invoice = str(marico_row[inv_col_marico]).strip()
                            marico_amt = float(marico_row[amount_col_marico]) if amount_col_marico else 0
                            
                            if invoice in customer_dict:
                                cust_row = customer_dict[invoice]
                                cust_amt = float(cust_row[amount_col_customer]) if amount_col_customer else 0
                                variance = cust_amt - marico_amt
                                variance_pct = abs(variance / marico_amt) if marico_amt != 0 else 1
                                
                                if variance_pct <= tolerance:
                                    status = 'matched'
                                    confidence = 1.0 - variance_pct
                                elif variance_pct <= 0.10:
                                    status = 'partial_match'
                                    confidence = 0.7
                                else:
                                    status = 'mismatch'
                                    confidence = 0.3
                            else:
                                status = 'missing_in_customer'
                                variance = -marico_amt
                                cust_amt = 0
                                confidence = 0
                            
                            results.append({
                                'invoice_number': invoice,
                                'customer_id': marico_row.get('customer_id', marico_row.get('customer', 'Unknown')),
                                'marico_amount': round(marico_amt, 2),
                                'customer_amount': round(cust_amt, 2),
                                'variance': round(variance, 2),
                                'match_status': status,
                                'confidence_score': round(confidence, 2)
                            })
                        
                        results_df = pd.DataFrame(results)
                        st.session_state.reconciliation_results = results_df
                        st.success(f"✅ Reconciliation complete! Processed {len(results_df)} transactions")
                        st.balloons()
                        st.info("💡 Go to the 'Dashboard' tab to view results!")
            else:
                st.warning("⚠️ Please upload both Marico and Customer data files first!")
    
    # Sample format templates
    with st.expander("📋 Need help with file format?"):
        st.markdown("**Expected CSV Format:**")
        st.markdown("**Marico Data:** invoice_number, customer_id, amount")
        st.markdown("**Customer Data:** invoice_number, customer_id, amount")
        st.markdown("The system will automatically detect columns containing 'invoice' and 'amount'.")

# ==================== TAB 3: DOCUMENT SCANNER ====================
with tab3:
    st.header("📸 Document Scanner & OCR")
    st.markdown("Upload scanned invoices, PODs, or claims for manual data extraction")
    
    uploaded_docs = st.file_uploader(
        "Upload scanned documents (PDF, PNG, JPG)",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    
    if uploaded_docs:
        for doc in uploaded_docs:
            doc_hash = hashlib.md5(doc.getvalue()).hexdigest()
            
            if not any(d['hash'] == doc_hash for d in st.session_state.scanned_docs):
                with st.expander(f"📄 {doc.name}"):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"**File Name:** {doc.name}")
                        st.markdown(f"**File Size:** {len(doc.getvalue()) / 1024:.1f} KB")
                    
                    with col2:
                        invoice_no = st.text_input("Invoice Number", key=f"inv_{doc_hash}")
                        amount = st.number_input("Amount (₹)", min_value=0.0, key=f"amt_{doc_hash}")
                        customer = st.text_input("Customer Name", key=f"cust_{doc_hash}")
                        
                        if st.button("✅ Save Extracted Data", key=f"save_{doc_hash}"):
                            st.session_state.scanned_docs.append({
                                'hash': doc_hash,
                                'filename': doc.name,
                                'invoice_number': invoice_no,
                                'amount': amount,
                                'customer': customer,
                                'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            st.success("Document data saved!")
                            st.rerun()
    
    if st.session_state.scanned_docs:
        st.markdown("---")
        st.subheader("📋 Scanned Documents Data")
        scanned_df = pd.DataFrame(st.session_state.scanned_docs)
        st.dataframe(scanned_df, use_container_width=True, hide_index=True)
        
        if st.button("📊 Use Scanned Data for Reconciliation"):
            scanned_data = []
            for doc in st.session_state.scanned_docs:
                if doc['invoice_number'] and doc['amount'] > 0:
                    scanned_data.append({
                        'invoice_number': doc['invoice_number'],
                        'customer_id': doc['customer'],
                        'amount': doc['amount']
                    })
            
            if scanned_data:
                scanned_df = pd.DataFrame(scanned_data)
                if st.session_state.uploaded_marico_data is not None:
                    combined = pd.concat([st.session_state.uploaded_marico_data, scanned_df], ignore_index=True)
                    st.session_state.uploaded_marico_data = combined
                    st.success(f"Added {len(scanned_data)} scanned documents to Marico data!")
                else:
                    st.session_state.uploaded_marico_data = scanned_df
                    st.success(f"Created Marico data from {len(scanned_data)} scanned documents!")

# ==================== TAB 4: HISTORY ====================
with tab4:
    st.header("📋 Reconciliation History")
    
    reports_dir = Path('data/reports')
    if reports_dir.exists():
        result_files = list(reports_dir.glob('reconciliation_results_*.csv'))
        
        if result_files:
            st.subheader("📁 Previous Reconciliation Runs")
            for file in sorted(result_files, reverse=True)[:10]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"📄 **{file.name}**")
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    st.caption(f"Created: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    if st.button("👁️ View", key=f"view_{file.name}"):
                        df = pd.read_csv(file)
                        st.session_state.reconciliation_results = df
                        st.success(f"Loaded {file.name}")
                        st.info("Go to Dashboard tab to see results!")
        else:
            st.info("No previous reconciliation runs found.")
    else:
        st.info("No history available yet.")

# Footer
st.markdown("---")
st.markdown("🏭 Marico Reconciliation System v2.0 | Powered by AI & Analytics")