import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_financial_health_tab(filtered_df, consolidated_df):
    """
    Render the Financial Health tab content.
    
    Args:
        filtered_df: The dataframe that has already been filtered by all active filters.
        consolidated_df: The full dataframe (for broader context if needed, though filtered is usually sufficient).
    """
    col1, col2 = st.columns(2)
    
    # --- Data Preparation ---
    # Filter for expenses only for the 50/30/20 rule
    expenses_df = filtered_df[filtered_df['Type'] == 'Out'].copy()
    income_df = filtered_df[filtered_df['Category'] == 'Income'].copy()
    
    # Calculate Total Income (for the period)
    total_income = income_df['Amount'].sum()
    
    with col1:
        st.subheader("Runway Calculator")
        
        # Calculate Current Balance (using consolidated_df to get the absolute latest state across all accounts, 
        # or filtered_df if we want to respect filters. Let's use filtered_df to respect bank/account filters)
        # Note: 'Amount' in the filtered_df is transaction amount. To get Balance, we need the rolling sum logic or 
        # just sum everything if the history is complete. 
        # BETTER: Use the 'Rolling Sum' logic from monthly balance, but simplify here.
        # Actually, the user asked for "Total Cash Balance / Avg Monthly Expenses".
        
        # 1. Get Current Balance
        # We sum all transaction amounts in the filtered selection. 
        current_balance = filtered_df['Amount'].sum()
        
        # 2. Average Monthly Expenses (Last 3 Months)
        # Find the last 3 months in the data
        all_months = sorted(expenses_df['YearMonth'].unique(), reverse=True)
        last_3_months = all_months[:3]
        
        if last_3_months:
            l3m_expenses = expenses_df[expenses_df['YearMonth'].isin(last_3_months)]
            avg_monthly_expenses = l3m_expenses['Amount'].abs().sum() / len(last_3_months)
        else:
            avg_monthly_expenses = 0
            
        if avg_monthly_expenses > 0:
            runway_months = current_balance / avg_monthly_expenses
            st.metric(
                label="Projected Runway", 
                value=f"{runway_months:.1f} Months",
                help=f"Based on current balance ({current_balance:,.0f}) and avg expenses of last {len(last_3_months)} months ({avg_monthly_expenses:,.0f}/mo)"
            )
            
            # Gauge for visual
            fig_runway = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = runway_months,
                title = {'text': "Survival Months"},
                gauge = {
                    'axis': {'range': [None, 24]},
                    'bar': {'color': "#1a5f3f"},
                    'steps': [
                        {'range': [0, 3], 'color': "red"},
                        {'range': [3, 6], 'color': "orange"},
                        {'range': [6, 24], 'color': "lightgreen"}
                    ],
                }
            ))
            fig_runway.update_layout(height=300)
            st.plotly_chart(fig_runway, width='stretch')
        else:
            st.info("Not enough expense data to calculate runway.")

    with col2:
        st.subheader("50/30/20 Rule Analysis")
        
        if total_income > 0:
            # Calculate buckets
            # Needs: 'Necessity' == 'Need'
            needs_amt = expenses_df[expenses_df['Necessity'] == 'Need']['Amount'].abs().sum()
            
            # Wants: 'Necessity' == 'Want' (Currently hardcoded to 'Need', so this will be 0)
            wants_amt = expenses_df[expenses_df['Necessity'] == 'Want']['Amount'].abs().sum()
            
            # Savings: Income - Expenses (Needs + Wants)
            total_expenses = needs_amt + wants_amt
            savings_amt = total_income - total_expenses
            
            # Percentages
            needs_pct = (needs_amt / total_income) * 100
            wants_pct = (wants_amt / total_income) * 100
            savings_pct = (savings_amt / total_income) * 100
            
            # Chart
            labels = ['Needs (Target: 50%)', 'Wants (Target: 30%)', 'Savings (Target: 20%)']
            values = [needs_amt, wants_amt, savings_amt]
            colors = ['#FFA07A', '#ADD8E6', '#90EE90'] # Light Salmon, Light Blue, Light Green
            
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=.4)])
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, width='stretch')
            
            st.markdown(f"""
            *   **Needs:** {needs_pct:.1f}% ({needs_amt:,.0f})
            *   **Wants:** {wants_pct:.1f}% ({wants_amt:,.0f})
            *   **Savings:** {savings_pct:.1f}% ({savings_amt:,.0f})
            """)
        else:
            st.info("No income data in filter period to calculate ratios.")
