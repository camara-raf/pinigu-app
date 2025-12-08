"""
File auto-detection module for identifying Bank+Account combinations.

Analyzes file structure (header names, columns, file format) to determine
which parsing signature should be used.
"""
import pandas as pd
import os
import yaml
from typing import Dict, Tuple, Optional, List
from .file_management import read_bank_mapping

CONFIG_PATH = 'config/file_signatures.yaml'

def load_signatures():
    """Load signatures from YAML configuration."""
    path = CONFIG_PATH
    if not os.path.exists(path):
        if os.path.exists(os.path.join('..', path)):
            path = os.path.join('..', path)
        else:
            return []
            
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        return data.get('signatures', [])

def read_file_header(file_path: str, skiprows: int = 0, usecols: Optional[str] = None, 
                     max_rows: int = 5) -> Optional[pd.DataFrame]:
    """
    Safely read file header without loading entire file.
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.xls', '.xlsx']:
            # Note: usecols in signature might be string "A:E" or list.
            # pd.read_excel supports string "A:E".
            df = pd.read_excel(file_path, sheet_name=0, skiprows=skiprows, 
                             usecols=usecols, nrows=max_rows)
        elif file_ext == '.csv':
            df = pd.read_csv(file_path, skiprows=skiprows, usecols=usecols, nrows=max_rows)
        else:
            return None
            
        return df
    except Exception as e:
        print(f"Error reading file header: {e}")
        return None


def check_column_match(file_columns: List[str], required_columns: List[str], 
                       strict: bool = True) -> bool:
    """
    Check if file has the required columns.
    """
    file_cols_lower = [str(col).lower().strip() for col in file_columns]
    required_lower = [str(col).lower().strip() for col in required_columns]
    
    if strict:
        # Exact match: same columns, same count, same order
        # Note: Some files might have extra columns at the end, handling strictness carefully.
        # If strict is True, we expect the required columns to be the exact set of columns in headers?
        # Or just that the required columns are present in that order?
        # The previous implementation was: file_cols_lower == required_lower
        # This implies the file MUST NOT have extra columns if we pass all columns.
        return file_cols_lower == required_lower
    else:
        # Subset match: all required columns must be present
        return all(col in file_cols_lower for col in required_lower)


def detect_bank_account_pair(file_path: str) -> Optional[Tuple[str, str, float]]:
    """
    Detect the Bank+Account pair for a file by analyzing its structure.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    signatures = load_signatures()
    
    # Get enabled bank/accounts from mapping
    mapping_df = read_bank_mapping()
    enabled_pairs = set()
    for _, row in mapping_df.iterrows():
        if row.get('Input') == 'Transactions':
            enabled_pairs.add((row['Bank'], row['Account']))
    
    best_match = None
    
    for sig in signatures:
        bank = sig.get('bank')
        account = sig.get('account')
        
        # Check if this bank/account is enabled in the app
        if (bank, account) not in enabled_pairs:
            continue

        # STRICT CHECK 1: File extension
        if file_ext not in sig.get('file_extensions', []):
            continue
        
        # Try to read file header
        skiprows = sig.get('skiprows', 0)
        # Note: 'usecols' logic in read_excel is tricky with varying columns.
        # Best to read all columns and check if required ones are present.
        # But previous logic used 'usecols' string from signature. 
        # My YAML doesn't have 'usecols' string (like "A:E") anymore, it has 'required_columns'.
        # So I will read without usecols restriction to see what's in the file.
        
        df_header = read_file_header(
            file_path,
            skiprows=skiprows
        )
        
        if df_header is None or df_header.empty:
            continue
        
        required_cols = sig.get('required_columns', [])
        if not required_cols:
            continue
        
        # STRICT CHECK 2: Column count and names
        # Previous logic was very strict: check_column_match(..., strict=True)
        # which meant df.columns MUST be exactly required_columns.
        # If I read without usecols, df might have extra columns.
        # I should check if the required columns are present.
        # If strict matching is desired, I should check if the first N columns match?
        # Or if the set matches?
        
        # Let's use subset matching for robustness, or strict if the file format is rigid.
        # The legacy code was strict. Let's try to be accurate.
        # If I read all columns, I can check if the detected columns *contain* the required ones in order?
        # Or just use subset match.
        
        columns_match = check_column_match(
            df_header.columns.tolist(), 
            required_cols,
            strict=False # Relaxing to False to allow extra columns if present, unless strict is needed. 
            # But wait, original code was strict=True.
            # If I want to maintain strictness, I need to know if the file should ONLY have these columns.
        )
        
        # Let's refine strictness:
        # If the file format uses rigid column positions (e.g. A:E), we expect those columns.
        # If I read the file, I get all columns.
        # If required_columns matches the first N columns of the file, that's a good match.
        
        # Let's try exact match on the available columns.
        # If I filter the file columns to only those in required, do they match?
        
        if columns_match:
             return (bank, account, 1.0)
    
    return None


def detect_all_files(file_paths: List[str]) -> Dict[str, Optional[Tuple[str, str, float]]]:
    """
    Detect Bank+Account pairs for multiple files.
    """
    results = {}
    for file_path in file_paths:
        results[file_path] = detect_bank_account_pair(file_path)
    return results


def get_module_signature_info(bank: str, account: str) -> Optional[Dict]:
    """
    Get the file format signature for a Bank+Account combination.
    """
    signatures = load_signatures()
    
    for sig in signatures:
        if sig.get('bank') == bank and (sig.get('account') == account or sig.get('account') in account):
             return {
                 'module': f"{bank}_{account}", # Dummy module name
                 'account_type': account,
                 'file_extensions': sig.get('file_extensions', []),
                 'required_columns': sig.get('required_columns', []),
                 'description': f"{bank} {account} format"
             }
    
    return None
