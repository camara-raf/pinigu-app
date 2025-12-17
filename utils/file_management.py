"""
Utility functions for managing uploaded source files and reading transactions.
Handles Excel file parsing, metadata extraction, and file deletion.
"""
import pandas as pd
import os
import shutil
from datetime import datetime
from .raw_file_reader import RawFileReader
from .logger import get_logger

logger = get_logger()

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
    """
    df = pd.read_csv(BANK_MAPPING_FILE)
    transaction_rows = df[df['Input'] == 'Transactions']
    return list(zip(transaction_rows['Bank'], transaction_rows['Account']))


def get_accounts_for_bank(bank):
    """
    Get list of accounts for a specific bank that support file uploads.
    """
    df = pd.read_csv(BANK_MAPPING_FILE)
    transaction_rows = df[(df['Input'] == 'Transactions') & (df['Bank'] == bank)]
    return transaction_rows['Account'].tolist()


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
        logger.error(f"Error writing file: {uploaded_file.name} -> {e}")
        return None

    logger.info(f"File saved: {output_path}")
    return output_path

def parse_multiple_files(file_list, bank, account):
    """
    Parse multiple files for a Bank+Account using RawFileReader.
    """
    reader = RawFileReader()
        
    # Let's resolve valid paths.
    valid_paths = []
    for f in file_list:
        if os.path.exists(f):
            valid_paths.append(f)
        else:
            # Check in temp dir
            temp_path = os.path.join(RAW_FILES_DIR, 'temp', os.path.basename(f))
            if os.path.exists(temp_path):
                valid_paths.append(temp_path)
            else:
                 # Check current dir (legacy)
                if os.path.exists(os.path.basename(f)):
                     valid_paths.append(os.path.abspath(os.path.basename(f)))
                else: 
                     logger.warning(f"Warning: File not found {f}")

    df = reader.read_files(valid_paths, bank, account)
    return df

def parse_excel_file(file_path, bank, account, temp=False):
    """
    Parse a single file using RawFileReader.
    Returns (dataframe, summary_dataframe).
    """
    if temp:
        # file_path is UploadedFile
        logger.info(f"Saving file to temp directory...")
        temp_file = write_raw_file(file_path, bank)
        if temp_file is None:
            raise ValueError(f"Error writing file: {file_path.name}")
        file_path_str = temp_file
    else:
        file_path_str = file_path

    reader = RawFileReader()
    # read_files expects list
    df = reader.read_files([file_path_str], bank, account)
    
    # Create summary
    if not df.empty:
         oldest = df['Transaction Date'].min().strftime('%Y-%m-%d')
         newest = df['Transaction Date'].max().strftime('%Y-%m-%d')
    else:
         oldest = None
         newest = None

    df_file_summary = pd.DataFrame([{
        'File Name': os.path.basename(file_path_str),
        'Bank': bank,
        'Account': account,
        'Upload Date': datetime.today().strftime("%Y-%m-%d %H:%M"),
        'Oldest Date': oldest,
        'Newest Date': newest
    }])

    return df, df_file_summary

def load_consolidated_data():
    """Load consolidated transactions from CSV."""
    if os.path.exists(CONSOLIDATED_FILE):
        df = pd.read_csv(CONSOLIDATED_FILE,keep_default_na=False,na_values=['NaN'])
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        logger.info(f"Loaded {len(df)} transactions from consolidated file")
        return df
    return pd.DataFrame(columns=['Transaction Date', 'Bank', 'Account', 'Transaction', 'Type', 
                                 'Amount', 'Effective Date', 'Balance', 'Category', 'Sub-Category', 'Source_File'])

def save_consolidated_data(df):
    """Save consolidated data to CSV."""
    logger.info(f"Saving consolidated data")
    df.to_csv(CONSOLIDATED_FILE, index=False)

def get_uploaded_files_info():
    """Get information about uploaded files from files_summary.csv."""
    try:
        df = pd.read_csv(FILES_SUMMARY_FILE)
        return df.to_dict('records')
    except FileNotFoundError:
        return []

def delete_uploaded_file(filename):
    """Delete an uploaded file and remove it from the summary."""
    deleted = False
    
    # Try temp dir
    file_path = os.path.join(RAW_FILES_DIR, 'temp', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        deleted = True
    
    # Try current dir (legacy)
    if not deleted and os.path.exists(filename):
        os.remove(filename)
        deleted = True
        
    # Remove from summary file regardless of whether physical file existed
    # (sometimes user might want to clean up ghost entries)
    try:
        if os.path.exists(FILES_SUMMARY_FILE):
            df = pd.read_csv(FILES_SUMMARY_FILE)
            # Remove rows matching filename
            df = df[df['File Name'] != filename]
            df.to_csv(FILES_SUMMARY_FILE, index=False)
            logger.info(f"Removed {filename} from {FILES_SUMMARY_FILE}")
    except Exception as e:
        logger.error(f"Error updating file summary for deletion: {e}")
        
    return deleted

def read_bank_mapping():
    """Read bank mapping file."""
    return pd.read_csv(BANK_MAPPING_FILE)

def update_file_summary(df, replace=False):
    try:
        if replace:
            df.to_csv(FILES_SUMMARY_FILE, index=False)
            return
        df['Processed'] = "No"
        try:
            df_summary = pd.read_csv(FILES_SUMMARY_FILE)
            df_summary = pd.concat([df_summary, df], ignore_index=True)
            df_summary.sort_values(by='Upload Date', ascending=False, inplace=True)
            df_summary.drop_duplicates(subset=['File Name', 'Bank', 'Account', 'Oldest Date', 'Newest Date'], keep='first', inplace=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_summary = df
            
        df_summary.to_csv(FILES_SUMMARY_FILE, index=False)
    except Exception as e:
        logger.error(f"Error updating file summary: {e}")
