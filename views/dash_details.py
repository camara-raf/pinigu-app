import streamlit as st

def render_details_tab(filtered_df):
    """
    Render the Details tab content.
    
    Args:
        filtered_df: The dataframe that has already been filtered by all active filters.
    """
    # Create editable dataframe
    display_cols = ['Transaction Date', 'Transaction', 'Bank', 'Account', 'Amount', 'Type', 'Category', 'Sub-Category']
    
    # Ensure all columns exist, just in case
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    
    display_df = filtered_df[available_cols].copy()
    if 'Transaction Date' in display_df.columns:
        display_df['Transaction Date'] = display_df['Transaction Date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(display_df, width='stretch', hide_index=True)

    st.info(f"📊 Showing {len(filtered_df)} transactions")
