import streamlit as st
import pandas as pd
import re
from utils import (
    load_mapping_rules, load_consolidated_data, 
    get_category_subcategory_combinations, get_subcategories_for_category,
    get_direction_for_subcategory, add_mapping_rule, match_pattern
)


def extract_distinct_uncategorized_transactions():
    """Extract all distinct transaction values where category == 'Uncategorized'."""
    logger.info("Extracting distinct uncategorized transactions...")
    df = load_consolidated_data()
    
    if df.empty:
        return pd.DataFrame(columns=['transaction'])
    
    uncategorized = df[df['Category'] == 'Uncategorized'].copy()
    
    if uncategorized.empty:
        return pd.DataFrame(columns=['transaction'])
    
    # Get distinct transactions
    distinct_tx = uncategorized['Transaction'].drop_duplicates().reset_index(drop=True)
    result = pd.DataFrame({'transaction': distinct_tx})
    
    return result


def validate_pattern(pattern_str):
    """
    Validate if pattern can compile as regex.
    Returns True if valid, False otherwise.
    """
    if not pattern_str:
        return False
    
    try:
        regex_pattern = re.escape(pattern_str).replace(r'\*', '.*')
        re.compile(regex_pattern)
        return True
    except Exception:
        return False


def compute_pattern_pass(pattern_str):
    """
    Compute pattern_pass value as 'True' or 'False' string.
    This determines if the pattern is valid for rule creation.
    """
    if validate_pattern(pattern_str):
        return "True"
    else:
        return "False"


def initialize_bulk_rules_df():
    """Initialize or return existing bulk_rules_df from session state."""
    if 'bulk_rules_df' not in st.session_state:
        # Create initial dataframe with uncategorized transactions
        distinct_tx = extract_distinct_uncategorized_transactions()
        
        if distinct_tx.empty:
            # Create empty structure
            st.session_state.bulk_rules_df = pd.DataFrame(columns=[
                'transaction', 'pattern', 'pattern_pass', 'category', 'sub_category'
            ])
        else:
            # Initialize with transactions
            st.session_state.bulk_rules_df = pd.DataFrame({
                'transaction': distinct_tx['transaction'],
                'pattern': '',  # User editable
                'pattern_pass': 'False',  # Auto-computed
                'category': '',  # User editable
                'sub_category': ''  # User editable
            })
    
    return st.session_state.bulk_rules_df


def update_pattern_pass_column():
    """Update pattern_pass column based on pattern column values."""
    df = st.session_state.bulk_rules_df
    
    for idx, row in df.iterrows():
        pattern = row['pattern']
        df.at[idx, 'pattern_pass'] = compute_pattern_pass(pattern)
    
    st.session_state.bulk_rules_df = df


