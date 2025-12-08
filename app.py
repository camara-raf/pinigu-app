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
def render_sidebar_controls():
    with st.sidebar:
        st.divider()
        st.subheader("Data Controls")
        
        # Full Reload
        if st.button("🔄 Full Reload", help="Reads all files, maps categories, and updates balances.", width="stretch"):
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
        if st.button("🏷️ Refresh Mappings", help="Re-applies rules to loaded data. Faster than full reload.", width="stretch"):
            if st.session_state.consolidated_df is None:
                with st.spinner("Ingesting files (required)..."):
                    st.session_state.consolidated_df = ingest_transactions()
            
            with st.spinner("Mapping transactions..."):
                st.session_state.consolidated_df = map_transactions(st.session_state.consolidated_df)
            with st.spinner("Synthesizing data..."):
                st.session_state.consolidated_df = synthesize_transactions(st.session_state.consolidated_df)
                save_consolidated_data(st.session_state.consolidated_df)
            st.success("Mappings updated!")

        # Refresh Balances Only
        if st.button("⚖️ Refresh Balances", help="Re-calculates synthetic transactions. Fastest.", width="stretch"):
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

# --- Navigation Setup ---

def show_home_page():
    """Render the Home Page."""
    st.title("💰 Finance Analyzer")
    
    st.markdown("""
    Welcome to your personal Finance Analyzer. Use the sidebar to navigate between different sections.
    
    ### 📚 Sections
    
    * **Transaction Accounts**: Upload files and manage your bank statements.
    * **Balance Accounts**: Manage manual balance accounts and enter snapshots.
    * **Categorization**: Map your transactions to categories and sub-categories.
    * **Analysis**: Visualize your financial data with interactive dashboards.
    
    ### 🚀 Quick Actions
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload New Files", width="stretch"):
            st.switch_page(upload_page)
            
    with col2:
        if st.button("📊 Go to Dashboard", width="stretch"):
            st.switch_page(dashboard_page)
            
    with col3:
        if st.button("⚖️ Enter Balance", width="stretch"):
            st.switch_page(balance_entries_p)

    st.divider()
    st.caption("v2.0 - Multipage Edition")

# Define Pages
home_page = st.Page(show_home_page, title="Home", icon="🏠", default=True)

# Transaction Accounts
upload_page = st.Page(render_upload_files_tab, title="Upload Files", icon="📥")
file_mgmt_page = st.Page(render_file_management_tab, title="File Management", icon="📂")

# Balance Accounts
# Note: modifying previously imported module to use the new functions
# We need to re-import or access the new functions. Since we updated the file in place, 
# and 'from views.non_transaction_accounts import ...' was done at top, 
# simply importing the new functions here is safer or assuming they are available if we reload.
# To be safe, we'll import them locally here to ensure we get the updated definitions if module reloading was an issue (though in Streamlit it re-runs).
from views.non_transaction_accounts import manage_accounts_page, balance_entries_page
manage_accts_p = st.Page(manage_accounts_page, title="Manage Accounts", icon="📋")
balance_entries_p = st.Page(balance_entries_page, title="Balance Entries", icon="⚖️")

# Categorization
mapping_page = st.Page(render_mapping_tab, title="Rules Mapping", icon="🏷️")
bulk_mapping_page = st.Page(render_bulk_mapping_tab, title="Bulk Mapping", icon="📦")
manual_overwrite_page = st.Page(render_manual_overwrite_tab, title="Manual Overwrite", icon="✍️")

# Analysis
dashboard_page = st.Page(render_dashboard_tab, title="Dashboard", icon="📊")
dashboard_v1_page = st.Page(render_dashboard_v1_tab, title="Dashboard v1", icon="📉")
dashboard_old_page = st.Page(render_dashboard_tab_old, title="Dashboard Old", icon="📜")

# Navigation Structure
pg = st.navigation({
    "Main": [home_page],
    "Transaction Accounts": [upload_page, file_mgmt_page],
    "Balance Accounts": [manage_accts_p, balance_entries_p],
    "Categorization": [mapping_page, bulk_mapping_page, manual_overwrite_page],
    "Analysis": [dashboard_page, dashboard_v1_page, dashboard_old_page]
})

# Run Navigation
pg.run()

# Render Global Sidebar Controls
# This renders the sidebar elements on every page
render_sidebar_controls()
