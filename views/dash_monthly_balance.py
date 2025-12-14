import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from views.dash_utils import calculate_chart_ranges

def render_monthly_balance_tab(consolidated_df, selected_year, selected_owners, selected_banks, selected_accounts):
    """
    Render the Monthly Balance tab content.
    
    Args:
        consolidated_df: The full consolidated dataframe (unfiltered by main filters).
        selected_year: The selected year from the main filter.
        selected_owners: List of selected owners.
        selected_banks: List of selected banks.
        selected_accounts: List of selected accounts.
    """
    tab1_col1, tab1_col2 = st.columns([7, 3])
    
    month_balance = consolidated_df.copy()

    # First, get the global min and max YearMonth across all data
    if month_balance.empty: # Handle empty dataframe case
         st.info("No data available for balance calculation.")
         return

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
    if filled_records:
        month_balance = pd.concat(filled_records, ignore_index=True)
        month_balance = month_balance.sort_values(['Bank', 'Account', 'YearMonth'])
        
        # Now aggregate by YearMonth only (sum across all Bank/Account pairs)
        month_balance = month_balance.groupby(['YearMonth'])['Amount'].sum().reset_index()
        month_balance = month_balance.sort_values('YearMonth')
        month_balance['Rolling Sum'] = month_balance['Amount'].cumsum()

        if selected_year != 'All':
            month_balance = month_balance[month_balance['YearMonth'].str.startswith(str(selected_year))]
    else:
        # Fallback for empty after filtering
         month_balance = pd.DataFrame(columns=['YearMonth', 'Amount', 'Rolling Sum'])

    with tab1_col1:
        if not month_balance.empty:
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

            # Determine last 14 months for initial view using helper function
            fixed_start, fixed_end, slider_start, slider_end = calculate_chart_ranges(
                month_balance['YearMonth'].unique()
            )

            if fixed_start:
                fig_bar.update_xaxes(
                    tickangle=90,
                    tickmode='linear',
                    dtick="M1",
                    range=[fixed_start, fixed_end],
                    rangeslider=dict(visible=True 
                                        ,thickness=0.05 
                                        ,range=[slider_start, slider_end]
                                        )
                )

            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No balance data to display for the selected criteria.")

    with tab1_col2:
        st.subheader("Table")
        
        if not month_balance.empty:
            # Create a display dataframe with visual indicator
            display_month_balance = month_balance.sort_values(by=month_balance.columns[0], ascending=False).copy()
            
            # Round numeric columns to 2 decimal places
            display_month_balance['Amount'] = display_month_balance['Amount'].round(2)
            display_month_balance['Rolling Sum'] = display_month_balance['Rolling Sum'].round(2)
            
            # Add visual indicator column
            display_month_balance.insert(1, '📊', display_month_balance['Amount'].apply(
                lambda x: '🟢' if x >= 0 else '🔴'
            ))
            
            # Configure columns for better display
            st.dataframe(
                display_month_balance,
                column_config={
                    'YearMonth': st.column_config.TextColumn('Month', width=50),
                    '📊': st.column_config.TextColumn('', width=10),
                    'Amount': st.column_config.NumberColumn('Amount', format="%.2f", width=60),
                    'Rolling Sum': st.column_config.NumberColumn('Balance', format="%.2f", width=60)
                },
                width='stretch',
                hide_index=True
            )
        else:
             st.info("No data.")
