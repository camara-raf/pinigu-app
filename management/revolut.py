import pandas as pd
import os

def readRevolut(account=None, dir_path='./', single_file=None, file_list=None):
    print("Reading Revolut files...")
    
    # Create an empty list to store the dataframes
    dfs = []
    df_files_summary = pd.DataFrame(columns=['File Name', 'Oldest Date', 'Newest Date'])

    # Determine which files to read
    if single_file is not None:
        csv_files = [single_file]
    elif file_list is not None:
        csv_files = file_list
    else:
        # List all CSV files in the directory
        csv_files = sorted([file for file in os.listdir(dir_path) if file.endswith('.csv')], reverse=True)

    for file_name in csv_files:
        print(f'Revolut: Reading file: {file_name}')
        file_path = os.path.join(dir_path, file_name)
        
        try:
            df = pd.read_csv(file_path)
            
            # Ensure required columns exist
            required_cols = ['Type', 'Product', 'Started Date', 'Completed Date', 'Description', 'Amount', 'Balance']
            if not all(col in df.columns for col in required_cols):
                print(f"Skipping {file_name}: Missing required columns")
                continue

            # Parse dates and normalize to date-only format (keep as datetime for compatibility)
            df['Started Date'] = pd.to_datetime(df['Started Date']).dt.normalize()
            df['Completed Date'] = pd.to_datetime(df['Completed Date']).dt.normalize()
            
            # Construct Transaction column
            # Type | Product | Description
            df['Transaction'] = df['Type'].astype(str) + " | " + df['Product'].astype(str) + " | " + df['Description'].astype(str)
            
            # Rename columns
            df = df.rename(columns={
                'Started Date': 'Transaction Date',
                'Completed Date': 'Effective Date',
                # Amount and Balance are already named correctly
            })
            
            # Add metadata
            df['FileName'] = os.path.basename(file_name)
            
            # Update summary
            if not df.empty:
                new_summary = pd.DataFrame({
                    'File Name': [os.path.basename(file_name)],
                    'Oldest Date': [df['Transaction Date'].min()],
                    'Newest Date': [df['Transaction Date'].max()]
                })
                df_files_summary = pd.concat([df_files_summary, new_summary], ignore_index=True)
            
            dfs.append(df)
            
        except Exception as e:
            print(f"Error reading {file_name}: {e}")

    if not dfs:
        return pd.DataFrame(), df_files_summary

    # Concatenate all dataframes
    result = pd.concat(dfs, ignore_index=True)
    
    # Select and order final columns
    # Expected: Transaction Date, Effective Date, Transaction, Amount, Balance, Source_File
    result = result[['Transaction Date', 'Effective Date', 'Transaction', 'Amount', 'Balance', 'FileName']]
    result.columns = ['Transaction Date', 'Effective Date', 'Transaction', 'Amount', 'Balance', 'Source_File']
    
    # Add Bank and Account info
    result['Bank'] = 'Revolut'
    result['Account'] = 'Revolut ' + (account if account else '')
    
    return result, df_files_summary
