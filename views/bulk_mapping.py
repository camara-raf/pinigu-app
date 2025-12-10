import streamlit as st
import pandas as pd
import re
from utils import (
    load_mapping_rules, 
    get_category_subcategory_combinations, get_subcategories_for_category,
    get_direction_for_subcategory, add_mapping_rule, match_pattern, get_flat_mapping_options,
    extract_distinct_uncategorized_transactions, apply_new_rules_list_to_consolidated_data #,validate_pattern
    ,get_logger
)

logger = get_logger(__name__)

def initialize_bulk_rules_df():
    """Initialize or return existing bulk_rules_df from session state."""
    if 'bulk_rules_df' not in st.session_state:
        # Create initial dataframe with uncategorized transactions
        # Use consolidated_df from session state if available to avoid reloading from disk/stale data
        source_df = st.session_state.get('consolidated_df')
        distinct_tx = extract_distinct_uncategorized_transactions(source_df)
        
        if distinct_tx.empty:
            # Create empty structure
            st.session_state.bulk_rules_df = pd.DataFrame(columns=[
                'transaction','count', 'max_date', 'avg_amount', 'pattern', 'pattern_pass', 'mapping'
            ])
        else:
            # Initialize with transactions
            st.session_state.bulk_rules_df = pd.DataFrame({
                'transaction': distinct_tx['transaction'],
                'count': distinct_tx['count'],
                'max_date': distinct_tx['max_date'],
                'avg_amount': distinct_tx['avg_amount'],
                'pattern': '',  # User editable
                'pattern_pass': 'False',  # Auto-computed,
                'mapping' : ''

            })
    
    return st.session_state.bulk_rules_df


def compute_pattern_pass_for_df(df):
    """Return a Series with pattern_pass values for each row in df."""
    def test_pattern(pat, txt):
        if pat is None:
            return ""
        pat = str(pat).strip()
        if pat == "":
            return ""
        try:
            return "True" if bool(re.search(pat, str(txt), flags=re.IGNORECASE)) else "False"
        except re.error:
            return "Invalid"

    return df.apply(lambda r: test_pattern(r.get("pattern", ""), r.get("transaction", "")), axis=1)

def run_pattern_tests(df):
    #df = st.session_state.bulk_rules_df.copy()

    for idx, row in df.iterrows():
        pattern = row.get("pattern", "").strip()
        transaction = row["transaction"]

        if pattern:
            try:
                # Convert wildcard pattern "*abc*" → regex ".*abc.*"
                regex = pattern.replace("*", ".*")
                is_match = bool(re.search(regex, transaction, re.IGNORECASE))
                df.at[idx, "pattern_pass"] = str(is_match)
            except:
                df.at[idx, "pattern_pass"] = "False"

    return df


