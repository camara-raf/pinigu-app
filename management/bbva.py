import pandas as pd
import os

def readBBVA(account = None, dir_path = './', single_file = None, file_list = None):

    print('BBVA Reading files', 'Single File' if single_file else 'File List' if file_list else 'Directory Scan')
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
        excel_files = sorted([file for file in os.listdir(dir_path) if file.endswith('.xlsx')], reverse=True)

    #Excel files tos read
    #excel_files = sorted([file for file in os.listdir(dir_path) if file.endswith('.xlsx')], reverse=True)
    
    # Loop over all the files in the directory with the .xlsx extension
    for file_name in excel_files:

        # Read in the Excel file as a Pandas dataframe, skipping the first 4 rows and the first column
        print('BBVA Reading file: {0}'.format(file_name))
        #df = pd.read_excel(os.path.join(dir_path, file_name), sheet_name=None, skiprows=4, usecols=lambda x: x != 0)
        df = pd.read_excel(os.path.join(dir_path, file_name), sheet_name=0, skiprows=4, usecols="B:J")
        #print(df.columns)
        # Get the name of the first (and only) sheet in the Excel file
        #sheet_name = list(df.keys())[0]

        # Reset the index of the dataframe
        df.reset_index(drop=True, inplace=True)

        # Ensure 'Fecha' and 'F.Valor' are read as strings first to handle "DD/MM/YYYY" if not standard Excel date format
        # Then convert them to datetime objects, specifying the format if necessary.
        # The subsequent lines already convert to datetime, so this step ensures they are parsed correctly.
        # If the columns are already parsed correctly by read_excel as datetime, these lines will re-convert but safely.
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        df['F.Valor'] = pd.to_datetime(df['F.Valor'], format='%d/%m/%Y', errors='coerce')

        df['FileName'] = os.path.basename(file_name) if isinstance(file_name, str) else file_name

        df_files_summary = pd.concat([df_files_summary, pd.DataFrame({'File Name': [file_name], 'Oldest Date': [df['Fecha'].min()], 'Newest Date': [df['Fecha'].max()]})], ignore_index=True)

        # Append the dataframe to the list of dataframes
        dfs.append(df)

    # Concatenate all the dataframes into a single dataframe
    result = pd.concat(dfs, ignore_index=True, verify_integrity=True)

    result['Transaction'] = result['Concepto'] + ' | ' + result['Observaciones'].astype(str)
    # Drop a1ny duplicate rows, ignoring the index
    result.drop_duplicates(subset=result.columns.difference(['index','Transaction']), inplace=True, keep='last')
    result = result.loc[:, ['F.Valor','Fecha', 'Transaction','Importe','Disponible','FileName']]
    result.columns = ['Transaction Date','Effective Date','Transaction','Amount','Balance','Source_File']
    result['Account'] = 'BBVA ' + account
    result['Bank'] = 'BBVA'
    #print(result.dtypes)
    return result.reset_index(drop=True), df_files_summary