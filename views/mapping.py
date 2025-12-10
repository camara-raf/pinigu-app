import streamlit as st
import pandas as pd
from utils import (
    load_mapping_rules, delete_mapping_rule,
    add_mapping_rule, test_rule, get_category_subcategory_combinations,
    get_subcategories_for_category, get_direction_for_subcategory,
    apply_new_rules_list_to_consolidated_data, get_logger
)

logger = get_logger(__name__)

def render_mapping_tab():
    """Render the Category Mapping tab."""
    st.header("🏷️ Category Mapping")
    
    # Load existing rules
    rules_df = load_mapping_rules()
    
    st.subheader("📋 Existing Rules")
    if not rules_df.empty:
        display_rules = rules_df[['Pattern', 'Category', 'Sub-Category', 'Direction', 'Priority']].copy()
        st.dataframe(display_rules, width='stretch', hide_index=True)
        
        # Simplified delete section
        st.subheader("🗑️ Delete a Rule")
        col1, col2 = st.columns([4, 1])
        
        # Prepare rule options for dropdown
        rule_options = {}
        rule_labels = []
        for _, rule in rules_df.iterrows():
            label = f"{rule['Pattern']} → {rule['Category']} / {rule['Sub-Category']} ({rule['Direction']})"
            rule_options[label] = rule['Rule_ID']
            rule_labels.append(label)
        
        with col1:
            selected_rule = st.selectbox("Select a rule to delete", rule_labels, key="delete_rule_select")
        
        with col2:
            if st.button("🗑️ Delete", key="delete_rule_button", type="secondary"):
                if selected_rule:
                    st.warning("⚠️ Are you sure you want to delete this rule? This action cannot be undone.")
                    
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Confirm Delete", key="confirm_delete_button", type="primary"):
                            delete_mapping_rule(rule_options[selected_rule])
                            st.success("✅ Rule deleted successfully")
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ Cancel", key="cancel_delete_button"):
                            st.info("Deletion cancelled")
    else:
        st.info("ℹ️ No rules created yet.")
    
    st.divider()
    
    st.subheader("➕ Create New Rule")
    
    st.info("💡 **Tip:** Use `*` as wildcard. Examples:\n"
            "- `*grocery*` matches 'whole foods grocery', 'grocery store', etc.\n"
            "- `*amazon*` matches any Amazon transaction\n"
            "- `salary*` matches anything starting with 'salary'")
    
    # Get existing combinations
    hierarchy = get_category_subcategory_combinations()
    all_categories = list(hierarchy.keys()) if hierarchy else []
    
    # Toggle between existing and new combination
    use_existing = st.checkbox("Use existing combination", value=True, key="use_existing_combo")
    
    # Pattern input and Category selection side by side
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        pattern_input = st.text_input("Pattern", placeholder="e.g., *restaurant*", key="pattern_input")
    
    with col2:
        if use_existing and all_categories:
            # Existing combination selection
            category_input = st.selectbox("Category", sorted(all_categories), key="category_existing")
        else:
            # New category creation
            category_input = st.text_input("New Category", placeholder="e.g., Entertainment", key="category_new")
    with col3:
        sub_category_input = None
        direction_input = None
    
        if use_existing and all_categories and category_input:
            # Existing combination selection - sub-category and direction
            subcats = get_subcategories_for_category(category_input)
            subcat_labels = [f"{item['sub_category']} ({item['direction']})" for item in subcats]
        
            if subcats:
                selected_subcat = st.selectbox("Sub-Category", subcat_labels, key="subcat_existing")
                # Extract sub-category name from label
                sub_category_input = selected_subcat.split(' (')[0]
                direction_input = get_direction_for_subcategory(category_input, sub_category_input)
                
            else:
                st.warning("No sub-categories found for this category")
        elif not use_existing:
            
            col1, col2 = st.columns(2)
            with col1:
                sub_category_input = st.text_input("New Sub-Category", placeholder="e.g., Movies", key="subcat_new")
            with col2:
                direction_input = st.selectbox("Direction", ["In", "Out", "None"], key="direction_new")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_button = st.button("🔍 Test Rule", key="test_rule_button")
    
    with col2:
        create_button = st.button("💾 Save Rule", key="save_rule_button", type="primary")
    
    # Test rule logic
    if test_button and pattern_input and category_input and sub_category_input and direction_input:
        uncategorized, categorized = test_rule(pattern_input, category_input, sub_category_input, direction_input)
        
        if uncategorized.empty and categorized.empty:
            st.warning("No matches found for this pattern and direction")
        else:
            st.subheader("🔍 Test Results")
            
            if not uncategorized.empty:
                st.subheader("🟡 Uncategorized Matches (Highlighted)")
                for _, row in uncategorized.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{row['Transaction']}**")
                        st.caption(f"{row['Amount']} • {row['Transaction Date'].strftime('%Y-%m-%d')} • Type: {row['Type']}")
                    with col2:
                        st.write("🟡 Uncategorized")
            
            if not categorized.empty:
                st.subheader("✅ Already Categorized Matches")
                for _, row in categorized.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{row['Transaction']}**")
                        st.caption(f"{row['Amount']} • {row['Transaction Date'].strftime('%Y-%m-%d')} • Type: {row['Type']}")
                    with col2:
                        st.write(f"✅ {row['Category']}")
            
            st.info(f"📊 Total matches: {len(uncategorized) + len(categorized)}")
    
    # Save rule logic
    if create_button:
        if not pattern_input or not category_input or not sub_category_input or not direction_input:
            st.error("❌ Pattern, Category, Sub-Category, and Direction are all required")
        else:
            try:
                add_mapping_rule(pattern_input, category_input, sub_category_input, direction_input)
                
                # Apply the new rule immediately to consolidated data
                apply_new_rules_list_to_consolidated_data([{'pattern': pattern_input}])
                
                st.success(f"✅ Rule saved! Pattern: '{pattern_input}' → {category_input} / {sub_category_input} ({direction_input})")
                st.session_state.data_refresh_needed = True
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error saving rule: {str(e)}")