import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from views.dash_utils import calculate_chart_ranges

def render_expenses_tab(filtered_df):
    """
    Render the Expenses tab content.
    
    Args:
        filtered_df: The dataframe that has already been filtered by all active filters.
    """
    col1, col2 = st.columns([6, 4])
    
    # Show only expenses
    spending_df = filtered_df[filtered_df['Type'] == 'Out'].copy()
    
    with col1:
        #st.subheader("📊 Monthly Spending by Category")
        if not spending_df.empty:
            # Group by YearMonth and category
            spending_by_month = spending_df.groupby(['YearMonth', 'Category'])['Amount'].sum().reset_index()
            spending_by_month['Amount'] = spending_by_month['Amount'].abs()
            spending_by_month = spending_by_month.sort_values('YearMonth')
            
            fig_bar = go.Figure()
            
            for category in spending_by_month['Category'].unique():
                cat_data = spending_by_month[spending_by_month['Category'] == category]
                fig_bar.add_trace(go.Bar(
                    name=category,
                    x=cat_data['YearMonth'],
                    y=cat_data['Amount'],
                    text=cat_data['Amount'],
                    texttemplate='%{text:.2s}',
                    textposition='inside'
                ))

            # Calculate totals for annotations (unused in chart directly but good for context)
            # monthly_totals = spending_by_month.groupby('YearMonth')['Amount'].sum().reset_index()
            
            fig_bar.update_layout(
                title="Spending by Category",
                height=550,
                showlegend=True # Ensure legend is always shown
            )

            # Determine last 14 months for initial view using helper function
            fixed_start, fixed_end, slider_start, slider_end = calculate_chart_ranges(
                spending_by_month['YearMonth'].unique()
            )

            if fixed_start:
                fig_bar.update_xaxes(
                    tickangle=90,
                    tickmode='linear',
                    dtick="M1",
                    range=[fixed_start, fixed_end],
                    rangeslider=dict(
                        visible=True,
                        thickness=0.05,
                        range=[slider_start, slider_end]
                    )
                )
            fig_bar.update_layout(hovermode='x unified', barmode='stack')
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No expense data to display")
    with col2:
        st.subheader("💸 Top Expenses")
        top_expenses = spending_df.sort_values('Amount', ascending=True).head(10)
        if not top_expenses.empty:
            display_top = top_expenses[['Transaction Date', 'Transaction', 'Amount', 'Category']].copy()
            display_top['Transaction Date'] = display_top['Transaction Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                display_top,
                width='stretch',
                hide_index=True,
                column_config={
                    "Transaction Date": st.column_config.Column(width="small"),
                    "Transaction": st.column_config.Column(width="medium"),
                    "Amount": st.column_config.Column(width="small"),
                    "Category": st.column_config.Column(width="small")
                }
            )
        else:
            st.info("No expenses found")