def render_bulk_mapping_tab():
    """Render the Bulk Category Mapping tab."""
    st.header("⚙️ Bulk Category Mapping")
    
    st.info(
        "💡 **How to use:**\n"
        "1. Edit the 'pattern' column for each transaction (use `*` as wildcard)\n"
        "2. Select a 'category' from the dropdown\n"
        "3. The 'sub-category' options will update based on your category selection\n"
        "4. The 'pattern_pass' column shows if your pattern is valid\n"
        "5. Click 'Save New Mapping Rules' to create all rules where both pattern and category are filled"
    )
    
    st.divider()
    
    # Initialize dataframe
    bulk_rules_df = initialize_bulk_rules_df()
    
    if bulk_rules_df.empty:
        st.warning("✅ No uncategorized transactions found. All transactions are categorized!")
        return
    
    st.subheader("📊 Uncategorized Transactions")
    
    # Build a mapping of categories to subcategories
    hierarchy = get_category_subcategory_combinations()

    # Get all available categories and subcategories for dropdowns
    all_categories = list(hierarchy.keys())
    
    # Build dynamic row-level options for subcategories
    subcat_options_per_row = {}

    for idx, row in bulk_rules_df.iterrows():
        cat = row.get("category", "")

        if cat in hierarchy:
            subcats = [item["sub_category"] for item in hierarchy[cat]]
        else:
            subcats = []

        subcat_options_per_row[idx] = subcats

    
    # Create column configuration for the data_editor
    column_config = {
        'transaction': st.column_config.TextColumn(
            label="Transaction",
            disabled=True,
            width="large"
        ),
        'pattern': st.column_config.TextColumn(
            label="Pattern (editable)",
            #placeholder="e.g., *grocery* or *amazon*",
            width="medium"
        ),
        'pattern_pass': st.column_config.TextColumn(
            label="Pattern Valid",
            disabled=True,
            width="small"
        ),
        'category': st.column_config.SelectboxColumn(
            label="Category (editable)",
            options=all_categories if all_categories else [""],
            width="medium"
        ),
        "sub_category": st.column_config.SelectboxColumn(
            "Sub-Category",
            options=subcat_options_per_row,  # <-- Dynamic per-row options!
            width="medium",
        ),
    }
    
    # Render the data editor
    edited_df = st.data_editor(
        bulk_rules_df,
        column_config=column_config,
        width='stretch',
        hide_index=False,
        key="bulk_rules_editor",
        num_rows="fixed"
    )
    
    # Update session state with edited data
    st.session_state.bulk_rules_df = edited_df
    
    # Update pattern_pass column based on pattern changes
    update_pattern_pass_column()
    
    st.divider()
    
    # Save button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save New Mapping Rules", type="primary", width='stretch'):
            save_bulk_mapping_rules()
    
    with col2:
        if st.button("🔄 Reset", type="secondary", width='stretch'):
            if 'bulk_rules_df' in st.session_state:
                del st.session_state.bulk_rules_df
            st.rerun()
    
    # Show preview of rules to be saved
    st.subheader("📋 Rules Preview")
    
    df = st.session_state.bulk_rules_df
    
    # Filter rows that will be saved
    valid_rules = df[
        (df['pattern'].notna()) & 
        (df['pattern'] != '') & 
        (df['category'].notna()) & 
        (df['category'] != '') & 
        (df['pattern_pass'] == 'True')
    ].copy()
    
    if valid_rules.empty:
        st.info("No valid rules to save. Fill in pattern and category columns for at least one row.")
    else:
        st.success(f"✅ Ready to save {len(valid_rules)} rule(s)")
        
        # Show preview table
        preview_df = valid_rules[['transaction', 'pattern', 'category', 'sub_category']].copy()
        preview_df.columns = ['Transaction', 'Pattern', 'Category', 'Sub-Category']
        
        st.dataframe(preview_df, width='stretch', hide_index=True)


def save_bulk_mapping_rules():
    """
    Save bulk mapping rules to mapping_rules.csv.
    Only saves rows where pattern and category are not empty AND pattern_pass is 'True'.
    """
    df = st.session_state.bulk_rules_df
    
    # Filter valid rules
    valid_rules = df[
        (df['pattern'].notna()) & 
        (df['pattern'] != '') & 
        (df['category'].notna()) & 
        (df['category'] != '') & 
        (df['pattern_pass'] == 'True')
    ].copy()
    
    if valid_rules.empty:
        st.error("❌ No valid rules to save. Ensure pattern and category are filled for at least one row.")
        return
    
    saved_count = 0
    errors = []
    
    # Load existing rules to get current max Rule_ID and Priority
    existing_rules = load_mapping_rules()
    
    for idx, row in valid_rules.iterrows():
        try:
            pattern = row['pattern'].strip()
            category = row['category'].strip()
            sub_category = row['sub_category'].strip() if row['sub_category'] else ''
            
            # Determine direction from sub_category if available
            direction = 'None'
            if category and sub_category:
                direction = get_direction_for_subcategory(category, sub_category)
                if direction is None:
                    direction = 'None'
            
            # Use existing add_mapping_rule function
            add_mapping_rule(pattern, category, sub_category, direction)
            saved_count += 1
            
        except ValueError as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
        except Exception as e:
            errors.append(f"Row {idx + 1}: Unexpected error - {str(e)}")
    
    # Display results
    if errors:
        st.warning(f"⚠️ Saved {saved_count} rule(s) with {len(errors)} error(s):")
        for error in errors:
            st.caption(f"❌ {error}")
    
    if saved_count > 0:
        st.success(f"✅ Successfully saved {saved_count} new mapping rule(s)!")
        st.session_state.data_refresh_needed = True
        
        # Reset the dataframe
        if 'bulk_rules_df' in st.session_state:
            del st.session_state.bulk_rules_df
        
        st.rerun()
