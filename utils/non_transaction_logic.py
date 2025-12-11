import pandas as pd
import os
import requests
from datetime import datetime
from .transaction_keys import create_transaction_key
from .logger import get_logger

logger = get_logger()


BALANCE_ENTRIES_FILE = os.path.join("data", "balance_entries.csv")
BANK_MAPPING_FILE = os.path.join("data", "bank_mapping.csv")


def get_exchange_rate(date_str, from_currency, to_currency='EUR'):
    """
    Get exchange rate from api.frankfurter.dev.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        from_currency: Currency code to convert from
        to_currency: Currency code to convert to (default EUR)
        
    Returns:
        Exchange rate (float) or None if failed
    """
    url = f"https://api.frankfurter.dev/v1/{date_str}"
    params = {
        "from": from_currency,
        "to": to_currency
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"Error fetching exchange rate: {data.get('message', 'Unknown error')}")
            return None
            
        rates = data.get('rates', {})
        rate = rates.get(to_currency)
        
        return rate
            
    except Exception as e:
        logger.error(f"Exception fetching exchange rate: {e}")
        return None


def parse_category_source(category_source_str):
    """
    Parse Category_Source string into list of (Category, Sub-Category) tuples.
    Format: (Category1,Sub-Category1)|(Category2,Sub-Category2)
    
    Args:
        category_source_str: Pipe-delimited string of category tuples
        
    Returns:
        List of (category, sub_category) tuples, empty list if invalid or empty
    """
    if not category_source_str or pd.isna(category_source_str) or category_source_str.strip() == '':
        return []
    
    try:
        pairs = []
        # Split by pipe delimiter
        tuples = category_source_str.split('|')
        for tuple_str in tuples:
            # Extract content between parentheses
            tuple_str = tuple_str.strip()
            if tuple_str.startswith('(') and tuple_str.endswith(')'):
                content = tuple_str[1:-1]
                parts = [p.strip() for p in content.split(',')]
                if len(parts) == 2:
                    pairs.append((parts[0], parts[1]))
        return pairs
    except Exception as e:
        logger.error(f"Error parsing category source: {e}")
        return []


def get_balance_accounts(has_categories = False):
    """
    Get all Balance-type accounts, or just the Balance-type accounts with categories.
    
    Args:
        has_categories: If True, only return accounts with categories. If False, return all balance accounts.
    
    Returns:
        DataFrame with columns: Bank, Account, Category_Source, parsed_categories
    """
    if not os.path.exists(BANK_MAPPING_FILE):
        return pd.DataFrame()
    
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE)
    
    balance_accts = bank_mapping[
        bank_mapping['Input'] == 'Balance'
    ][['Bank', 'Account', 'Category_Source']].copy()

    # Parse category sources if the category source is not empty
    balance_accts['parsed_categories'] = balance_accts['Category_Source'].apply(parse_category_source)
    
    if has_categories:
        return balance_accts[balance_accts['parsed_categories'].apply(len) > 0]
    
    return balance_accts
    

def load_balance_entries():
    """Load balance entries from CSV."""
    if not os.path.exists(BALANCE_ENTRIES_FILE):
        return pd.DataFrame(columns=['Bank', 'Account', 'Date', 'Balance', 'Entered_Date', 'Original_Balance', 'Original_Currency'])
    
    df = pd.read_csv(BALANCE_ENTRIES_FILE)
    # Handle mixed date formats (YYYY-MM-DD and YYYY-MM-DD HH:MM:SS)
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    
    # Ensure new columns exist
    if 'Original_Balance' not in df.columns:
        df['Original_Balance'] = None
    if 'Original_Currency' not in df.columns:
        df['Original_Currency'] = None
        
    # Ensure object type for currency to avoid FutureWarning
    df['Original_Currency'] = df['Original_Currency'].astype('object')
        
    return df


