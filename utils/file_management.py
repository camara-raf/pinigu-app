"""
Utility functions for managing uploaded source files and reading transactions.
Handles Excel file parsing, metadata extraction, and file deletion.

Module Registration:
Modules must return a tuple of (dataframe, summary_dataframe) where:
- dataframe: Contains columns [Transaction Date, Effective Date, Transaction, Type, Amount, 
             Effective Date, Category, Sub-Category, Source_File, Bank, Account]
- summary_dataframe: Contains columns [File Name, Oldest Date, Newest Date]

New bank onboarding:
1. Add row to bank_mapping.csv with Input='Transactions' and Module column set to 'module_name.function_name'
2. Create module in management/ folder implementing the read function
3. Module must return tuple (dataframe, summary_dataframe) as described above
"""
import pandas as pd
import os
import importlib
from datetime import datetime
#from management import santander, bbva
#from management.santander import readSantander
#from management.bbva import readBBAFiles

DATA_DIR = "data"
RAW_FILES_DIR = os.path.join(DATA_DIR, "raw_files")
CONSOLIDATED_FILE = os.path.join(DATA_DIR, "consolidated_transactions.csv")
FILES_SUMMARY_FILE = os.path.join(DATA_DIR, "files_summary.csv")
BANK_MAPPING_FILE = os.path.join(DATA_DIR, "bank_mapping.csv")

# Ensure directories exist
os.makedirs(RAW_FILES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def get_transaction_capable_banks():
    """
    Get list of banks/accounts that can have files uploaded (Input='Transactions').
    
    Returns:
        list: Tuples of (Bank, Account) combinations that support file uploads
    """
    df = pd.read_csv(BANK_MAPPING_FILE)
    transaction_rows = df[df['Input'] == 'Transactions']
    return list(zip(transaction_rows['Bank'], transaction_rows['Account']))


def get_accounts_for_bank(bank):
    """
    Get list of accounts for a specific bank that support file uploads.
    
    Args:
        bank (str): Bank name
        
    Returns:
        list: Account names for the given bank with Input='Transactions'
    """
    df = pd.read_csv(BANK_MAPPING_FILE)
    transaction_rows = df[(df['Input'] == 'Transactions') & (df['Bank'] == bank)]
    return transaction_rows['Account'].tolist()


def get_module_info(bank, account):
    """
    Get module information for a bank/account combination.
    
    Args:
        bank (str): Bank name
        account (str): Account type
        
    Returns:
        dict: Dictionary with keys 'module_path', 'function_name', 'bank_id', or None if not found
        
    Raises:
        ValueError: If bank/account combination is not transaction-capable
    """
    df = pd.read_csv(BANK_MAPPING_FILE)
    row = df[(df['Input'] == 'Transactions') & (df['Bank'] == bank) & (df['Account'] == account)]
    
    if row.empty:
        raise ValueError(f"Bank/account combination '{bank}/{account}' is not transaction-capable or does not exist")
    
    module_str = row.iloc[0]['Module']
    if pd.isna(module_str) or module_str == '':
        raise ValueError(f"No module configured for {bank}/{account}")
    
    parts = module_str.rsplit('.', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid module format '{module_str}'. Expected 'module_name.function_name'")
    
    return {
        'module_path': 'management' + '.' + parts[0],
        'function_name': parts[1],
        'bank_id': row.iloc[0]['Bank_ID']
    }


def call_bank_module(module_path, function_name, file_path, account):
    """
    Dynamically import and call a bank module function.
    
    Args:
        module_path (str): Module path (e.g., 'management.santander')
        function_name (str): Function name (e.g., 'readSantander')
        file_path (str): Path to the file to parse
        
    Returns:
        tuple: (dataframe, summary_dataframe) from the module
        
    Raises:
        Exception: If module import or function call fails
    """
    try:
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        
        # Call function with single_file parameter for the common pattern
        # Different modules may accept different parameters
        result = func(single_file=file_path, account=account)
        
        if not isinstance(result, tuple) or len(result) != 2:
            raise ValueError(f"Module {module_path}.{function_name} must return tuple of (dataframe, summary_dataframe)")
        
        return result
    except ImportError as e:
        raise Exception(f"Cannot import module '{module_path}': {str(e)}")
    except AttributeError as e:
        raise Exception(f"Module '{module_path}' does not have function '{function_name}'")
    except TypeError as e:
        # If single_file parameter fails, it might be a module that needs special handling
        raise Exception(f"Error calling {module_path}.{function_name}: {str(e)}")


def write_raw_file(uploaded_file, bank):
    """
    Save a Streamlit UploadedFile object to disk.
    Returns the full output path, or None if error.
    """
    # Build output directory
    file_dir = os.path.join(RAW_FILES_DIR, 'temp')

    try:
        os.makedirs(file_dir, exist_ok=True)

        # Full path for saving the file
        output_path = os.path.join(file_dir, uploaded_file.name)

        # Write bytes from Streamlit uploaded file
        with open(output_path, "wb") as f:
            f.write(uploaded_file.getvalue())

    except Exception as e:
        print(f"Error writing file: {uploaded_file.name} -> {e}")
        return None

    print(f"File saved: {output_path}")
    return output_path

def parse_multiple_files(file_list, bank, account):
    dfs = []
    for file_path in file_list:
        print(f"Multiple func: Parsing file: {file_path}")
        df, df_summary = parse_excel_file(file_path, bank, account)
        dfs.append(df)
    concat_df = pd.concat(dfs)
    
    #concat_df = concat_df.drop_duplicates(subset=concat_df.columns.difference(['FileName']), keep='first')
    return concat_df

def parse_excel_file(file_path, bank, account, temp=False):
    """
    Parse Excel file and return standardized dataframe.
    Dynamically loads the module specified in bank_mapping.csv Module column.
    
    Args:
        file_path: Path to the file or Streamlit UploadedFile object
        bank: Bank name (must match bank_mapping.csv)
        account: Account type (must match bank_mapping.csv)
        temp: If True, saves file to temp directory first
    
    Returns:
        tuple: (dataframe, summary_dataframe) with standardized columns
        
    Raises:
        ValueError: If bank/account combination is invalid or file has errors
    """
    try:
        # Validate bank/account combination exists and get module info
        module_info = get_module_info(bank, account)
        
        if temp:
            print(f"Saving file to temp directory...")
            temp_file = write_raw_file(file_path, bank)
            if temp_file is None:
                raise ValueError(f"Error writing file: {file_path.name}")
            file_path = temp_file
        
        print(f"Parsing file: {file_path} for {bank}/{account}")
        
        # Dynamically call the module function
        df_transactions, df_file_summary = call_bank_module(
            module_info['module_path'],
            module_info['function_name'],
            file_path,
            account=account
        )
        
        df = df_transactions
              
        # Map columns to standard format
        df['Type'] = df['Amount'].apply(lambda x: 'In' if x > 0 else 'Out')
       
        # Ensure Transaction Date is datetime
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])

        df['Category'] = 'Uncategorized'
        df['Sub-Category'] = 'Uncategorized'

        # Select only required columns
        required_cols = ['Transaction Date', 'Bank', 'Account', 'Transaction', 'Type', 
                        'Amount', 'Effective Date', 'Balance', 'Category', 'Sub-Category', 'Source_File']
        df = df[required_cols]

        df_file_summary['Bank'] = bank
        df_file_summary['Account'] = account
        df_file_summary['Upload Date'] = datetime.today().strftime("%Y-%m-%d %H:%M")
        df_file_summary['Oldest Date'] = df_file_summary['Oldest Date'].dt.strftime('%Y-%m-%d')
        df_file_summary['Newest Date'] = df_file_summary['Newest Date'].dt.strftime('%Y-%m-%d')

        return df, df_file_summary
    except Exception as e:
        raise Exception(f"Error parsing file: {str(e)}")

