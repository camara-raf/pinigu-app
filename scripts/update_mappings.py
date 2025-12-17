import pandas as pd
import os

def main():
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mapped_categories_path = os.path.join(base_dir, 'data', 'mapped_categories.csv')
    mapping_rules_path = os.path.join(base_dir, 'data', 'mapping_rules.csv')
    mapping_pairs_path = os.path.join(base_dir, 'data', 'mapping_pairs.csv')

    # Read mapped_categories.csv
    # Default pandas behavior handles standard None/NaN values correctly
    df_mapped = pd.read_csv(mapped_categories_path,keep_default_na=False,na_values=['NaN'])

    # ---------------------------------------------------------
    # Task A: Update mapping_rules.csv IDs
    # ---------------------------------------------------------
    
    # 1) Identify rows where Old_id is not null or empty string
    # Ensure Old_id is treated as numeric/object that can be NaN, dropna removes NaNs
    # With keep_default_na=False, we must also filter out empty strings
    updates = df_mapped[df_mapped['Old_id'].notna() & (df_mapped['Old_id'] != '')].copy()
    
    if not updates.empty:
        # Create a dictionary for mapping: Old_id -> New_id
        # Ensure IDs are integers for robust matching if they look like floats (e.g. 1.0)
        try:
            updates['Old_id'] = updates['Old_id'].astype(float).astype(int)
            updates['new_id'] = updates['new_id'].astype(float).astype(int)
            id_map = dict(zip(updates['Old_id'], updates['new_id']))
            
            # Read mapping_rules.csv
            df_rules = pd.read_csv(mapping_rules_path,keep_default_na=False,na_values=['NaN'])
            
            # 2 & 3) Find rows in mapping_rules using old pair id and replace with new pair id
            # We map Pair_ID using the id_map. If not found in map, keep original.
            # Using simple replacement
            
            # First ensure Pair_ID is same type (int) if possible to match keys
            # Handle potential NaNs in Pair_ID just in case, though unlikely for IDs
            if df_rules['Pair_ID'].dtype == float:
                 df_rules['Pair_ID'] = df_rules['Pair_ID'].fillna(-1).astype(int)

            # Apply mapping
            # map() with fillna won't work easily if we want to keep original values that aren't in the map
            # replace() is better suited
            df_rules['Pair_ID'] = df_rules['Pair_ID'].replace(id_map)
            
            # Ensure Pair_ID is exported as integer (no decimals)
            df_rules['Pair_ID'] = df_rules['Pair_ID'].astype(int)
            
            # Write back to mapping_rules.csv
            df_rules.to_csv(mapping_rules_path, index=False)
            print(f"Updated {mapping_rules_path}")

        except Exception as e:
            print(f"Error updating mapping_rules.csv: {e}")
            exit(1)
    else:
        print("No updates found for mapping_rules.csv (no non-null Old_id).")

    # ---------------------------------------------------------
    # Task B: Update mapping_pairs.csv with only new ids
    # ---------------------------------------------------------
    
    # 1) Get distinct rows of new_* columns
    new_cols = ['new_id', 'new_category', 'new_subcategory', 'new_direction']
    df_pairs_new = df_mapped[new_cols].drop_duplicates()
    
    # Rename columns to match mapping_pairs.csv headers: Pair_ID,Category,Sub-Category,Direction
    df_pairs_new = df_pairs_new.rename(columns={
        'new_id': 'Pair_ID',
        'new_category': 'Category',
        'new_subcategory': 'Sub-Category',
        'new_direction': 'Direction'
    })
    
    # Handle NaNs in Pair_ID if any (shouldn't be based on logic, but for safety)
    df_pairs_new = df_pairs_new.dropna(subset=['Pair_ID'])
    
    # 2) Sort rows by id
    df_pairs_new['Pair_ID'] = df_pairs_new['Pair_ID'].astype(float).astype(int)
    df_pairs_new = df_pairs_new.sort_values(by='Pair_ID')
    
    # 3) Overwrite content of mapping_pairs.csv
    df_pairs_new.to_csv(mapping_pairs_path, index=False)
    print(f"Updated {mapping_pairs_path}")

if __name__ == "__main__":
    main()
