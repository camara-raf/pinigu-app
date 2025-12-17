import streamlit as st
import pandas as pd
from utils.categorization import (
    get_mapping_pairs_with_counts,
    save_mapping_pairs_bulk,
    get_rules_by_pair_id,
    save_rules_bulk
)

def detect_changes_summary(original_df, edited_df, id_col, compare_cols):
    """
    Compares original and edited dataframes to identify added, removed, and modified rows.
    Returns (changes_detected, summary_parts)
    """
    changes_detected = False
    summary_parts = []
    
    # 1. Identify Deleted Rows
    original_ids = set(original_df[id_col])
    
    # Handle cases where ID might be float/NaN in edited df due to new rows
    if id_col in edited_df.columns:
        valid_id_mask = edited_df[id_col].notna() & (edited_df[id_col] != 0)
        current_valid_rows = edited_df[valid_id_mask].copy()
        
        try:
            current_ids = set(current_valid_rows[id_col].astype(int))
        except (ValueError, TypeError):
            # Fallback if IDs are not coercible to int
            current_ids = set(current_valid_rows[id_col])
    else:
        current_valid_rows = pd.DataFrame()
        current_ids = set()
        
    deleted_ids = original_ids - current_ids
    if deleted_ids:
        changes_detected = True
        summary_parts.append(f"{len(deleted_ids)} deleted rows")

    # 2. Identify New Rows
    if id_col in edited_df.columns:
        new_rows_mask = edited_df[id_col].isna() | (edited_df[id_col] == 0)
        new_count = new_rows_mask.sum()
        if new_count > 0:
            changes_detected = True
            summary_parts.append(f"{new_count} new rows")
            
    # 3. Identify Edited Rows
    edit_count = 0
    common_ids = original_ids.intersection(current_ids)
    if common_ids:
        # Filter and sort to align
        orig_common = original_df[original_df[id_col].isin(common_ids)].sort_values(id_col).set_index(id_col)
        
        # Handle type matching for comparison
        if pd.api.types.is_numeric_dtype(original_df[id_col]) and not current_valid_rows.empty:
             curr_common = current_valid_rows[current_valid_rows[id_col].isin(common_ids)].astype({id_col: int}).sort_values(id_col).set_index(id_col)
        else:
             curr_common = current_valid_rows[current_valid_rows[id_col].isin(common_ids)].sort_values(id_col).set_index(id_col)
        
        # Compare relevant columns
        valid_compare_cols = [c for c in compare_cols if c in orig_common.columns and c in curr_common.columns]
        
        if valid_compare_cols:
            # Reindex ensures columns are in same order
            diff = (orig_common[valid_compare_cols] != curr_common[valid_compare_cols]).any(axis=1)
            edit_count = diff.sum()
            
            if edit_count > 0:
                changes_detected = True
                summary_parts.append(f"{edit_count} edited rows")
    
    return changes_detected, summary_parts

