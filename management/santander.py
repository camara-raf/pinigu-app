import pandas as pd
import os
import xlrd


def readSantanderChequing(account = "Chequing", dir_path = './', single_file = None, file_list = None):
    print("Reading Santander Chequing files...")
    usecols = "A:E"
    return readSantander(account = account, dir_path = dir_path, single_file = single_file, file_list = file_list, usecols = usecols)

def readSantanderCredit(account = "Credit", dir_path = './', single_file = None, file_list = None):
    print("Reading Santander Credit files...")
    usecols = "A:C"
    return readSantander(account = account, dir_path = dir_path, single_file = single_file, file_list = file_list, usecols = usecols)

def readSantander(account = None, dir_path = './', single_file = None, file_list = None, usecols = None):
    # Create an empty list to store the dataframes
    dfs = []

    df_files_summary = pd.DataFrame(columns=['File Name','Oldest Date','Newest Date'])

    # If a filename was provided, use only that file
    if single_file is not None:
        excel_files = [single_file]
    elif file_list is not None:
        excel_files = file_list
    else:
        # Excel files to read
        excel_files = sorted([file for file in os.listdir(dir_path) if file.endswith('.xls')], reverse=True)

    # Loop over all the files in the directory with the .xlsx extension
    for file_name in excel_files:

        # Read in the Excel file as a Pandas dataframe, skipping the first 4 rows and the first column
        print('Santander: Reading file: {0}'.format(file_name))
        df = pd.read_excel(os.path.join(dir_path, file_name), sheet_name=0, skiprows=7, usecols=usecols)
        # Get the name of the first (and only) sheet in the Excel file

        # Reset the index of the dataframe
        df.reset_index(drop=True, inplace=True)

        # Convert "Date" column from datetime to date only format
        df['FECHA OPERACIÓN'] = pd.to_datetime(df['FECHA OPERACIÓN'], format='%d/%m/%Y')
        if account == "Chequing":
            df['FECHA VALOR'] = pd.to_datetime(df['FECHA VALOR'], format='%d/%m/%Y')
        if account == "Credit":
            df['FECHA VALOR'] = df['FECHA OPERACIÓN']
            df['SALDO'] = '0'
        
        df['FileName'] = os.path.basename(file_name) if isinstance(file_name, str) else file_name

        if df_files_summary.empty:
            df_files_summary = pd.DataFrame({'File Name': [file_name], 'Oldest Date': [df['FECHA OPERACIÓN'].min()], 'Newest Date': [df['FECHA OPERACIÓN'].max()]})
        else:
            df_files_summary = pd.concat([df_files_summary, pd.DataFrame({'File Name': [file_name], 'Oldest Date': [df['FECHA OPERACIÓN'].min()], 'Newest Date': [df['FECHA OPERACIÓN'].max()]})], ignore_index=True)
        
        # Append the dataframe to the list of dataframes
        dfs.append(df)

    # Concatenate all the dataframes into a single dataframe
    result = pd.concat(dfs, ignore_index=True, verify_integrity=True)

    #result.drop_duplicates(subset=result.columns.difference(['FileName']), inplace=True, keep='first')

    result = result.loc[:, ['FECHA OPERACIÓN', 'FECHA VALOR', 'CONCEPTO', 'IMPORTE EUR', 'SALDO', 'FileName']]
    result.columns = ['Transaction Date','Effective Date','Transaction','Amount','Balance','Source_File']
    result['Account'] = 'Santander ' + account
    result['Bank'] = 'Santander'

    return result.reset_index(drop=True), df_files_summary
