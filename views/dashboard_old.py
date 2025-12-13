import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render_dashboard_tab_old():
    """Render the Dashboard Old tab."""
    st.header("📊 Dashboard Old")
    
    consolidated_df = st.session_state.consolidated_df.copy()

    if consolidated_df.empty:
        st.info("📭 No transaction data available. Please upload files and reload data in the 'File Management' tab.")

    else:
        # Filters
        st.subheader("🔍 Filters")

        # Create Year-Month column for sorting and display
        consolidated_df['YearMonth'] = consolidated_df['Transaction Date'].dt.to_period('M').astype(str)
        consolidated_df['Month_Name'] = consolidated_df['Transaction Date'].dt.strftime('%B')
        consolidated_df['Year'] = consolidated_df['Transaction Date'].dt.year

        
        # 1. Date Filters
        col1, col2, col3 = st.columns(3)
        
        years = sorted(consolidated_df['Year'].unique().tolist(), reverse=True)
        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        with col1:
            selected_year = st.selectbox("Year", ['All'] + years, key="year_filter")
        
        with col2:
            # Filter months based on available data if needed, or keep static
            selected_month = st.selectbox("Month", months, key="month_filter")
            
        # 2. Categorical Filters
        col4, col5, col6, col7 = st.columns(4)
        
        with col4:
            banks = sorted(consolidated_df['Bank'].dropna().unique().tolist())
            selected_banks = st.multiselect("Bank", banks, default=[], key="bank_filter")
            
        with col5:
            # Filter accounts based on selected banks? For now, show all or filtered
            if selected_banks:
                accounts = sorted(consolidated_df[consolidated_df['Bank'].isin(selected_banks)]['Account'].dropna().unique().tolist())
            else:
                accounts = sorted(consolidated_df['Account'].dropna().unique().tolist())
            selected_accounts = st.multiselect("Account", accounts, default=[], key="account_filter")
            
        with col6:
            categories = sorted(consolidated_df['Category'].dropna().unique().tolist())
            selected_categories = st.multiselect("Category", categories, default=[], key="category_filter")
            
        with col7:
            if selected_categories:
                sub_categories = sorted(consolidated_df[consolidated_df['Category'].isin(selected_categories)]['Sub-Category'].dropna().unique().tolist())
            else:
                sub_categories = sorted(consolidated_df['Sub-Category'].dropna().unique().tolist())
            selected_sub_categories = st.multiselect("Sub-Category", sub_categories, default=[], key="subcategory_filter")        

        
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
        
        st.divider()
        
        # Data table
        st.subheader("📋 Transactions Table")
        
        # Create editable dataframe
        display_cols = ['Transaction Date', 'Transaction', 'Bank', 'Account', 'Amount', 'Type', 'Category', 'Sub-Category']
        display_df = filtered_df[display_cols].copy()
        display_df['Transaction Date'] = display_df['Transaction Date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        st.divider()
        
        # Visualizations
        col1, col2 = st.columns(2)
      
        with col1:
            st.subheader("💰 Monthly Cash Flow")
            # Prepare data for Cash Flow
            cash_flow_df = filtered_df[filtered_df['Type'].isin(['In', 'Out'])].copy()
            if not cash_flow_df.empty:
                # Group by YearMonth to ensure chronological order and separation of years
                cash_flow_monthly = cash_flow_df.groupby(['YearMonth', 'Type'])['Amount'].sum().reset_index()
                cash_flow_monthly['Amount'] = cash_flow_monthly['Amount'].abs()
                
                # Sort by YearMonth
                cash_flow_monthly = cash_flow_monthly.sort_values('YearMonth')
                
                fig_cash = px.bar(
                    cash_flow_monthly,
                    x='YearMonth',
                    y='Amount',
                    color='Type',
                    barmode='group',
                    title="Income vs Expenses",
                    color_discrete_map={'In': '#28a745', 'Out': '#dc3545'},
                    height=400
                )
                fig_cash.update_layout(hovermode='x unified')
                st.plotly_chart(fig_cash, width='stretch')
            else:
                st.info("No data for Cash Flow")

        with col2:
            st.subheader("📊 Monthly Spending by Category")
            
            # Exclude income category
            spending_df = filtered_df[filtered_df['Type'] == 'Out'].copy()
            
            if not spending_df.empty:
                # Group by YearMonth and category
                spending_by_month = spending_df.groupby(['YearMonth', 'Category'])['Amount'].sum().reset_index()
                spending_by_month['Amount'] = spending_by_month['Amount'].abs()
                spending_by_month = spending_by_month.sort_values('YearMonth')
                
                fig_bar = px.bar(
                    spending_by_month,
                    x='YearMonth',
                    y='Amount',
                    color='Category',
                    title="Spending by Category",
                    height=400
                )
                fig_bar.update_layout(hovermode='x unified')
                st.plotly_chart(fig_bar, width='stretch')
            else:
                st.info("No expense data to display")
     
        st.divider()
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📈 Monthly Balance Trend")     
            #Exclude None Transactions
            month_balance = consolidated_df[consolidated_df['Type'] != 'None'].copy()
            
            # Apply filters for Bank and Account to the calculation base
            if selected_banks:
                month_balance = month_balance[month_balance['Bank'].isin(selected_banks)]
            
            if selected_accounts:
                month_balance = month_balance[month_balance['Account'].isin(selected_accounts)]
                
            month_balance = month_balance.sort_values('Transaction Date').reset_index(drop=True)

            # Group by YearMonth and sum amount
            month_balance = month_balance.groupby(['YearMonth'])['Amount'].sum().reset_index()
            month_balance = month_balance.sort_values('YearMonth')
            
            month_balance['Rolling Sum'] = month_balance['Amount'].cumsum()
            
            # Apply date filters to the VIEW only, not the calculation (to keep rolling sum correct)
            # But wait, if we filter by year, we might want to see the balance trend for that year only?
            # Usually balance is cumulative from the beginning. 
            # Let's filter the display df based on selected year/month if needed, 
            # but usually a trend line is best viewed over time.
            # If the user selected a specific year, we filter the view.
            
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

        with col4:
            st.subheader("💸 Top Expenses")
            top_expenses = filtered_df[filtered_df['Type'] == 'Out'].sort_values('Amount', ascending=True).head(10)
            if not top_expenses.empty:
                display_top = top_expenses[['Transaction Date', 'Transaction', 'Amount', 'Category']].copy()
                display_top['Transaction Date'] = display_top['Transaction Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_top, width='stretch', hide_index=True)
            else:
                st.info("No expenses found")


        st.divider()
        
        # Summary statistics
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)

   
        total_in = filtered_df[filtered_df['Type'] == 'In']['Amount'].sum()
        total_out = filtered_df[filtered_df['Type'] == 'Out']['Amount'].sum()
        net_balance = total_in + total_out
        avg_transaction = filtered_df['Amount'].mean()
     
        with col1:
            st.metric("Total Income", f"${total_in:,.2f}", delta=None, delta_color="normal")
        
        with col2:
            st.metric("Total Expenses", f"${total_out:,.2f}", delta=None, delta_color="normal")
        
        with col3:
            st.metric("Net Balance", f"${net_balance:,.2f}", delta=None, 
                     delta_color="normal" if net_balance >= 0 else "inverse")
        
        with col4:
            st.metric("Avg Transaction", f"${avg_transaction:,.2f}", delta=None, delta_color="normal")
