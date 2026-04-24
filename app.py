import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Marico Reconciliation", layout="wide")

st.title("🏭 Marico - Customer Reconciliation Dashboard")

# Load results
results_path = Path('data/reports/reconciliation_results.csv')

if not results_path.exists():
    st.warning("No reconciliation results found. Please run the pipeline first.")
    st.code("python src/pipeline.py", language="bash")
    st.stop()

df = pd.read_csv(results_path)

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Transactions", len(df))
with col2:
    matched = len(df[df['status'] == 'matched'])
    st.metric("Matched", f"{matched} ({matched/len(df)*100:.0f}%)")
with col3:
    mismatches = len(df[df['status'] == 'mismatch'])
    st.metric("Mismatches", f"{mismatches} ({mismatches/len(df)*100:.0f}%)")
with col4:
    total_variance = df['variance'].sum()
    st.metric("Total Variance", f"₹{total_variance:,.2f}")

# Charts
col1, col2 = st.columns(2)

with col1:
    status_counts = df['status'].value_counts()
    fig = px.pie(values=status_counts.values, names=status_counts.index, title="Status Distribution")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Top mismatches by customer
    cust_variance = df.groupby('customer')['variance'].sum().sort_values(ascending=False).head(10)
    if len(cust_variance) > 0:
        fig = px.bar(x=cust_variance.values, y=cust_variance.index, orientation='h', 
                     title="Top Customers by Variance")
        st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("📋 Detailed Results")
st.dataframe(df, use_container_width=True, hide_index=True)

# Variance histogram
st.subheader("📊 Variance Distribution")
fig = px.histogram(df[df['variance'] != 0], x='variance', nbins=50, 
                   title="Distribution of Variances")
st.plotly_chart(fig, use_container_width=True)

# Download button
csv = df.to_csv(index=False)
st.download_button(
    label="📥 Download Results as CSV",
    data=csv,
    file_name="reconciliation_results.csv",
    mime="text/csv"
)