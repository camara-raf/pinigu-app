import pandas as pd

def calculate_chart_ranges(unique_months, n_bars_to_show=18):
    """
    Calculate fixed start/end ranges and slider ranges for charts.
    """
    if len(unique_months) == 0:
        return None, None, None, None
        
    # Ensure months are sorted
    sorted_months = sorted(unique_months)

    # Handle single month case specially to avoid huge bars
    if len(sorted_months) <= 1:
        target_month = sorted_months[0]
        base_dt = pd.to_datetime(target_month, format='%Y-%m')
        
        # Create a centered view: 1 month before to 1 month after
        # This gives context and prevents the single bar from filling the entire width
        fixed_start_range = base_dt - pd.DateOffset(months=1)
        fixed_start_range = fixed_start_range - pd.DateOffset(hours=1) # minor buffer
        
        fixed_end_range = base_dt + pd.DateOffset(months=2) # 1 month for bar + 1 month after
        
        # For slider, just use the same range or slightly wider if you prefer
        return fixed_start_range, fixed_end_range, fixed_start_range, fixed_end_range

    # Get the subset to show initially
    last_n = sorted_months[-n_bars_to_show:]
    start_range = last_n[0]
    end_range = last_n[-1]
    
    # Calculate fixed range (initial view)
    start_dt = pd.to_datetime(start_range, format='%Y-%m')
    end_dt = pd.to_datetime(end_range, format='%Y-%m')
    fixed_start_range = start_dt - pd.DateOffset(hours=1)
    fixed_end_range = end_dt + pd.DateOffset(months=1)
    
    # Calculate slider range (full data)
    slider_start_dt = pd.to_datetime(sorted_months[0], format='%Y-%m') - pd.DateOffset(hours=1)
    slider_end_dt = pd.to_datetime(sorted_months[-1], format='%Y-%m') + pd.DateOffset(months=1)
    
    return fixed_start_range, fixed_end_range, slider_start_dt, slider_end_dt

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