def get_exceptional_transaction_accounts():
    """
    Get all Exceptional_Transaction-type accounts that requires an captured transaction from another account.
    
    Returns:
        DataFrame with columns: Bank, Account, Category_Source, parsed_categories
    """
    if not os.path.exists(BANK_MAPPING_FILE):
        return pd.DataFrame()
    
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE)
    
    exceptional_transaction_accts = bank_mapping[
        (bank_mapping['Input'] == 'Transactions') &
        bank_mapping['Category_Source'].notna() &
        (bank_mapping['Category_Source'].astype(str).str.strip() != '')
    ][['Bank', 'Account', 'Category_Source']].copy()
    
    # Parse category sources if the category source is not empty
    exceptional_transaction_accts['parsed_categories'] = exceptional_transaction_accts['Category_Source'].apply(parse_category_source)
    
    return exceptional_transaction_accts

def transfer_transactions_to_fake_accounts(consolidated_df):
    """
    Transfer transactions from transaction accounts to a fake account. 
    Based on the category sources defined in the bank mapping file for a fake account, updates records in the consolidated_df
    Moving them from their original Account to the fake account
    
    Args:
        consolidated_df: Main consolidated transactions dataframe
        
    Returns:
        the consolidated_df with transactions potentially transfered to 
    """
    if consolidated_df.empty:
        return pd.DataFrame()
    
    if not os.path.exists(BANK_MAPPING_FILE):
        return pd.DataFrame()
    
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE)

    fake_accounts = bank_mapping[
        (bank_mapping['Input'] == 'Fake') &
        bank_mapping['Category_Source'].notna() &
        (bank_mapping['Category_Source'].astype(str).str.strip() != '')
    ][['Bank', 'Account', 'Category_Source']].copy()
    
    fake_accounts['parsed_categories'] = fake_accounts['Category_Source'].apply(parse_category_source)

    total_transferred = 0
    
    for _, fake_account_row in fake_accounts.iterrows():
        bank = fake_account_row['Bank']
        account = fake_account_row['Account']
        categories = fake_account_row['parsed_categories']
        
        if not categories:
            continue
        
        # Find matching transactions in consolidated data using vectorized filtering
        for cat, subcat in categories:
            mask = (consolidated_df['Category'] == cat) & (consolidated_df['Sub-Category'] == subcat)
            num_matches = mask.sum()
            consolidated_df.loc[mask, 'Account'] = account
            consolidated_df.loc[mask, 'Bank'] = bank
            consolidated_df.loc[mask, 'Transaction_Source'] = 'Fake'
            total_transferred += num_matches
    
    logger.info(f"Transactions transferred to fake accounts: {total_transferred}")
    return consolidated_df

def get_captured_transactions(consolidated_df):
    """
    Generate captured transactions (mirrors of categorized transactions for non-transaction accounts).
    
    Args:
        consolidated_df: Main consolidated transactions dataframe
        
    Returns:
        DataFrame of captured transactions with same structure as consolidated_df
    """
    if consolidated_df.empty:
        return pd.DataFrame()
    
    balance_accounts = get_balance_accounts(has_categories=True)
    
    exceptional_transaction_accounts = get_exceptional_transaction_accounts()

    captured_accounts = pd.concat([balance_accounts, exceptional_transaction_accounts])

    if captured_accounts.empty:
        return pd.DataFrame()
    
    captured_transactions = []
    
    # For each balance account with category sources
    for _, account_row in captured_accounts.iterrows():
        bank = account_row['Bank']
        account = account_row['Account']
        categories = account_row['parsed_categories']
        
        if not categories:
            continue
        
        # Find matching transactions in consolidated data
        for _, trans in consolidated_df.iterrows():
            # Check if transaction matches any linked category+subcategory
            category_match = False
            for cat, subcat in categories:
                if (trans['Category'] == cat and trans['Sub-Category'] == subcat):
                    category_match = True
                    break
            
            if not category_match:
                continue
            
            # Create captured transaction (mirror with reversed amount)
            captured = {
                'Transaction Date': trans['Transaction Date'],
                'Effective Date': trans['Effective Date'],
                'Bank': bank,
                'Account': account,
                'Transaction': trans['Transaction'],
                'Type': trans['Type'],
                'Amount': -trans['Amount'],  # Reverse the amount
                'Balance': None,  # Captured transactions don't have balance from source
                'Category': trans['Category'],
                'Sub-Category': trans['Sub-Category'],
                'Source_File': trans['Source_File'],
                'Source_RowNo': trans['Source_RowNo'],
                'Transaction_Source': 'Captured'
            }
            captured_transactions.append(captured)
    
    if not captured_transactions:
        return pd.DataFrame()
    
    return pd.DataFrame(captured_transactions)


