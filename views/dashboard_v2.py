import streamlit as st
import pandas as pd
from utils import read_bank_mapping, get_logger
from views.dash_utils import get_available_options
from views.dash_monthly_balance import render_monthly_balance_tab
from views.dash_details import render_details_tab
from views.dash_expenses import render_expenses_tab
from views.dash_income import render_income_tab
from views.dash_investments import render_investments_tab

logger = get_logger(__name__)

def render_dashboard_v2_tab():
    """Render the Dashboard tab (v2)."""
    st.header("📊 Dashboard v2")
    
    consolidated_df = st.session_state.consolidated_df.copy()
    logger.debug(f"Consolidated df shape: {consolidated_df.shape}")
    bank_mapping_df = read_bank_mapping()
    bank_mapping_df['Bank_Account_key'] = bank_mapping_df['Bank'] + ' ' + bank_mapping_df['Account']
    consolidated_df['Bank_Account_key'] = consolidated_df['Bank'] + ' ' + consolidated_df['Account']
    logger.debug(f"Consolidated df shape: {consolidated_df.shape}")
    consolidated_df = pd.merge(consolidated_df, bank_mapping_df[['Bank_Account_key', 'Owner']], how='left', on='Bank_Account_key')
    logger.debug(f"Consolidated df shape: {consolidated_df.shape}")
    consolidated_df = consolidated_df.drop(columns=['Bank_Account_key'])
    logger.debug(f"Consolidated df shape: {consolidated_df.shape}")
    del bank_mapping_df
    
    # Create Year-Month column for sorting and display
    consolidated_df['YearMonth'] = consolidated_df['Transaction Date'].dt.to_period('M').astype(str)
    consolidated_df['Month_Name'] = consolidated_df['Transaction Date'].dt.strftime('%B')
    consolidated_df['Year'] = consolidated_df['Transaction Date'].dt.year
    
    logger.debug(f"Consolidated df shape: {consolidated_df.shape}")
    if consolidated_df.empty:
        st.info("📭 No transaction data available. Please upload files and reload data in the 'File Management' tab.")
    else:
        # Filter columns
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        years = sorted(consolidated_df['Year'].unique().tolist(), reverse=True)
        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        # Year and Month filters (independent)
        with col1:
            selected_year = st.selectbox("Year", ['All'] + years, key="year_filter")
        
        with col2:
            selected_month = st.selectbox("Month", months, key="month_filter")
        
        # Get current filter selections (will be empty on first render)
        selected_owners = st.session_state.get("owner_filter", [])
        selected_banks = st.session_state.get("bank_filter", [])
        selected_accounts = st.session_state.get("account_filter", [])
        selected_categories = st.session_state.get("category_filter", [])
        selected_sub_categories = st.session_state.get("subcategory_filter", [])
        
        # Create a dict of current selections for easy passing
        current_selections = {
            'Owner': selected_owners,
            'Bank': selected_banks,
            'Account': selected_accounts,
            'Category': selected_categories,
            'Sub-Category': selected_sub_categories
        }
        
        # Base dataframe for filter options (all unique combinations)
        filters_base_df = consolidated_df[['Owner', 'Bank', 'Account', 'Category', 'Sub-Category']].drop_duplicates().copy()
        
        # Render cascading filters
        with col7:
            owners = get_available_options(filters_base_df, 'Owner', current_selections)
            selected_owners = st.multiselect("Owner", owners, default=selected_owners, key="owner_filter")
            
        with col3:
            banks = get_available_options(filters_base_df, 'Bank', current_selections)
            selected_banks = st.multiselect("Bank", banks, default=selected_banks, key="bank_filter")

        with col4:
            accounts = get_available_options(filters_base_df, 'Account', current_selections)
            selected_accounts = st.multiselect("Account", accounts, default=selected_accounts, key="account_filter")
            
        with col5:
            categories = get_available_options(filters_base_df, 'Category', current_selections)
            selected_categories = st.multiselect("Category", categories, default=selected_categories, key="category_filter")
            
        with col6:
            sub_categories = get_available_options(filters_base_df, 'Sub-Category', current_selections)
            selected_sub_categories = st.multiselect("Sub-Category", sub_categories, default=selected_sub_categories, key="subcategory_filter")
        
        # Apply all filters to the main dataframe
        filtered_df = consolidated_df.copy()
        
        # Apply Year and Month filters
        if selected_year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == int(selected_year)]
        
        if selected_month != 'All':
            month_num = months.index(selected_month)
            filtered_df = filtered_df[filtered_df['Transaction Date'].dt.month == month_num]
        
        # Apply cascading filters
        if selected_owners:
            filtered_df = filtered_df[filtered_df['Owner'].isin(selected_owners)]
            
        if selected_banks:
            filtered_df = filtered_df[filtered_df['Bank'].isin(selected_banks)]
            
        if selected_accounts:
            filtered_df = filtered_df[filtered_df['Account'].isin(selected_accounts)]
            
        if selected_categories:
            filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]
            
        if selected_sub_categories:
            filtered_df = filtered_df[filtered_df['Sub-Category'].isin(selected_sub_categories)]
        
        #st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Monthly Balance", "Details", "Expenses", "Income", "Investments"])

        with tab1:
            render_monthly_balance_tab(consolidated_df, selected_year, selected_owners, selected_banks, selected_accounts)
        
        with tab2:
            render_details_tab(filtered_df)
        
        with tab3:
            render_expenses_tab(filtered_df)
        
        with tab4:
            render_income_tab(filtered_df)
        
        with tab5:
            render_investments_tab(filtered_df)