def render_bulk_mapping_tab():
    st.header("⚙️ Bulk Category Mapping")

    st.info(
        "💡 **Instructions**\n"
        "1. Fill in the 'pattern' column where needed\n"
        "2. Select a mapping using the combined dropdown\n"
        "3. Click **Run Pattern Test** to validate all patterns\n"
        "4. Click **Save New Mapping Rules** to commit"
    )

    bulk_rules_df = initialize_bulk_rules_df()

    if bulk_rules_df.empty:
        st.success("🎉 All transactions are categorized!")
        return

    st.subheader("📊 Uncategorized Transactions")

    # Load hierarchy and build combined mapping strings
    #hierarchy = get_category_subcategory_combinations()
    flat_options = get_flat_mapping_options()

    # --------------------
    # Column Config
    # --------------------
    column_config = {
        "transaction": st.column_config.TextColumn("Transaction", disabled=True, width="large"),
        "count": st.column_config.NumberColumn("Count", disabled=True, width="small"),
        "max_date": st.column_config.DateColumn("Max Date", disabled=True, width="small"),
        "avg_amount": st.column_config.NumberColumn(
            "Avg Amount",
            disabled=True,
            width="small"
        ),
        "pattern": st.column_config.TextColumn("Pattern", width="medium"),
        "pattern_pass": st.column_config.TextColumn("Pattern Test", disabled=True, width="small"),
        "mapping": st.column_config.SelectboxColumn(
            "Select Mapping",
            options=flat_options,
            width="large",
        ),
    }

    # Add empty mapping column if not present
    if "mapping" not in bulk_rules_df.columns:
        bulk_rules_df["mapping"] = ""

    edited_df = st.data_editor(
        bulk_rules_df,
        key="bulk_rules_editor",
        column_config=column_config,
        width='stretch',
        hide_index=False,
        num_rows="fixed"
    )

    st.divider()
    
    # Save button
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save New Mapping Rules", type="primary", width="stretch"):
            # Save edited data to session state before processing
            st.session_state.bulk_rules_df = edited_df.copy()
            save_bulk_mapping_rules(edited_df)
    
    with col2:
        # --------------------
        # Pattern Test Button
        # --------------------
        if st.button("Run Pattern Test", type="secondary", width="stretch"):
            # Save edited data to session state
            st.session_state.bulk_rules_df = edited_df.copy()
            # Run pattern tests and update session state
            st.session_state.bulk_rules_df = run_pattern_tests(st.session_state.bulk_rules_df)
            st.rerun()

    with col3:
        if st.button("🔄 Reset", type="secondary", width="stretch"):
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
        (df['mapping'].notna()) & 
        (df['mapping'] != '') & 
        (df['pattern_pass'] == 'True')
    ].copy()
    
    if valid_rules.empty:
        st.info("No valid rules to save. Fill in pattern and mapping columns for at least one row.")
    else:
        st.success(f"✅ Ready to save {len(valid_rules)} rule(s)")
        
        # Show preview table
        preview_df = valid_rules[['transaction', 'pattern', 'mapping']].copy()
        preview_df.columns = ['Transaction', 'Pattern', 'Mapping']
        
        st.dataframe(preview_df, width='stretch', hide_index=True)


def save_bulk_mapping_rules(df):
    """
    Save bulk mapping rules to mapping_rules.csv.
    Only saves rows where pattern and mapping are not empty AND pattern_pass is 'True'.
    """
    logger.info("Saving bulk mapping rules...")
    
    # Filter valid rules
    valid_rules = df[
        (df['pattern'].notna()) & 
        (df['pattern'] != '') & 
        (df['mapping'].notna()) & 
        (df['mapping'] != '') & 
        (df['pattern_pass'] == 'True')
    ].copy()
    
    if valid_rules.empty:
        st.error("❌ No valid rules to save. Ensure pattern and mapping are filled for at least one row.")
        return
    
    saved_count = 0
    errors = []
    new_rules = []
       
    for idx, row in valid_rules.iterrows():
        try:
            pattern = row['pattern'].strip()
            mapping = row.get("mapping", "").strip()
            
            if not pattern or not mapping:
                continue
           
            # mapping looks like: "Home Spends -> Electricity (Out)"
            parts = mapping.split(" -> ")
            if len(parts) != 2:
                errors.append(f"Row {idx + 1}: Invalid mapping format '{mapping}'")
                continue
                
            cat = parts[0].strip()
            rest = parts[1].strip()
            
            # Extract subcategory and direction
            if "(" not in rest or ")" not in rest:
                errors.append(f"Row {idx + 1}: Invalid mapping format '{mapping}'")
                continue
                
            sub = rest.split(" (")[0].strip()
            direction = rest.split(" (")[1].rstrip(")").strip()

            # Use existing add_mapping_rule function
            add_mapping_rule(pattern, cat, sub, direction)
            
            # Collect for bulk application
            new_rules.append({
                'pattern': pattern,
                'direction': direction
            })
            
            saved_count += 1
            logger.info(f"Added rule: {pattern} -> {cat} / {sub} ({direction})")
            
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            
    # Apply all new rules to consolidated data at once
    if new_rules:
        with st.spinner("Applying new rules to existing transactions..."):
            apply_new_rules_list_to_consolidated_data(new_rules)
    
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
