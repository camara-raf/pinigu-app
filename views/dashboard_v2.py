import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_dashboard_v2_tab():
    """Render the Dashboard tab (v2)."""
    st.header("📊 Dashboard v2", )
    
    consolidated_df = st.session_state.consolidated_df
    
    if consolidated_df.empty:
        st.info("📭 No transaction data available. Please upload files and reload data in the 'File Management' tab.")
    else:
        # Filters
        #st.subheader("🔍 Filters")
        
        # Filter columns
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        # Create Year-Month column for sorting and display
        consolidated_df['YearMonth'] = consolidated_df['Transaction Date'].dt.to_period('M').astype(str)
        consolidated_df['Month_Name'] = consolidated_df['Transaction Date'].dt.strftime('%B')
        consolidated_df['Year'] = consolidated_df['Transaction Date'].dt.year
        
        years = sorted(consolidated_df['Year'].unique().tolist(), reverse=True)
        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        with col1:
            selected_year = st.selectbox("Year", ['All'] + years, key="year_filter_v1")
        
        with col2:
            selected_month = st.selectbox("Month", months, key="month_filter_v1")
            
        with col3:
            banks = sorted(consolidated_df['Bank'].dropna().unique().tolist())
            selected_banks = st.multiselect("Bank", banks, default=[], key="bank_filter_v1")
            
        with col4:
            if selected_banks:
                accounts = sorted(consolidated_df[consolidated_df['Bank'].isin(selected_banks)]['Account'].dropna().unique().tolist())
            else:
                accounts = sorted(consolidated_df['Account'].dropna().unique().tolist())
            selected_accounts = st.multiselect("Account", accounts, default=[], key="account_filter_v1")
            
        with col5:
            categories = sorted(consolidated_df['Category'].dropna().unique().tolist())
            selected_categories = st.multiselect("Category", categories, default=[], key="category_filter_v1")
            
        with col6:
            if selected_categories:
                sub_categories = sorted(consolidated_df[consolidated_df['Category'].isin(selected_categories)]['Sub-Category'].dropna().unique().tolist())
            else:
                sub_categories = sorted(consolidated_df['Sub-Category'].dropna().unique().tolist())
            selected_sub_categories = st.multiselect("Sub-Category", sub_categories, default=[], key="subcategory_filter_v1")
        
        # Apply filters
        filtered_df = consolidated_df.copy()
        
        if selected_year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == int(selected_year)]
        
        if selected_month != 'All':
            month_num = months.index(selected_month)
            filtered_df = filtered_df[filtered_df['Transaction Date'].dt.month == month_num]
            
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