import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_filters(df):
    """Render filters in the sidebar and return filtered dataframe."""
    st.sidebar.header("🔍 Dashboard Filters")
    
    # Create Year-Month column for sorting and display
    df['YearMonth'] = df['Transaction Date'].dt.to_period('M').astype(str)
    df['Month_Name'] = df['Transaction Date'].dt.strftime('%B')
    df['Year'] = df['Transaction Date'].dt.year
    
    # 1. Date Filters
    years = sorted(df['Year'].unique().tolist(), reverse=True)
    months = ['All', 'January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    selected_year = st.sidebar.selectbox("Year", ['All'] + years, key="dash_year_filter")
    selected_month = st.sidebar.selectbox("Month", months, key="dash_month_filter")
        
    # 2. Categorical Filters
    banks = sorted(df['Bank'].dropna().unique().tolist())
    selected_banks = st.sidebar.multiselect("Bank", banks, default=[], key="dash_bank_filter")
    
    # Filter accounts based on selected banks
    if selected_banks:
        accounts = sorted(df[df['Bank'].isin(selected_banks)]['Account'].dropna().unique().tolist())
    else:
        accounts = sorted(df['Account'].dropna().unique().tolist())
    selected_accounts = st.sidebar.multiselect("Account", accounts, default=[], key="dash_account_filter")
        
    categories = sorted(df['Category'].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect("Category", categories, default=[], key="dash_category_filter")
        
    if selected_categories:
        sub_categories = sorted(df[df['Category'].isin(selected_categories)]['Sub-Category'].dropna().unique().tolist())
    else:
        sub_categories = sorted(df['Sub-Category'].dropna().unique().tolist())
    selected_sub_categories = st.sidebar.multiselect("Sub-Category", sub_categories, default=[], key="dash_subcategory_filter")
    
    # Apply filters
    filtered_df = df.copy()
    
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
        
    return filtered_df

def render_expenses_analysis(df):
    """1) Expenses Analysis: Show The breakdown by categories, the top expenses"""
    st.subheader("💸 Expenses Analysis")
    
    expenses_df = df[df['Type'] == 'Out'].copy()
    
    if expenses_df.empty:
        st.info("No expense data available for the selected filters.")
        return

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("##### Breakdown by Category")
        # Group by Category
        cat_expenses = expenses_df.groupby('Category')['Amount'].sum().reset_index()
        cat_expenses = cat_expenses.sort_values('Amount', ascending=False)
        
        fig = px.bar(
            cat_expenses,
            x='Category',
            y='Amount',
            color='Category',
            text_auto='.2s',
            title="Expenses by Category"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
        
    with col2:
        st.markdown("##### Top Expenses")
        top_expenses = expenses_df.sort_values('Amount', ascending=False).head(10)
        
        display_top = top_expenses[['Transaction Date', 'Transaction', 'Amount']].copy()
        display_top['Transaction Date'] = display_top['Transaction Date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_top, 
            width='stretch', 
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="$%.2f")
            }
        )

def render_balance_analysis(df):
    """2) Balance Analysis: Show the Cumulative amount, and the net balance per month"""
    st.subheader("⚖️ Balance Analysis")
    
    if df.empty:
        st.info("No data available.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Net Balance per Month")
        # Net balance = In - Out
        # We need to group by Month and Type
        monthly_net = df.groupby(['YearMonth', 'Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
        
        if 'In' not in monthly_net.columns: monthly_net['In'] = 0
        if 'Out' not in monthly_net.columns: monthly_net['Out'] = 0
        
        monthly_net['Net Balance'] = monthly_net['In'] - monthly_net['Out']
        monthly_net = monthly_net.sort_values('YearMonth')
        
        fig_net = px.bar(
            monthly_net,
            x='YearMonth',
            y='Net Balance',
            color='Net Balance',
            title="Net Balance (Income - Expenses)",
            color_continuous_scale=px.colors.diverging.RdYlGn
        )
        st.plotly_chart(fig_net, width='stretch')

    with col2:
        st.markdown("##### Cumulative Balance Trend")
        # For cumulative balance, we ideally want the running total of all time, 
        # but filtered by the view. 
        # If we just sum the filtered rows, it might start from 0 which is misleading if the account had previous balance.
        # However, without a starting balance input, we can only show the trend of the *transactions*.
        # Let's show the cumulative sum of the filtered transactions for now.
        
        # Sort by date
        trend_df = df.sort_values('Transaction Date').copy()
        
        # Adjust signs: In is positive, Out is negative
        trend_df['Signed Amount'] = trend_df.apply(lambda x: x['Amount'] if x['Type'] == 'In' else -x['Amount'], axis=1)
        trend_df['Cumulative Balance'] = trend_df['Signed Amount'].cumsum()
        
        fig_line = px.line(
            trend_df,
            x='Transaction Date',
            y='Cumulative Balance',
            title="Cumulative Balance (Selected Transactions)",
        )
        st.plotly_chart(fig_line, width='stretch')

def render_detailed_rows(df):
    """3) Detailed rows: Shows a table with all the transactions based on the selected filters."""
    st.subheader("📋 Detailed Transactions")
    
    if df.empty:
        st.info("No transactions found.")
        return
        
    # Calculate Total
    total_in = df[df['Type'] == 'In']['Amount'].sum()
    total_out = df[df['Type'] == 'Out']['Amount'].sum()
    net_total = total_in - total_out
    
    st.markdown(f"**Total Income:** `${total_in:,.2f}` | **Total Expenses:** `${total_out:,.2f}` | **Net:** `${net_total:,.2f}`")

    display_cols = ['Transaction Date', 'Transaction', 'Bank', 'Account', 'Amount', 'Type', 'Category', 'Sub-Category']
    display_df = df[display_cols].copy()
    display_df['Transaction Date'] = display_df['Transaction Date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df, 
        width='stretch', 
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%.2f")
        }
    )

def render_accounts_summary(df):
    """4) Accounts Summary: A break-down of what is available in each account"""
    st.subheader("🏦 Accounts Summary")
    
    if df.empty:
        st.info("No data available.")
        return

    # Current available in each account (based on filtered data)
    # Note: This is just the sum of transactions in the filtered view. 
    # Real account balance would need a starting point. 
    # Assuming 'Amount' is absolute, we need to sign it.
    
    df['Signed Amount'] = df.apply(lambda x: x['Amount'] if x['Type'] == 'In' else -x['Amount'], axis=1)
    
    account_summary = df.groupby(['Bank', 'Account'])['Signed Amount'].sum().reset_index()
    account_summary.rename(columns={'Signed Amount': 'Net Change'}, inplace=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Net Change per Account (Selected Period)")
        st.dataframe(
            account_summary, 
            width='stretch', 
            hide_index=True,
            column_config={
                "Net Change": st.column_config.NumberColumn(format="$%.2f")
            }
        )
        
    with col2:
        st.markdown("##### Distribution by Bank")
        bank_summary = df.groupby('Bank')['Signed Amount'].sum().reset_index()
        # Only show positive balances for the pie chart or handle negatives?
        # Pie charts don't like negatives. Let's show absolute volume of activity or just positive net changes?
        # User asked: "how much each bank/account represents from the total amount available"
        # Since we don't have absolute total available, let's show the breakdown of Income (In) by Bank
        # Or we can show the breakdown of the Net Change if positive.
        
        # Let's try showing the breakdown of 'In' transactions (Money flowing in)
        # and 'Out' transactions (Money flowing out)
        
        sub_col_a, sub_col_b = st.columns(2)
        with sub_col_a:
            in_by_bank = df[df['Type'] == 'In'].groupby('Bank')['Amount'].sum().reset_index()
            if not in_by_bank.empty:
                fig_in = px.pie(in_by_bank, values='Amount', names='Bank', title="Income by Bank")
                st.plotly_chart(fig_in, width='stretch')
        
        with sub_col_b:
            out_by_bank = df[df['Type'] == 'Out'].groupby('Bank')['Amount'].sum().reset_index()
            if not out_by_bank.empty:
                fig_out = px.pie(out_by_bank, values='Amount', names='Bank', title="Expenses by Bank")
                st.plotly_chart(fig_out, width='stretch')


def render_dashboard_tab():
    """Render the Dashboard tab."""
    st.header("📊 Dashboard")
    
    consolidated_df = st.session_state.consolidated_df
    
    if consolidated_df.empty:
        st.info("📭 No transaction data available. Please upload files and reload data in the 'File Management' tab.")
        return

    # Render Filters (Sidebar)
    filtered_df = render_filters(consolidated_df)
    
    # Render Sections
    st.divider()
    render_expenses_analysis(filtered_df)
    
    st.divider()
    render_balance_analysis(filtered_df)
    
    st.divider()
    render_detailed_rows(filtered_df)
    
    st.divider()
    render_accounts_summary(filtered_df)