def get_synthetic_transactions(consolidated_df):
    """
    Generate synthetic balance-adjustment transactions based on balance entries.
    Compares manually entered balances with sum of captured transactions.
    
    Args:
        consolidated_df: Main consolidated transactions dataframe (including captured transactions)
        
    Returns:
        DataFrame of synthetic transactions
    """
    balance_entries = load_balance_entries()
    if balance_entries.empty:
        return pd.DataFrame()
    
    balance_accounts = get_balance_accounts()
    if balance_accounts.empty:
        return pd.DataFrame()
    
    synthetic_transactions = []
    
    # For each balance account
    for _, account_row in balance_accounts.iterrows():
        bank = account_row['Bank']
        account = account_row['Account']
        
        # Get balance entries for this account, sorted by date
        account_entries = balance_entries[
            (balance_entries['Bank'] == bank) & 
            (balance_entries['Account'] == account)
        ].sort_values('Date').reset_index(drop=True)
        
        if account_entries.empty:
            continue
        
        # Get all captured transactions for this account, sorted by date
        account_transactions = consolidated_df[
            (consolidated_df['Bank'] == bank) & 
            (consolidated_df['Account'] == account) &
            (consolidated_df['Transaction_Source'] == 'Captured')
        ].sort_values('Transaction Date').reset_index(drop=True)
        
        # Calculate running sum and generate synthetic transactions for each balance entry
        running_sum = 0.0
        trans_idx = 0
        cumulative_synthetic_adjustment = 0.0
        
        for _, entry in account_entries.iterrows():
            entry_date = entry['Date']
            manual_balance = entry['Balance']
            
            # Sum all captured transactions up to this entry date
            while trans_idx < len(account_transactions):
                trans_date = account_transactions.iloc[trans_idx]['Transaction Date']
                if trans_date <= entry_date:
                    running_sum += account_transactions.iloc[trans_idx]['Amount']
                    trans_idx += 1
                else:
                    break
            
            # Calculate delta (difference between manual balance and running sum + previous adjustments)
            # We need to reach manual_balance, starting from (running_sum + cumulative_synthetic_adjustment)
            delta = manual_balance - (running_sum + cumulative_synthetic_adjustment)
            
            # Only create synthetic transaction if delta is not zero
            if delta != 0:
                synthetic = {
                    'Transaction Date': entry_date,
                    'Effective Date': entry_date,
                    'Bank': bank,
                    'Account': account,
                    'Transaction': f"Adjustment - {bank} {account} | Balance {manual_balance}",
                    'Type': 'None',  # Synthetic adjustments are neutral
                    'Amount': delta,
                    'Balance': manual_balance,  # Use the manual balance as the balance field
                    'Category': 'Balance Adjustment',
                    'Sub-Category': 'Balance Adjustment',
                    'Source_File': None,
                    'Transaction_Source': 'Synthetic'
                }
                synthetic_transactions.append(synthetic)
                cumulative_synthetic_adjustment += delta
    
    if not synthetic_transactions:
        return pd.DataFrame()
    
    return pd.DataFrame(synthetic_transactions)


