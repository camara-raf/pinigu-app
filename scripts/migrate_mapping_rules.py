import pandas as pd
import os
import shutil

MAPPING_RULES_FILE = "data/mapping_rules.csv"
MAPPING_PAIRS_FILE = "data/mapping_pairs.csv"
BACKUP_FILE = "data/mapping_rules.csv.bak"

def migrate():
    if not os.path.exists(MAPPING_RULES_FILE):
        print(f"File {MAPPING_RULES_FILE} not found.")
        return

    # Backup
    shutil.copy(MAPPING_RULES_FILE, BACKUP_FILE)
    print(f"Backed up {MAPPING_RULES_FILE} to {BACKUP_FILE}")

    df = pd.read_csv(MAPPING_RULES_FILE, keep_default_na=False, na_values=['NaN'])
    
    # Ensure columns exist
    required_cols = ['Category', 'Sub-Category', 'Direction']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''

    # Extract unique pairs
    pairs = df[required_cols].drop_duplicates().reset_index(drop=True)
    pairs['Pair_ID'] = pairs.index + 1
    
    # Save pairs
    pairs = pairs[['Pair_ID', 'Category', 'Sub-Category', 'Direction']]
    pairs.to_csv(MAPPING_PAIRS_FILE, index=False)
    print(f"Created {MAPPING_PAIRS_FILE} with {len(pairs)} pairs.")

    # Merge back to get Pair_ID in rules
    merged = pd.merge(df, pairs, on=['Category', 'Sub-Category', 'Direction'], how='left')
    
    # Select columns for new rules file
    new_rules_cols = ['Rule_ID', 'Pattern', 'Pair_ID', 'Priority', 'Is_Wildcard']
    # Ensure other columns are kept if they exist (though we are refactoring, let's stick to the plan)
    # The plan says: Rule_ID, Pattern, Pair_ID, Priority, Is_Wildcard
    
    new_rules = merged[new_rules_cols]
    new_rules.to_csv(MAPPING_RULES_FILE, index=False)
    print(f"Updated {MAPPING_RULES_FILE} with Pair_ID.")

if __name__ == "__main__":
    migrate()
