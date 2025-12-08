"""
File auto-detection module for identifying Bank+Account combinations.

Analyzes file structure (header names, columns, file format) to determine
which parsing module should be used, without executing the module itself.
"""
import pandas as pd
import os
from typing import Dict, Tuple, Optional, List
from .file_management import read_bank_mapping


# Define module signatures - characteristics of each bank's file format
MODULE_SIGNATURES = {
    'santander.readSantanderChequing': {
        'Chequing': {
            'file_extensions': ['.xls'],
            'required_columns': ['FECHA OPERACIÓN', 'FECHA VALOR', 'CONCEPTO', 'IMPORTE EUR', 'SALDO'],
            'skiprows': 7,
            'usecols': 'A:E',
            'description': 'Santander with columns A:E, header at row 8'
        }
    },
    'santander.readSantanderCredit': {
        'Credit': {
            'file_extensions': ['.xls'],
            'required_columns': ['FECHA OPERACIÓN', 'CONCEPTO', 'IMPORTE EUR'],
            'skiprows': 7,
            'usecols': 'A:C',
            'description': 'Santander Credit with columns A:C, header at row 8'
        }
    },
    'bbva.readBBVA': {
        'Chequing': {
            'file_extensions': ['.xlsx'],
            'required_columns': ['F.Valor', 'Fecha', 'Concepto', 'Movimiento', 'Importe', 'Divisa', 'Disponible', 'Divisa.1', 'Observaciones'],
            'skiprows': 4,
            'usecols': 'B:J',
            'description': 'BBVA with columns B:J, header at row 5'
        }
    },
    'revolut.readRevolut': {
        'Chequing-Rafa': {
            'file_extensions': ['.csv'],
            'required_columns': ['Type', 'Product', 'Started Date', 'Completed Date', 'Description', 'Amount', 'Fee', 'Currency', 'State', 'Balance'],
            'skiprows': 0,
            'description': 'Revolut CSV with standard columns'
        }
    }
}


def read_file_header(file_path: str, skiprows: int = 0, usecols: Optional[str] = None, 
                     max_rows: int = 5) -> Optional[pd.DataFrame]:
    """
    Safely read file header without loading entire file.
    
    Args:
        file_path: Path to the file
        skiprows: Number of rows to skip
        usecols: Columns to read (if specified)
        max_rows: Maximum number of rows to read
        
    Returns:
        DataFrame with header and first few rows, or None if error
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.xls', '.xlsx']:
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
    
    Args:
        file_columns: Columns found in the file
        required_columns: Required columns for the format
        strict: If True, requires exact match (same columns, same order, same count).
                If False, requires all required columns to be present (allows extras).
        
    Returns:
        True if columns match requirements exactly
    """
    file_cols_lower = [str(col).lower().strip() for col in file_columns]
    required_lower = [str(col).lower().strip() for col in required_columns]
    
    if strict:
        # Exact match: same columns, same count, same order
        return file_cols_lower == required_lower
    else:
        # Subset match: all required columns must be present
        return all(col in file_cols_lower for col in required_lower)


def detect_bank_account_pair(file_path: str) -> Optional[Tuple[str, str, float]]:
    """
    Detect the Bank+Account pair for a file by analyzing its structure.
    
    Uses STRICT matching:
    - File extension must match exactly
    - Header row position (skiprows) must match
    - Column COUNT must match exactly
    - Column NAMES must match exactly (in order, case-insensitive)
    
    Args:
        file_path: Path to the uploaded file
        
    Returns:
        Tuple of (bank, account, confidence_score) or None if no match found
        Confidence score ranges from 0.0 to 1.0
        
    Example:
        ('Santander', 'Chequing', 1.0)
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Get mapping from bank_mapping.csv to find module->bank/account relationships
    mapping_df = read_bank_mapping()
    module_to_bank_account = {}
    
    for _, row in mapping_df.iterrows():
        if pd.notna(row.get('Module')) and row.get('Input') == 'Transactions':
            module_to_bank_account[row['Module']] = (row['Bank'], row['Account'])
    
    best_match = None
    best_score = 0.0
    
    # Try each module signature
    for module_name, account_variants in MODULE_SIGNATURES.items():
        for account_type, signature in account_variants.items():
            # STRICT CHECK 1: File extension must match exactly
            if file_ext not in signature.get('file_extensions', []):
                continue
            
            # Try to read file header with this signature's parameters
            df_header = read_file_header(
                file_path,
                skiprows=signature.get('skiprows', 0),
                usecols=signature.get('usecols')
            )
            
            if df_header is None or df_header.empty:
                continue
            
            required_cols = signature.get('required_columns', [])
            if not required_cols:
                continue
            
            # STRICT CHECK 2: Column count must match exactly
            if len(df_header.columns) != len(required_cols):
                continue
            
            # STRICT CHECK 3: Column names must match exactly (in order, case-insensitive)
            columns_match = check_column_match(
                df_header.columns.tolist(), 
                required_cols,
                strict=True
            )
            
            if columns_match:
                # Found a match - get bank/account from mapping
                if module_name in module_to_bank_account:
                    bank, account = module_to_bank_account[module_name]
                    best_match = (bank, account, 1.0)
                    return best_match
    
    return None


def detect_all_files(file_paths: List[str]) -> Dict[str, Optional[Tuple[str, str, float]]]:
    """
    Detect Bank+Account pairs for multiple files.
    
    Args:
        file_paths: List of file paths to analyze
        
    Returns:
        Dictionary mapping file_path -> (bank, account, confidence) or None
    """
    results = {}
    for file_path in file_paths:
        results[file_path] = detect_bank_account_pair(file_path)
    return results


def get_module_signature_info(bank: str, account: str) -> Optional[Dict]:
    """
    Get the file format signature for a Bank+Account combination.
    Useful for providing hints to users about expected file format.
    
    Args:
        bank: Bank name
        account: Account type
        
    Returns:
        Dictionary with signature info, or None if not found
    """
    mapping_df = read_bank_mapping()
    row = mapping_df[(mapping_df['Bank'] == bank) & 
                     (mapping_df['Account'] == account) & 
                     (mapping_df['Input'] == 'Transactions')]
    
    if row.empty:
        return None
    
    module_name = row.iloc[0].get('Module')
    if pd.isna(module_name):
        return None
    
    # Find in signatures
    for mod_name, accounts in MODULE_SIGNATURES.items():
        if mod_name == module_name:
            for acc_type, sig in accounts.items():
                if acc_type == account or (acc_type in account):
                    return {
                        'module': module_name,
                        'account_type': acc_type,
                        'file_extensions': sig.get('file_extensions', []),
                        'required_columns': sig.get('required_columns', []),
                        'description': sig.get('description', '')
                    }
    
    return None