def render_mapping_pairs_view():
    st.header("🏷️ Manage Mapping Pairs")
    
    tab1, tab2 = st.tabs(["Mapping Groups", "Rules by Group"])
    
    # --- Tab 1: Manage Mapping Pairs ---
    with tab1:
        st.markdown("Define the Category, Sub-Category, and Direction combinations available for mapping.")
        
        # Load Data
        pairs_df = get_mapping_pairs_with_counts()
        
        # Configure Columns for Editor
        column_config = {
            "Pair_ID": st.column_config.NumberColumn("ID", disabled=True),
            "Category": st.column_config.TextColumn("Category", required=True),
            "Sub-Category": st.column_config.TextColumn("Sub-Category", required=True),
            "Direction": st.column_config.SelectboxColumn(
                "Direction",
                options=["In", "Out", "None"],
                required=True,
                help="Transactions flow: In (Income), Out (Expense), or None (Internal/Both)"
            ),
            "Rule_Count": st.column_config.NumberColumn(
                "Rules", 
                format="%d",
                disabled=True
            ),
        }
        
        # Data Editor
        edited_pairs_df = st.data_editor(
            pairs_df,
            column_config=column_config,
            width="stretch",
            num_rows="dynamic",
            key="mapping_pairs_editor",
            hide_index=True,
            disabled=["Pair_ID", "Rule_Count"]
        )
        
        
        # --- Change Detection Logic ---
        changes_detected, summary_parts = detect_changes_summary(
            pairs_df, 
            edited_pairs_df, 
            "Pair_ID", 
            ["Category", "Sub-Category", "Direction"]
        )
        
        # Display Summary
        if changes_detected:
            st.info(f"Pending Changes: {'; '.join(summary_parts)}")
        
        # Save Button
        if st.button("💾 Save Changes (Pairs)", type="primary", disabled=not changes_detected):
            try:
                save_mapping_pairs_bulk(edited_pairs_df)
                st.success("Mapping pairs updated successfully!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # --- Tab 2: Manage Rules by Pair ---
    with tab2:
        st.markdown("Manage regex rules for a specific category group.")
        
        # Select Pair
        # Create user-friendly labels
        if pairs_df.empty:
            st.info("No mapping pairs available. Create some in the first tab.")
            return

        pair_options = pairs_df.apply(
            lambda x: f"{x['Category']} -> {x['Sub-Category']} ({x['Direction']})", axis=1
        ).tolist()
        
        # Need to map back selection to ID
        # Create a dictionary for easy lookup
        pair_map = {
            f"{row['Category']} -> {row['Sub-Category']} ({row['Direction']})": row['Pair_ID'] 
            for _, row in pairs_df.iterrows()
        }
        
        selected_label = st.selectbox("Select Group to Edit Rules:", pair_options)
        
        if selected_label:
            selected_pair_id = pair_map[selected_label]
            
            # Load Rules for this pair
            rules_df = get_rules_by_pair_id(selected_pair_id).reset_index(drop=True)
            
            # FORCE Pattern to be string to avoid list inference issues
            if 'Pattern' in rules_df.columns:
                rules_df['Pattern'] = rules_df['Pattern'].astype(str)
            
            st.caption(f"Editing rules for Pair ID: {selected_pair_id}. Found {len(rules_df)} rules.")
            
            # Configure Rule Columns
            rule_col_config = {
                "Rule_ID": st.column_config.NumberColumn("ID", disabled=True),
                "Pattern": st.column_config.TextColumn("Pattern", required=True, width="large", validate="^.*$"),
                "Pair_ID": st.column_config.NumberColumn("Pair ID", disabled=True) # Hidden or disabled
            }
            
            # Allow user to edit rules
            edited_rules_df = st.data_editor(
                rules_df,
                column_config=rule_col_config,
                width="stretch",
                num_rows="dynamic",
                key=f"rules_editor_{selected_pair_id}",
                hide_index=True,
                column_order=["Rule_ID", "Pattern"] # Clean view - hide calculated fields
            )
            
            
            # Change Detection for Rules
            rules_changes_detected, rules_summary = detect_changes_summary(
                rules_df,
                edited_rules_df,
                "Rule_ID",
                ["Pattern"]
            )
            
            if rules_changes_detected:
                st.info(f"Pending Changes: {'; '.join(rules_summary)}")

            if st.button("💾 Save Rules", type="primary", disabled=not rules_changes_detected):
                # DEBUG: Check for list artifacts
                artifacts_found = []
                for idx, row in edited_rules_df.iterrows():
                    pat = row.get("Pattern", "")
                    if isinstance(pat, list) or (isinstance(pat, str) and pat.startswith("['") and pat.endswith("']")):
                        artifacts_found.append(f"Row {idx}: {pat} (Type: {type(pat)})")
                
                if artifacts_found:
                    st.warning(f"⚠️ Detected potential list artifacts in Pattern (Streamlit issue). Saving anyway but please report this:\n" + "\n".join(artifacts_found))
                
                try:
                    save_rules_bulk(edited_rules_df, selected_pair_id)
                    st.success(f"Rules for '{selected_label}' updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred saving rules: {e}")