def load_consolidated_data():
    """Load consolidated transactions from CSV."""
    if os.path.exists(CONSOLIDATED_FILE):
        df = pd.read_csv(CONSOLIDATED_FILE,keep_default_na=False,na_values=['NaN'])
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        return df
    return pd.DataFrame(columns=['Transaction Date', 'Bank', 'Account', 'Transaction', 'Type', 
                                 'Amount', 'Effective Date', 'Balance', 'Category', 'Sub-Category', 'Source_File'])

def save_consolidated_data(df):
    """Save consolidated data to CSV."""
    df.to_csv(CONSOLIDATED_FILE, index=False)

def get_uploaded_files_info():
    """Get information about uploaded files from files_summary.csv."""
    try:
        df = pd.read_csv(FILES_SUMMARY_FILE)
        return df.to_dict('records')
    except FileNotFoundError:
        return []

def delete_uploaded_file(filename):
    """Delete an uploaded file."""
    file_path = os.path.join(RAW_FILES_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def read_bank_mapping():
    """Read bank mapping file."""
    return pd.read_csv(BANK_MAPPING_FILE)

def update_file_summary(df, replace=False):
    try:
        if replace:
            df.to_csv(FILES_SUMMARY_FILE, index=False)
            return
        df['Processed'] = "No"
        df_summary = pd.read_csv(FILES_SUMMARY_FILE)
        df_summary = pd.concat([df_summary, df], ignore_index=True)
        df_summary.sort_values(by='Upload Date', ascending=False, inplace=True)
        df_summary.drop_duplicates(subset=['File Name', 'Bank', 'Account', 'Oldest Date', 'Newest Date'], keep='first', inplace=True)
        df_summary.to_csv(FILES_SUMMARY_FILE, index=False)
    except FileNotFoundError:
        df.to_csv(FILES_SUMMARY_FILE, index=False)

