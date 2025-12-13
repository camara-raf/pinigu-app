import pandas as pd
from datetime import datetime, timedelta

# Read CSV file
input_file = 'wise_statement.csv'  # Change this to your filename
df = pd.read_csv(input_file)

# Keep only required columns
df = df[['Date', 'DateTime', 'Currency', 'Running Balance EUR']]

# Convert DateTime to proper datetime format
df['DateTime'] = pd.to_datetime(df['DateTime'], format='%d/%m/%Y %H:%M:%S.%f')
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

# Sort by DateTime (oldest first)
df = df.sort_values('DateTime').reset_index(drop=True)

# Find max date in dataset
max_date = df['Date'].max()

# Fill date gaps by currency
filled_dfs = []
for currency in df['Currency'].unique():
    curr_df = df[df['Currency'] == currency].copy()
    
    # Get date range from first to max date
    min_date = curr_df['Date'].min()
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # Create complete date range dataframe
    complete_df = pd.DataFrame({'Date': date_range})
    complete_df['Currency'] = currency
    
    # Merge with existing data
    merged = complete_df.merge(curr_df, on=['Date', 'Currency'], how='left')
    
    # Forward fill the Running Balance EUR
    merged['Running Balance EUR'] = merged['Running Balance EUR'].fillna(method='ffill')
    merged['DateTime'] = merged['DateTime'].fillna(method='ffill')
    
    filled_dfs.append(merged)

# Combine all currencies
df_filled = pd.concat(filled_dfs, ignore_index=True)

# Extract month-year for grouping
df_filled['MonthYear'] = df_filled['Date'].dt.to_period('M')

# Get latest row per month per currency
monthly_latest = df_filled.groupby(['Currency', 'MonthYear']).tail(1)

# Pivot to get CAD and EUR columns
pivot = monthly_latest.pivot_table(
    index='MonthYear',
    columns='Currency',
    values='Running Balance EUR',
    aggfunc='sum'
).reset_index()

# Calculate grand total
pivot['Grand Total'] = pivot[['CAD', 'EUR']].sum(axis=1)

# Rename columns
pivot.columns.name = None
pivot = pivot.rename(columns={'MonthYear': 'Month-Year'})

# Convert Month-Year to string format
pivot['Month-Year'] = pivot['Month-Year'].astype(str)

# Fill NaN with 0 for missing currencies
pivot = pivot.fillna(0)

# Convert Month-Year to Year-Month-LatestDate of Month
pivot['Month-Year'] = pivot['Month-Year'].apply(lambda x: pd.Period(x, freq='M').end_time.strftime('%Y-%m-%d'))
pivot.insert(0, 'Bank', 'Wise')
pivot.insert(1, 'Account', 'Chequing-Rafa')
pivot['ImportDate'] = '2025-12-13 20:45:11'

# Display results
print(pivot)

# Save to CSV
output_file = 'monthly_totals.csv'
#drop the CAD and EUR columns
pivot = pivot.drop(columns=['CAD', 'EUR'])
pivot['Empty1'] = ''
pivot['Empty2'] = ''

pivot.to_csv(output_file, index=False)
print(f"\nResults saved to {output_file}")