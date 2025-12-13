import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import read_bank_mapping, get_logger

logger = get_logger(__name__)

def render_dashboard_v2_tab():
    """Render the Dashboard tab (v2)."""
    st.header("📊 Dashboard v2", )
    
    consolidated_df = st.session_state.consolidated_df.copy()
    logger.info(f"Consolidated df shape: {consolidated_df.shape}")
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

            # First, get the global min and max YearMonth across all data
            all_months = pd.period_range(
                start=month_balance['YearMonth'].min(),
                end=month_balance['YearMonth'].max(),
                freq='M'
            ).astype(str).tolist()

            # Apply filters for Bank and Account to the calculation base
            if selected_banks:
                month_balance = month_balance[month_balance['Bank'].isin(selected_banks)]
            
            if selected_accounts:
                month_balance = month_balance[month_balance['Account'].isin(selected_accounts)]
            
            if selected_owners:
                month_balance = month_balance[month_balance['Owner'].isin(selected_owners)]
                
            month_balance = month_balance.sort_values('Transaction Date').reset_index(drop=True)

            # Calculate the sum per month/bank/account
            month_balance = month_balance.groupby(['YearMonth', 'Bank', 'Account'])['Amount'].sum().reset_index()
            month_balance = month_balance.sort_values(['Bank', 'Account', 'YearMonth'])
            
            # Fill YearMonth gaps for each Bank/Account pair
            
            # Create a complete date range for each Bank/Account pair
            filled_records = []
            for (bank, account), group in month_balance.groupby(['Bank', 'Account']):
                min_yearmonth = group['YearMonth'].min()
                # Create full month range, starting from the min_yearmonth of the current group
                full_index = pd.DataFrame({'YearMonth': [
                    m for m in all_months if m >= min_yearmonth
                ]})
                full_index['Bank'] = bank
                full_index['Account'] = account
                
                # Merge with existing data
                merged = full_index.merge(
                    group[['YearMonth', 'Amount']], 
                    on='YearMonth', 
                    how='left'
                )
                
                # Forward fill: replace NaN with 0
                merged['Amount'] = merged['Amount'].fillna(0)
                
                filled_records.append(merged)
            
            # Combine all Bank/Account pairs
            month_balance = pd.concat(filled_records, ignore_index=True)
            month_balance = month_balance.sort_values(['Bank', 'Account', 'YearMonth'])
            
            # Now aggregate by YearMonth only (sum across all Bank/Account pairs)
            month_balance = month_balance.groupby(['YearMonth'])['Amount'].sum().reset_index()
            month_balance = month_balance.sort_values('YearMonth')
            month_balance['Rolling Sum'] = month_balance['Amount'].cumsum()

            if selected_year != 'All':
                month_balance = month_balance[month_balance['YearMonth'].str.startswith(str(selected_year))]
        
            with tab1_col1:
                # Assign colors based on whether Amount is positive or negative
                bar_colors = ['#1a5f3f' if x >= 0 else '#8b0000' for x in month_balance['Amount']]
                
                # Create bar chart with conditional colors
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=month_balance['YearMonth'],
                        y=month_balance['Rolling Sum'],
                        text=month_balance['Rolling Sum'],
                        marker_color=bar_colors,
                        showlegend=False,
                        customdata=month_balance['Amount']
                    )
                ])
                
                fig_bar.update_layout(
                    title="Cumulative Balance",
                    height=400
                )
                fig_bar.update_traces(
                    texttemplate='%{text:,.0f}',
                    textposition='inside',
                    textfont_color='white',
                    textfont_size=12,
                    hovertemplate='<b>Balance:</b> %{y:,.0f}<br><b>Diff:</b> %{customdata:,.0f}<extra></extra>'
                )
                fig_bar.update_layout(
                    hovermode='x unified',
                    xaxis_title='',
                    yaxis_title='',
                    xaxis=dict(fixedrange=True)
                )

                # Determine last 14 months for initial view
                N_bars_to_show = 14
                unique_months = month_balance['YearMonth'].unique()
                last_14 = unique_months[-N_bars_to_show:]
                start_range = last_14[0]
                end_range = last_14[-1]
                start_dt = pd.to_datetime(start_range, format='%Y-%m')
                end_dt = pd.to_datetime(end_range, format='%Y-%m')
                fixed_start_range = start_dt - pd.DateOffset(hours=1)
                fixed_end_range = end_dt + pd.DateOffset(months=1)
                slider_start_dt = pd.to_datetime(unique_months[0], format='%Y-%m') - pd.DateOffset(hours=1)
                slider_end_dt = pd.to_datetime(unique_months[-1], format='%Y-%m') + pd.DateOffset(months=1)
                

                fig_bar.update_xaxes(
                    tickangle=90,
                    tickmode='linear',
                    dtick="M1",
                    range=[fixed_start_range, fixed_end_range],
                    rangeslider=dict(visible=True 
                                     ,thickness=0.05 
                                     ,range=[slider_start_dt, slider_end_dt]
                                     )
                )

                st.plotly_chart(fig_bar, width='stretch')
        
            with tab1_col2:
                st.subheader("Table")
                st.dataframe(month_balance, width='stretch', hide_index=True)
        
        with tab2:
            # Create editable dataframe
            display_cols = ['Transaction Date', 'Transaction', 'Bank', 'Account', 'Amount', 'Type', 'Category', 'Sub-Category']
            display_df = filtered_df[display_cols].copy()
            display_df['Transaction Date'] = display_df['Transaction Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, width='stretch', hide_index=True)
        
            st.info(f"📊 Showing {len(filtered_df)} transactions")