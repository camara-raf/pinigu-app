"""
Streamlit view for managing non-transaction accounts (balance-based accounts).
Allows users to define category sources for transfer capture and enter balance snapshots.
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.non_transaction_logic import (
    get_balance_accounts,
    load_balance_entries,
    add_balance_entry,
    remove_balance_entry,
    update_category_source,
    parse_category_source
)

BANK_MAPPING_FILE = os.path.join("data", "bank_mapping.csv")


def render_non_transaction_accounts_tab():
    """Render the Non-Transaction Accounts management tab."""
    st.header("⚖️ Non-Transaction Accounts")
    
    # Tab selector for different operations
    sub_tab1, sub_tab2 = st.tabs(["📋 Manage Accounts", "📊 Balance Entries"])
    
    with sub_tab1:
        render_manage_accounts_tab()
    
    with sub_tab2:
        render_balance_entries_tab()


def manage_accounts_page():
    """Standalone page for Manage Accounts."""
    st.title("📋 Manage Accounts")
    render_manage_accounts_tab()


def balance_entries_page():
    """Standalone page for Balance Entries."""
    st.title("⚖️ Balance Snapshots")
    render_balance_entries_tab()


def render_manage_accounts_tab():
    """Render account management section."""
    st.subheader("Configure Balance-Based Accounts")
    
    # Load balance accounts
    balance_accounts = get_balance_accounts()
    
    if balance_accounts.empty:
        st.info("No balance-type accounts found in bank_mapping.csv")
        return
    
    # Get all balance accounts (including those without categories)
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE)
    all_balance_accounts = bank_mapping[bank_mapping['Input'] == 'Balance'][['Bank', 'Account', 'Category_Source']].copy()
    
    if all_balance_accounts.empty:
        st.info("No balance-type accounts found in bank_mapping.csv")
        return
    
    # Account selector
    account_options = [f"{row['Bank']} - {row['Account']}" for _, row in all_balance_accounts.iterrows()]
    selected_account_str = st.selectbox(
        "Select Account",
        account_options,
        key="account_selector"
    )
    
    # Parse selected account
    selected_bank, selected_account = selected_account_str.split(" - ")
    selected_row = all_balance_accounts[
        (all_balance_accounts['Bank'] == selected_bank) & 
        (all_balance_accounts['Account'] == selected_account)
    ].iloc[0]
    
    st.write(f"**Selected**: {selected_bank} / {selected_account}")
    
    # Current category source
    current_source = selected_row['Category_Source']
    current_pairs = parse_category_source(current_source) if pd.notna(current_source) else []
    
    st.write("### Linked Categories for Transfer Capture")
    st.write("Define which categories should generate captured transactions for this account.")
    
    # Display current pairs
    if current_pairs:
        st.write("**Current linked pairs:**")
        for i, (cat, subcat) in enumerate(current_pairs):
            col1, col2, col3 = st.columns([1, 1, 0.5])
            col1.write(cat)
            col2.write(subcat)
            if col3.button("❌", key=f"remove_pair_{i}"):
                st.session_state[f"remove_pair_{i}"] = True
    else:
        st.write("No linked categories yet")
    
    # Handle pair removal
    for i in range(len(current_pairs)):
        if st.session_state.get(f"remove_pair_{i}"):
            current_pairs.pop(i)
            _save_category_source(selected_bank, selected_account, current_pairs)
            st.session_state[f"remove_pair_{i}"] = False
            st.rerun()
    
    # Add new pair
    st.write("### Add New Category Link")
    with st.form("add_category_pair", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_category = st.text_input("Category")
        with col2:
            new_subcategory = st.text_input("Sub-Category")
        
        submitted = st.form_submit_button("➕ Add Category Link")
    
        if submitted:
            if new_category and new_subcategory:
                current_pairs.append((new_category, new_subcategory))
                _save_category_source(selected_bank, selected_account, current_pairs)
                st.success(f"Added: {new_category} / {new_subcategory}")
                st.rerun()
            else:
                st.error("Both Category and Sub-Category are required")


def render_balance_entries_tab():
    """Render balance entries section."""
    st.subheader("Enter Balance Snapshots")
    
    # Load balance entries
    balance_entries = load_balance_entries()
    
    # Get all balance accounts
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE)
    all_balance_accounts = bank_mapping[bank_mapping['Input'] == 'Balance'][['Bank', 'Account', 'Currency']].copy()
    
    if all_balance_accounts.empty:
        st.info("No balance-type accounts found in bank_mapping.csv")
        return
    
    # Create two columns for entry form and existing entries
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("### Add Balance Entry")
        
        # Account selector
        account_options = [f"{row['Bank']} - {row['Account']}" for _, row in all_balance_accounts.iterrows()]
        selected_account_str = st.selectbox(
            "Select Account",
            account_options,
            key="balance_account_selector"
        )
        
        # Parse selected account
        selected_bank, selected_account = selected_account_str.split(" - ")
        
        # Get account currency
        selected_row = all_balance_accounts[
            (all_balance_accounts['Bank'] == selected_bank) & 
            (all_balance_accounts['Account'] == selected_account)
        ].iloc[0]
        account_currency = selected_row['Currency']
        
        # Currency selector (Radio)
        currency_options = ["EUR"]
        # Add account currency if it's not EUR and valid
        if pd.notna(account_currency) and account_currency != "EUR":
            currency_options.append(account_currency)
            
        # Default to account currency if available in options
        default_index = 0
        if account_currency in currency_options:
            default_index = currency_options.index(account_currency)
            
        currency = st.radio("Currency", currency_options, index=default_index, horizontal=True, key="balance_currency")
        
        # Date and balance inputs
        entry_date = st.date_input("Date", key="balance_date")
        
        label = "Balance Amount (EUR)" if currency == "EUR" else f"Original Amount ({currency})"
        if currency != "EUR":
            st.caption(f"Amount will be converted to EUR using exchange rate on {entry_date}")
            
        entry_balance = st.number_input(label, value=0.0, step=0.01, key="balance_amount")
        
        if st.button("💾 Save Balance Entry", key="save_balance"):
            if currency == "EUR":
                add_balance_entry(selected_bank, selected_account, entry_date, entry_balance)
            else:
                # Pass original currency and amount
                # The logic function will handle conversion
                add_balance_entry(
                    selected_bank, 
                    selected_account, 
                    entry_date, 
                    entry_balance, # This is the original amount here because we pass original_currency
                    original_currency=currency,
                    original_balance=entry_balance
                )
                
            st.success(f"Saved balance entry for {selected_bank} {selected_account} on {entry_date}")
            st.rerun()
    
    with col2:
        st.write("### Existing Balance Entries")
        
        if not balance_entries.empty:
            # Display all entries
            display_df = balance_entries.copy()
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
            display_df['Balance'] = display_df['Balance'].apply(lambda x: f"€ {x:,.2f}")
            
            # Format original balance if present
            if 'Original_Balance' in display_df.columns:
                display_df['Original'] = display_df.apply(
                    lambda row: f"{row['Original_Currency']} {row['Original_Balance']:,.2f}" 
                    if pd.notna(row['Original_Balance']) and row['Original_Balance'] != '' 
                    else "-", axis=1
                )
            
            display_df['Entered_Date'] = pd.to_datetime(display_df['Entered_Date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Select columns to display
            cols_to_show = ['Bank', 'Account', 'Date', 'Balance']
            if 'Original' in display_df.columns:
                cols_to_show.append('Original')
            cols_to_show.append('Entered_Date')
            
            st.dataframe(display_df[cols_to_show], width='stretch')
            
            # Delete balance entry
            st.write("**Remove Entry**")
            delete_options = [
                f"{row['Bank']} {row['Account']} - {row['Date']}"
                for _, row in balance_entries.iterrows()
            ]
            
            if delete_options:
                selected_delete = st.selectbox("Select entry to remove", delete_options, key="delete_entry")
                
                if st.button("🗑️ Delete Entry", key="delete_balance"):
                    # Parse the selection
                    parts = selected_delete.split(" - ")
                    date_str = parts[-1]
                    account_parts = parts[0].split()
                    bank = account_parts[0]
                    account = " ".join(account_parts[1:])
                    
                    remove_balance_entry(bank, account, pd.to_datetime(date_str))
                    st.success("Balance entry removed")
                    st.rerun()
        else:
            st.info("No balance entries yet")


def _save_category_source(bank, account, pairs):
    """Helper function to save category source string."""
    if pairs:
        category_source_str = "|".join([f"({cat},{subcat})" for cat, subcat in pairs])
    else:
        category_source_str = ""
    
    update_category_source(bank, account, category_source_str)