def add_balance_entry(bank, account, date, balance, original_currency='EUR', original_balance=None):
    """
    Add or update a balance entry.
    
    Args:
        bank: Bank name
        account: Account name
        date: Date of balance entry (datetime)
        balance: Balance amount (numeric) - This should be in EUR if original_currency is EUR, 
                 or the converted EUR amount if original_currency is not EUR.
        original_currency: Currency code of the original amount (default 'EUR')
        original_balance: Original amount in original currency (optional, None if EUR)
    """
    entries = load_balance_entries()
    
    # Convert date to string for storage
    date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
    
    # If currency is not EUR and balance is not provided (or needs calculation), 
    # we might want to handle it here, but the UI should ideally pass the converted amount.
    # However, per requirements, we should do the conversion here if needed.
    # But the function signature assumes 'balance' is passed. 
    # Let's adjust logic: if original_currency != EUR, we expect 'original_balance' to be set.
    # If 'balance' is passed as the converted amount, we use it. 
    # If 'balance' is passed as the original amount (and we need to convert), we should handle that.
    # The requirement said: "Capture the EUR Balance in the "Balance" column... and the Original_Balance"
    # So let's assume the caller might pass the original amount as 'balance' if they don't do conversion?
    # No, the plan said "Update add_balance_entry to accept original_currency and original_amount".
    # And "If original_currency is not EUR: Call get_exchange_rate... Calculate EUR amount".
    
    final_eur_balance = balance
    final_original_balance = original_balance
    final_original_currency = original_currency
    
    if original_currency != 'EUR':
        if original_balance is None:
            # If original_balance not explicitly passed, assume 'balance' arg is the original amount
            final_original_balance = balance
        
        # Calculate EUR equivalent
        rate = get_exchange_rate(date_str, original_currency, 'EUR')
        if rate:
            final_eur_balance = round(final_original_balance * rate, 2)
        else:
            # Fallback if rate fails? For now, maybe just use original amount or raise error?
            # Requirement doesn't specify failure mode. Let's warn and use original as 1:1 fallback or keep as is?
            # Better to probably fail or store as is but mark it? 
            # Let's assume 1:1 for now to avoid crashing, but print error.
            logger.warning(f"Warning: Could not convert {original_currency} to EUR for {date_str}. Using 1:1 rate.")
            final_eur_balance = final_original_balance
            
    else:
        # EUR
        final_original_balance = None
        final_original_currency = None
    
    # Check if entry already exists
    existing = entries[
        (entries['Bank'] == bank) & 
        (entries['Account'] == account) & 
        (entries['Date'] == date_str)
    ]
    
    if not existing.empty:
        # Update existing entry
        mask = (entries['Bank'] == bank) & (entries['Account'] == account) & (entries['Date'] == date_str)
        entries.loc[mask, 'Balance'] = final_eur_balance
        entries.loc[mask, 'Entered_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entries.loc[mask, 'Original_Balance'] = final_original_balance
        entries.loc[mask, 'Original_Currency'] = final_original_currency
    else:
        # Add new entry
        new_entry = pd.DataFrame([{
            'Bank': bank,
            'Account': account,
            'Date': date_str,
            'Balance': final_eur_balance,
            'Entered_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Original_Balance': final_original_balance,
            'Original_Currency': final_original_currency
        }])
        entries = pd.concat([entries, new_entry], ignore_index=True, sort=False)
    
    entries.to_csv(BALANCE_ENTRIES_FILE, index=False)


def remove_balance_entry(bank, account, date):
    """
    Remove a balance entry.
    
    Args:
        bank: Bank name
        account: Account name
        date: Date of balance entry to remove (datetime)
    """
    entries = load_balance_entries()
    date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
    
    entries = entries[~(
        (entries['Bank'] == bank) & 
        (entries['Account'] == account) & 
        (entries['Date'] == date_str)
    )]
    
    entries.to_csv(BALANCE_ENTRIES_FILE, index=False)


def update_category_source(bank, account, category_source_str):
    """
    Update Category_Source for a balance account in bank_mapping.csv.
    
    Args:
        bank: Bank name
        account: Account name
        category_source_str: Pipe-delimited category+subcategory pairs
    """
    if not os.path.exists(BANK_MAPPING_FILE):
        return
    
    bank_mapping = pd.read_csv(BANK_MAPPING_FILE, dtype=str)
    
    # Find and update the account
    mask = (bank_mapping['Bank'] == bank) & (bank_mapping['Account'] == account)
    if mask.any():
        bank_mapping.loc[mask, 'Category_Source'] = category_source_str
        bank_mapping.to_csv(BANK_MAPPING_FILE, index=False)
