import streamlit as st
import pandas as pd
from utils import (
    load_manual_overwrites, remove_manual_override,
    create_transaction_key, add_manual_override,
    get_category_subcategory_combinations, get_subcategories_for_category,
    get_direction_for_subcategory
)
from utils.manual_overrides import (
    load_amount_overwrites, add_amount_override, remove_amount_override
)


def render_manual_overwrite_tab():
    """Render the Manual Overwrites tab."""
    st.header("✏️ Manual Overwrites")
    
    consolidated_df = st.session_state.consolidated_df
    
    if not consolidated_df.empty:
        # Add transaction key for reference
        consolidated_df['_key'] = consolidated_df.apply(create_transaction_key, axis=1)
        
        # Search filter
        search_term = st.text_input("🔍 Search transactions", placeholder="Filter by transaction name...")
        
        if search_term:
            filtered_df = consolidated_df[consolidated_df['Transaction'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = consolidated_df
        
        # --- Display Existing Overwrites ---
        
        # 1. Instance Overwrites
        overwrites = load_manual_overwrites()
        
        st.subheader("Existing Overwrites")
        
        tab1, tab2 = st.tabs(["Instance Overwrites", "Transaction + Amount Overwrites"])
        
        with tab1:
            if overwrites:
                # Create overwrites dataframe for display
                overwrites_list = []
                for key, override in overwrites.items():
                    # Find the original transaction
                    original_trans = filtered_df[filtered_df['_key'] == key]
                    if not original_trans.empty:
                        row = original_trans.iloc[0]
                        overwrites_list.append({
                            'Date': row['Transaction Date'],
                            'Transaction': row['Transaction'],
                            'Amount': row['Amount'],
                            'Original Category': row['Category'],
                            'Original Sub-Category': row['Sub-Category'],
                            'Override Date': override['Override_Date'],
                            '_key': key,
                            'Overridden To': f"{override['Category']} / {override['Sub-Category']} ({override['Direction']})"
                        })
                
                if overwrites_list:
                    display_overwrites = pd.DataFrame(overwrites_list)
                    display_overwrites = display_overwrites.sort_values('Date', ascending=False)
                    
                    st.dataframe(display_overwrites[['Date', 'Transaction', 'Amount', 'Original Category', 'Original Sub-Category', 'Overridden To', 'Override Date']], 
                                use_container_width=True, hide_index=True)
                    
                    st.caption("🗑️ Remove Instance Overwrites")
                    for _, row in display_overwrites.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{row['Transaction']}** ({row['Amount']}) - {row['Date'].strftime('%Y-%m-%d')}")
                        with col2:
                            if st.button("Remove", key=f"remove_override_{row['_key']}"):
                                remove_manual_override(row['_key'])
                                st.success("✅ Override removed")
                                st.rerun()
                else:
                    st.info("ℹ️ No instance overwrites found matching current filter.")
            else:
                st.info("ℹ️ No instance overwrites created yet.")

        with tab2:
            amount_overwrites = load_amount_overwrites()
            if amount_overwrites:
                amt_list = []
                for (trans, amt), v in amount_overwrites.items():
                    # Filter by search term if present
                    if search_term and search_term.lower() not in trans.lower():
                        continue
                        
                    amt_list.append({
                        'Transaction': trans,
                        'Amount': amt,
                        'Category': v['Category'],
                        'Sub-Category': v['Sub-Category'],
                        'Direction': v['Direction'],
                        'Override Date': v['Override_Date'],
                        '_key': f"{trans}_{amt}" # Pseudo key for UI
                    })
                
                if amt_list:
                    df_amt = pd.DataFrame(amt_list)
                    st.dataframe(df_amt, use_container_width=True, hide_index=True)
                    
                    st.caption("🗑️ Remove Amount Overwrites")
                    for _, row in df_amt.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{row['Transaction']}** ({row['Amount']})")
                        with col2:
                            if st.button("Remove", key=f"remove_amt_override_{row['_key']}"):
                                remove_amount_override(row['Transaction'], row['Amount'])
                                st.success("✅ Override removed")
                                st.rerun()
                else:
                    st.info("ℹ️ No amount overwrites found matching current filter.")
            else:
                st.info("ℹ️ No amount overwrites created yet.")
        
        st.divider()
        st.subheader("➕ Create New Override")
        
        # Filter to uncategorized transactions
        uncategorized_df = filtered_df[filtered_df['Category'] == 'Uncategorized']
        
        if not uncategorized_df.empty:
            # Select transaction
            transaction_options = [f"{row['Transaction Date'].strftime('%Y-%m-%d')} | {row['Transaction']} ({row['Amount']})" 
                                  for _, row in uncategorized_df.iterrows()]
            selected_transaction_str = st.selectbox("Select uncategorized transaction", transaction_options, key="select_transaction_override")
            
            if selected_transaction_str:
                # Find the selected transaction
                selected_idx = transaction_options.index(selected_transaction_str)
                selected_row = uncategorized_df.iloc[selected_idx]
                transaction_key = selected_row['_key']
                
                st.write(f"**Transaction:** {selected_row['Transaction']}")
                st.write(f"**Amount:** {selected_row['Amount']} | **Type:** {selected_row['Type']} | **Date:** {selected_row['Transaction Date'].strftime('%Y-%m-%d')}")
                
                # Scope Selection
                override_scope = st.radio(
                    "Apply Override To:",
                    ["This specific transaction only (Instance)", "All transactions with same Name & Amount"],
                    index=0,
                    key="override_scope"
                )
                
                st.divider()
                
                # Category + Sub-Category + Direction selection (same as mapping rules)
                hierarchy = get_category_subcategory_combinations()
                all_categories = list(hierarchy.keys()) if hierarchy else []
                
                use_existing = st.checkbox("Use existing combination", value=True, key="use_existing_override")
                
                category_override = None
                sub_category_override = None
                direction_override = None
                
                if use_existing and all_categories:
                    # Existing combination selection
                    category_override = st.selectbox("Category", sorted(all_categories), key="category_existing_override")
                    
                    if category_override:
                        subcats = get_subcategories_for_category(category_override)
                        subcat_labels = [f"{item['sub_category']} ({item['direction']})" for item in subcats]
                        
                        if subcats:
                            selected_subcat = st.selectbox("Sub-Category", subcat_labels, key="subcat_existing_override")
                            # Extract sub-category name from label
                            sub_category_override = selected_subcat.split(' (')[0]
                            direction_override = get_direction_for_subcategory(category_override, sub_category_override)
                            
                            st.info(f"📍 Direction: **{direction_override}** (Read-only)")
                else:
                    # New combination creation
                    st.write("**Create new Category + Sub-Category + Direction**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        category_override = st.text_input("New Category", placeholder="e.g., Entertainment", key="category_new_override")
                    with col2:
                        sub_category_override = st.text_input("New Sub-Category", placeholder="e.g., Movies", key="subcat_new_override")
                    with col3:
                        direction_override = st.selectbox("Direction", ["In", "Out", "None"], key="direction_new_override")
                
                if st.button("💾 Save Override", key="save_override_button", type="primary"):
                    if not category_override or not sub_category_override or not direction_override:
                        st.error("❌ Category, Sub-Category, and Direction are all required")
                    else:
                        try:
                            if "Instance" in override_scope:
                                add_manual_override(transaction_key, category_override, sub_category_override, direction_override)
                                st.success(f"✅ Instance override saved!")
                            else:
                                add_amount_override(selected_row['Transaction'], selected_row['Amount'], category_override, sub_category_override, direction_override)
                                st.success(f"✅ Transaction + Amount override saved!")
                                
                            st.session_state.data_refresh_needed = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving override: {str(e)}")
        else:
            st.info("📭 No uncategorized transactions found.")
    else:
        st.info("📭 No transaction data available. Please upload files and reload data.")