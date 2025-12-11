import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import read_bank_mapping


def render_dashboard_v2_tab():
    """Render the Dashboard tab (v2)."""
    st.header("📊 Dashboard v2", )
    
    consolidated_df = st.session_state.consolidated_df
    bank_mapping_df = read_bank_mapping()
    bank_mapping_df['Bank_Account_key'] = bank_mapping_df['Bank'] + ' ' + bank_mapping_df['Account']
    consolidated_df['Bank_Account_key'] = consolidated_df['Bank'] + ' ' + consolidated_df['Account']

    consolidated_df = pd.merge(consolidated_df, bank_mapping_df[['Bank_Account_key', 'Owner']], how='left', on='Bank_Account_key')
    consolidated_df = consolidated_df.drop(columns=['Bank_Account_key'])

    del bank_mapping_df
    
    # Create Year-Month column for sorting and display
    consolidated_df['YearMonth'] = consolidated_df['Transaction Date'].dt.to_period('M').astype(str)
    consolidated_df['Month_Name'] = consolidated_df['Transaction Date'].dt.strftime('%B')
    consolidated_df['Year'] = consolidated_df['Transaction Date'].dt.year
    
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
        
        # Helper function to compute available filter options based on other filter selections
        def get_available_options(base_df, filter_name, selected_filters):
            """
            Compute available options for a filter based on current selections in other filters.
            
            Args:
                base_df: The base dataframe to filter
                filter_name: The name of the filter column to get options for
                selected_filters: Dict of {filter_name: selected_values} for other filters
            
            Returns:
                Sorted list of unique available values
            """
            temp_df = base_df.copy()
            
            # Apply all other filter selections
            for fname, fvalues in selected_filters.items():
                if fname != filter_name and fvalues:
                    temp_df = temp_df[temp_df[fname].isin(fvalues)]
            
            return sorted(temp_df[filter_name].dropna().unique().tolist())
        
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

        tab1, tab2 = st.tabs(["Monthly Balance", "Details"])

        with tab1:
            tab1_col1, tab1_col2 = st.columns(2)
            
            month_balance = consolidated_df.copy()
            # Apply filters for Bank and Account to the calculation base
            if selected_banks:
                month_balance = month_balance[month_balance['Bank'].isin(selected_banks)]
            
            if selected_accounts:
                month_balance = month_balance[month_balance['Account'].isin(selected_accounts)]
            
            if selected_owners:
                month_balance = month_balance[month_balance['Owner'].isin(selected_owners)]
                
            month_balance = month_balance.sort_values('Transaction Date').reset_index(drop=True)

            # Calculate the Rolling Sum / Cumulative Sum per month/bank/account
            month_balance = month_balance.groupby(['YearMonth'])['Amount'].sum().reset_index()
            month_balance = month_balance.sort_values('YearMonth')
            month_balance['Rolling Sum'] = month_balance['Amount'].cumsum()

        
            with tab1_col1:
                #st.subheader("📈 Monthly Balance Trend")                 
                view_balance = month_balance.copy()
                if selected_year != 'All':
                    view_balance = view_balance[view_balance['YearMonth'].str.startswith(str(selected_year))]
                
                fig_line = px.line(
                    view_balance,
                    x='YearMonth',
                    y='Rolling Sum',
                    title="Cumulative Balance",
                    markers=True,
                    height=400
                )
                fig_line.update_layout(hovermode='x unified')
                st.plotly_chart(fig_line, width='stretch')
        
            with tab1_col2:
                st.subheader("📋 to come")
        
        with tab2:
            # Create editable dataframe
            display_cols = ['Transaction Date', 'Transaction', 'Bank', 'Account', 'Amount', 'Type', 'Category', 'Sub-Category']
            display_df = filtered_df[display_cols].copy()
            display_df['Transaction Date'] = display_df['Transaction Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, width='stretch', hide_index=True)
        
            st.info(f"📊 Showing {len(filtered_df)} transactions")