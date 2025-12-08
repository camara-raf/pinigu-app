"""
Utility functions for managing manual transaction overrides.
Handles storing, loading, and removing manual categorization overwrites.
Supports Category + Sub-Category + Direction combinations.
"""
import pandas as pd
import os
from datetime import datetime
from .transaction_keys import create_transaction_key

MANUAL_OVERWRITES_FILE = os.path.join("data", "manual_overwrites.csv")


def load_manual_overwrites():
    """Load manual overwrites from CSV."""
    if os.path.exists(MANUAL_OVERWRITES_FILE):
        df = pd.read_csv(MANUAL_OVERWRITES_FILE,keep_default_na=False,na_values=['NaN'])
        # Ensure required columns exist
        required_cols = ['Transaction_Key', 'Category', 'Sub-Category', 'Direction', 'Override_Date']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        return df.set_index('Transaction_Key').to_dict('index')
    return {}


def add_manual_override(transaction_key, category, sub_category, direction):
    """Add or update manual override with Category, Sub-Category, and Direction."""
    overwrites = load_manual_overwrites()
    
    overwrites[transaction_key] = {
        'Category': category,
        'Sub-Category': sub_category,
        'Direction': direction,
        'Override_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    df = pd.DataFrame([
        {
            'Transaction_Key': k,
            'Category': v['Category'],
            'Sub-Category': v['Sub-Category'],
            'Direction': v['Direction'],
            'Override_Date': v['Override_Date']
        }
        for k, v in overwrites.items()
    ])
    
    df.to_csv(MANUAL_OVERWRITES_FILE, index=False)


def remove_manual_override(transaction_key):
    """Remove a manual override."""
    overwrites = load_manual_overwrites()
    
    if transaction_key in overwrites:
        del overwrites[transaction_key]
    
    if not overwrites:
        # If no overwrites left, save empty file with headers
        df = pd.DataFrame(columns=['Transaction_Key', 'Category', 'Sub-Category', 'Direction', 'Override_Date'])
    else:
        df = pd.DataFrame([
            {
                'Transaction_Key': k,
                'Category': v['Category'],
                'Sub-Category': v['Sub-Category'],
                'Direction': v['Direction'],
                'Override_Date': v['Override_Date']
            }
            for k, v in overwrites.items()
        ])
    
    df.to_csv(MANUAL_OVERWRITES_FILE, index=False)


AMOUNT_OVERWRITES_FILE = os.path.join("data", "amount_overwrites.csv")


def load_amount_overwrites():
    """Load amount-based overwrites from CSV."""
    if os.path.exists(AMOUNT_OVERWRITES_FILE):
        df = pd.read_csv(AMOUNT_OVERWRITES_FILE, keep_default_na=False, na_values=['NaN'])
        # Ensure required columns exist
        required_cols = ['Transaction', 'Amount', 'Category', 'Sub-Category', 'Direction', 'Override_Date']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        # Create a dictionary keyed by (Transaction, Amount)
        # Note: Amount should be handled carefully (float vs string), but assuming exact match for now
        overwrites = {}
        for _, row in df.iterrows():
            key = (str(row['Transaction']), float(row['Amount']) if row['Amount'] else 0.0)
            overwrites[key] = {
                'Category': row['Category'],
                'Sub-Category': row['Sub-Category'],
                'Direction': row['Direction'],
                'Override_Date': row['Override_Date']
            }
        return overwrites
    return {}


def add_amount_override(transaction, amount, category, sub_category, direction):
    """Add or update manual override based on Transaction + Amount."""
    overwrites = load_amount_overwrites()
    
    # Ensure amount is float for consistency
    try:
        amount_val = float(amount)
    except (ValueError, TypeError):
        amount_val = 0.0
        
    key = (str(transaction), amount_val)
    
    overwrites[key] = {
        'Category': category,
        'Sub-Category': sub_category,
        'Direction': direction,
        'Override_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    _save_amount_overwrites(overwrites)


def remove_amount_override(transaction, amount):
    """Remove an amount-based override."""
    overwrites = load_amount_overwrites()
    
    try:
        amount_val = float(amount)
    except (ValueError, TypeError):
        amount_val = 0.0
        
    key = (str(transaction), amount_val)
    
    if key in overwrites:
        del overwrites[key]
        _save_amount_overwrites(overwrites)


def _save_amount_overwrites(overwrites):
    """Save amount overwrites to CSV."""
    if not overwrites:
        df = pd.DataFrame(columns=['Transaction', 'Amount', 'Category', 'Sub-Category', 'Direction', 'Override_Date'])
    else:
        data_list = []
        for (trans, amt), v in overwrites.items():
            data_list.append({
                'Transaction': trans,
                'Amount': amt,
                'Category': v['Category'],
                'Sub-Category': v['Sub-Category'],
                'Direction': v['Direction'],
                'Override_Date': v['Override_Date']
            })
        df = pd.DataFrame(data_list)
    
    df.to_csv(AMOUNT_OVERWRITES_FILE, index=False)
