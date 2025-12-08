"""
Utility functions for consolidating raw transaction data from multiple sources.
Handles combining, deduplicating, and applying categorization to transactions.
Includes support for non-transaction (balance-based) accounts with transfer capture and synthetic transaction generation.
"""
import pandas as pd
import os
from .transaction_keys import create_transaction_key
from .categorization import apply_categorization
from .file_management import FILES_SUMMARY_FILE, parse_multiple_files, update_file_summary
from .non_transaction_logic import get_captured_transactions, get_synthetic_transactions


def ingest_transactions(incremental=False):
    """
    Step 1: Ingest raw files.
    Reads raw files from disk.
    If incremental=True, only reads files not already in the summary (TODO: implement incremental logic fully).
    Currently reads all files as per original logic, but returns the raw dataframe.
    """
    print("Step 1: Ingesting transactions...")
    all_dfs = []
    
    # Read files summary
    files_summary_df = pd.read_csv(FILES_SUMMARY_FILE)
    grouped_files = files_summary_df.groupby(['Bank', 'Account'])['File Name'].apply(list).reset_index(name='FileNames')

    # Track which files were actually processed
    processed_files = []
    
    # TODO: Implement true incremental loading here by filtering out already processed files
    # For now, we follow the original pattern of reading everything defined in the summary
    
    for index, row in grouped_files.iterrows():
        print(f"Reading files for {row['Bank']} {row['Account']}:Files: { row['FileNames'] }")
        all_dfs.append(parse_multiple_files(row['FileNames'], row['Bank'], row['Account']))
        # Track these files as processed
        processed_files.extend(row['FileNames'])
    
    if not all_dfs:
        return pd.DataFrame(columns=['Transaction Date', 'Bank', 'Account', 'Transaction', 'Type', 
                                     'Amount', 'Effective Date', 'Category', 'Sub-Category', 'Source_File', 'Transaction_Source'])
    
    # Concatenate all dataframes
    raw_df = pd.concat(all_dfs, ignore_index=True)
    
    # Add Transaction_Source column for file-based transactions
    raw_df['Transaction_Source'] = 'File'
    
    # Create unique key for deduplication
    raw_df['_key'] = raw_df.apply(create_transaction_key, axis=1)
    
    # Remove duplicates (keep first occurrence)
    raw_df = raw_df.drop_duplicates(subset='_key', keep='first')
    
    # Drop the internal key column
    raw_df = raw_df.drop('_key', axis=1)
    
    # Update Processed flag ONLY for files that were actually read
    files_summary_df.loc[files_summary_df['File Name'].isin(processed_files), 'Processed'] = 'Yes'
    update_file_summary(files_summary_df, replace=True)
    
    print(f"Ingestion complete. Raw DF shape: {raw_df.shape}")
    return raw_df

def map_transactions(df):
    """
    Step 2: Map transactions.
    Applies categorization rules and manual overrides to the dataframe.
    """
    print("Step 2: Mapping transactions...")
    if df.empty:
        return df
        
    # Apply categorization
    mapped_df = apply_categorization(df)
    
    return mapped_df

def synthesize_transactions(df):
    """
    Step 3: Synthesize transactions.
    Generates captured and synthetic transactions based on the mapped data.
    """
    print("Step 3: Synthesizing transactions...")
    if df.empty:
        return df
        
    master_df = df.copy()
    
    # Generate captured transactions (mirrors of categorized transactions for non-transaction accounts)
    print("Generating captured transactions...")
    captured_df = get_captured_transactions(master_df)
    
    if not captured_df.empty:
        print(f"Generated {len(captured_df)} captured transactions")
        # Ensure all columns match
        for col in master_df.columns:
            if col not in captured_df.columns:
                captured_df[col] = None
        master_df = pd.concat([master_df, captured_df], ignore_index=True)
    
    # Generate synthetic balance-adjustment transactions
    print("Generating synthetic transactions...")
    synthetic_df = get_synthetic_transactions(master_df)
    
    if not synthetic_df.empty:
        print(f"Generated {len(synthetic_df)} synthetic transactions before deduplication")
        # Ensure all columns match
        for col in master_df.columns:
            if col not in synthetic_df.columns:
                synthetic_df[col] = None
        
        # Deduplicate synthetic transactions by key fields
        synthetic_df['_key'] = synthetic_df.apply(create_transaction_key, axis=1)
        synthetic_df = synthetic_df.drop_duplicates(subset='_key', keep='first')
        synthetic_df = synthetic_df.drop('_key', axis=1)
        
        print(f"Generated {len(synthetic_df)} synthetic transactions after deduplication")
        master_df = pd.concat([master_df, synthetic_df], ignore_index=True)
    
    # Sort by transaction date
    master_df = master_df.sort_values('Transaction Date', ascending=False)
    
    print(f"Synthesis complete. Final DF shape: {master_df.shape}")
    return master_df

def consolidate_data():
    """
    Legacy wrapper for full consolidation.
    Executes all 3 steps: Ingest -> Map -> Synthesize.
    """
    raw_df = ingest_transactions()
    mapped_df = map_transactions(raw_df)
    final_df = synthesize_transactions(mapped_df)
    return final_df


def extract_distinct_uncategorized_transactions(df=None):
    """Extract all distinct transaction values where category == 'Uncategorized'."""
    if df is None:
        from .file_management import load_consolidated_data
        df = load_consolidated_data()
    
    
    if df.empty:
        return pd.DataFrame(columns=['transaction'])
    
    uncategorized = df[df['Category'] == 'Uncategorized'].copy()
    
    if uncategorized.empty:
        return pd.DataFrame(columns=['transaction'])
    # Get counts, max dates, and avg amounts for distinct transactions
    result = uncategorized.groupby('Transaction').agg({
        'Transaction Date': ['count', 'max'],
        'Amount': 'mean'
    }).reset_index()
    result.columns = ['transaction', 'count', 'max_date', 'avg_amount']
    return result
