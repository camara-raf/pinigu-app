import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from utils.categorization import load_mapping_rules, add_mapping_rule

def verify():
    print("Verifying load_mapping_rules...")
    rules = load_mapping_rules()
    print(f"Loaded {len(rules)} rules.")
    print("Columns:", rules.columns.tolist())
    
    if 'Category' not in rules.columns or 'Pair_ID' not in rules.columns:
        print("FAIL: Missing expected columns.")
        return

    print("Sample rule:")
    print(rules.iloc[0].to_dict())

    print("\nVerifying add_mapping_rule...")
    # Try adding a rule with an existing pair
    existing_rule = rules.iloc[0]
    cat = existing_rule['Category']
    sub = existing_rule['Sub-Category']
    direction = existing_rule['Direction']
    
    new_pattern = "TEST_PATTERN_EXISTING_PAIR"
    try:
        new_id = add_mapping_rule(new_pattern, cat, sub, direction)
        print(f"Added rule {new_id} with existing pair.")
    except Exception as e:
        print(f"FAIL: Failed to add rule with existing pair: {e}")

    # Try adding a rule with a NEW pair
    new_pattern_2 = "TEST_PATTERN_NEW_PAIR"
    new_cat = "NewCategory"
    new_sub = "NewSubCategory"
    new_dir = "Out"
    
    try:
        new_id_2 = add_mapping_rule(new_pattern_2, new_cat, new_sub, new_dir)
        print(f"Added rule {new_id_2} with NEW pair.")
    except Exception as e:
        print(f"FAIL: Failed to add rule with new pair: {e}")

    # Verify persistence
    rules_reloaded = load_mapping_rules()
    
    r1 = rules_reloaded[rules_reloaded['Pattern'] == new_pattern]
    if not r1.empty:
        print(f"Verified rule 1: {r1.iloc[0]['Category']} / {r1.iloc[0]['Sub-Category']}")
    else:
        print("FAIL: Rule 1 not found.")

    r2 = rules_reloaded[rules_reloaded['Pattern'] == new_pattern_2]
    if not r2.empty:
        print(f"Verified rule 2: {r2.iloc[0]['Category']} / {r2.iloc[0]['Sub-Category']}")
    else:
        print("FAIL: Rule 2 not found.")

    # Cleanup
    from utils.categorization import delete_mapping_rule
    if 'new_id' in locals(): delete_mapping_rule(new_id)
    if 'new_id_2' in locals(): delete_mapping_rule(new_id_2)
    print("Cleanup done.")

if __name__ == "__main__":
    verify()
