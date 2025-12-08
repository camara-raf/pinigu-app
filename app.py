import streamlit as st

# Page configuration - MUST be called first before any other Streamlit commands
st.set_page_config(page_title="💰 Finance Analyzer", layout="wide")

import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime

# Import logger
from utils.logger import get_logger
logger = get_logger()

# Import Views
from views.upload_files import render_upload_files_tab
from views.file_management import render_file_management_tab
from views.mapping import render_mapping_tab
from views.bulk_mapping import render_bulk_mapping_tab
from views.manual_overwrite import render_manual_overwrite_tab
from views.non_transaction_accounts import render_non_transaction_accounts_tab
from views.dashboard import render_dashboard_tab
from views.dashboard_v1 import render_dashboard_v1_tab
from views.dashboard_old import render_dashboard_tab_old

# Import Utils
from utils import (
    ingest_transactions,
    map_transactions,
    synthesize_transactions,
    save_consolidated_data,
    load_consolidated_data
)

# Initialize session state
if 'data_refresh_needed' not in st.session_state:
    st.session_state.data_refresh_needed = False
if 'last_load_timestamp' not in st.session_state:
    st.session_state.last_load_timestamp = None

# Cache for dataframes to support granular refresh
if 'consolidated_df' not in st.session_state:
    st.session_state.consolidated_df = None

# Optimization: Hydrate session state from disk if available or if refresh needed
if st.session_state.consolidated_df is None or st.session_state.data_refresh_needed:
    try:
        logger.info("Refresh trigger: no consolidated_df or data_refresh_needed")
        df = load_consolidated_data()
        if not df.empty and 'Transaction_Source' in df.columns:
            # We use the file-based transactions as our 'raw' and 'mapped' starting point
            # This avoids re-reading Excel files on every refresh
            file_txns = df[df['Transaction_Source'] == 'File'].copy()
            st.session_state.consolidated_df = file_txns
            st.session_state.last_load_timestamp = datetime.fromtimestamp(os.path.getmtime("data/consolidated_transactions.csv"))
            st.session_state.data_refresh_needed = False
            logger.info(f"Hydrated {len(file_txns)} transactions from disk.")
    except Exception as e:
        logger.error(f"Could not hydrate from disk: {e}")

# Sidebar - Data Controls
with st.sidebar:
    st.title("💰 Finance Analyzer")
    st.divider()
    
    st.subheader("Data Controls")
    
    # Full Reload
    if st.button("🔄 Full Reload", help="Reads all files, maps categories, and updates balances.", use_container_width=True):
        with st.spinner("Ingesting files..."):
            st.session_state.consolidated_df = ingest_transactions()
        with st.spinner("Mapping transactions..."):
            st.session_state.consolidated_df = map_transactions(st.session_state.consolidated_df)
        with st.spinner("Synthesizing data..."):
            st.session_state.consolidated_df = synthesize_transactions(st.session_state.consolidated_df)
            save_consolidated_data(st.session_state.consolidated_df)
        st.session_state.last_load_timestamp = datetime.now()
        st.session_state.data_refresh_needed = False
        st.success("Full reload complete!")
        
    # Refresh Mappings Only
    if st.button("🏷️ Refresh Mappings", help="Re-applies rules to loaded data. Faster than full reload.", use_container_width=True):
        if st.session_state.consolidated_df is None:
            # If raw data isn't in memory, we must ingest first (or load from disk if we had a way to save raw)
            # For now, let's trigger ingest if missing
            with st.spinner("Ingesting files (required)..."):
                st.session_state.consolidated_df = ingest_transactions()
        
        with st.spinner("Mapping transactions..."):
            st.session_state.consolidated_df = map_transactions(st.session_state.consolidated_df)
        with st.spinner("Synthesizing data..."):
            st.session_state.consolidated_df = synthesize_transactions(st.session_state.consolidated_df)
            save_consolidated_data(st.session_state.consolidated_df)
        st.success("Mappings updated!")

    # Refresh Balances Only
    if st.button("⚖️ Refresh Balances", help="Re-calculates synthetic transactions. Fastest.", use_container_width=True):
        if st.session_state.consolidated_df is None:
            with st.spinner("Ingesting files (required)..."):
                st.session_state.consolidated_df = ingest_transactions()
        with st.spinner("Mapping transactions (required)..."):
            st.session_state.consolidated_df = map_transactions(st.session_state.consolidated_df)
        
        with st.spinner("Synthesizing data..."):
            st.session_state.consolidated_df = synthesize_transactions(st.session_state.consolidated_df)
            save_consolidated_data(st.session_state.consolidated_df)
        st.success("Balances updated!")
        
    if st.session_state.last_load_timestamp:
        st.caption(f"Last update: {st.session_state.last_load_timestamp.strftime('%H:%M:%S')}")

# Main Layout
st.title("💰 Finance Analysis Dashboard")

# Create main tabs
tab_input, tab_cat, tab_analysis, tab_analysis_v1, tab_analysis_old = st.tabs([
    "📥 Input & Data",
    "🏷️ Categorization",
    "📊 Analysis",
    "📊 Analysis v1",
    "📊 Analysis Old"
])

# Tab 1: Input & Data
with tab_input:
    st.info("Manage your data sources here. Upload files, manage existing files, and configure non-transaction accounts.")
    subtab_upload, subtab_manage, subtab_nontrx = st.tabs([
        "Upload Files",
        "File Management",
        "Non-Transaction Accounts"
    ])
    
    with subtab_upload:
        render_upload_files_tab()
    with subtab_manage:
        render_file_management_tab()
    with subtab_nontrx:
        render_non_transaction_accounts_tab()

# Tab 2: Categorization
with tab_cat:
    st.info("Define how your transactions are categorized. Rules are applied in order.")
    subtab_mapping, subtab_bulk, subtab_manual = st.tabs([
        "Category Mapping",
        "Bulk Mapping",
        "Manual Overwrites"
    ])
    
    with subtab_mapping:
        render_mapping_tab()
    with subtab_bulk:
        render_bulk_mapping_tab()
    with subtab_manual:
        render_manual_overwrite_tab()

# Tab 3: Analysis
with tab_analysis:
    render_dashboard_tab()

# Tab 4: Analysis v1
with tab_analysis_v1:
    render_dashboard_v1_tab()

# Tab 5: Analysis Old
with tab_analysis_old:
    render_dashboard_tab_old()

# Footer
st.divider()
st.caption("💰 Finance Analysis Dashboard | Built with Streamlit")
