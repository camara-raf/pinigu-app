import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from views.dash_utils import calculate_chart_ranges

def render_income_tab(filtered_df):
    """
    Render the Income tab content.
    
    Args:
        filtered_df: The dataframe that has already been filtered by all active filters.
    """
    col1, col2 = st.columns([6, 4])
    income_df = filtered_df[filtered_df['Category'] == 'Income']
    
    if not income_df.empty:
        # Pivot the data: Index=YearMonth, Columns=Owner, Values=Amount
        income_pivot = income_df.pivot_table(
            index='YearMonth', 
            columns='Owner', 
            values='Amount', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Calculate Total Income across all owners for each month
        income_pivot['Total Income'] = income_pivot.sum(axis=1)
        
        # Sort by YearMonth descending
        income_pivot = income_pivot.sort_index(ascending=False)
        
        # Reset index to make YearMonth a column again
        income_pivot = income_pivot.reset_index()
        
        with col1:
            st.subheader("Income Summary by Month and Owner")
            
            # Dynamic column configuration for Owner columns
            column_config = {
                "YearMonth": st.column_config.TextColumn("Month"),
                "Total Income": st.column_config.NumberColumn("Total Income", format="%.2f"),
            }
            
            # Apply currency formatting to all other columns (Owners)
            for col in income_pivot.columns:
                if col not in ["YearMonth", "Total Income"]:
                    column_config[col] = st.column_config.NumberColumn(col, format="%.2f")

            st.dataframe(
                income_pivot, 
                column_config=column_config,
                use_container_width=True,
                hide_index=True
            )
    else:
        with col1:
             st.info("No income data found.")
    with col2:
        st.subheader("Financial Health")
        
        # Calculate monthly income
        monthly_income = income_df.groupby('YearMonth')['Amount'].sum().reset_index()
        monthly_income.rename(columns={'Amount': 'Income'}, inplace=True)
        
        # Calculate monthly expenses (Type == 'Out')
        # We start from filtered_df again to get expenses
        expenses_df = filtered_df[filtered_df['Type'] == 'Out']
        monthly_expenses = expenses_df.groupby('YearMonth')['Amount'].sum().abs().reset_index()
        monthly_expenses.rename(columns={'Amount': 'Expenses'}, inplace=True)
        
        # Merge
        health_df = pd.merge(monthly_income, monthly_expenses, on='YearMonth', how='outer').fillna(0)
        
        # Calculate coverage percentage
        # Avoid division by zero
        health_df['Coverage %'] = health_df.apply(
            lambda x: (x['Expenses'] / x['Income'] * 100) if x['Income'] != 0 else 0, axis=1
        )
        
        # Sort descending by month
        health_df = health_df.sort_values('YearMonth', ascending=False)
        
        st.dataframe(
            health_df,
            column_config={
                "YearMonth": st.column_config.TextColumn("Month"),
                "Income": st.column_config.NumberColumn("Income", format="%.2f"),
                "Expenses": st.column_config.NumberColumn("Expenses", format="%.2f"),
                "Coverage %": st.column_config.NumberColumn(
                    "Coverage %", 
                    format="%.1f%%",
                    help="Percentage of income used for expenses. >100% means expenses exceeded income."
                ),
            },
            use_container_width=True,
            hide_index=True
        )