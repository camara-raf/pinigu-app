import pandas as pd
import os
from utils.manual_overrides import add_amount_override, load_amount_overwrites, remove_amount_override
from utils.categorization import apply_categorization

def test_amount_override():
    print("Testing Amount Override Logic...")
    
    # 1. Setup Data
    test_trans = "Test Transaction"
    test_amount = 123.45
    
    # Create a dummy dataframe
    df = pd.DataFrame([
        {'Transaction': test_trans, 'Amount': test_amount, 'Type': 'Out', 'Transaction Date': '2023-01-01', 'Bank': 'Test', 'Account': 'Test', 'Balance': 0},
        {'Transaction': test_trans, 'Amount': 999.99, 'Type': 'Out', 'Transaction Date': '2023-01-01', 'Bank': 'Test', 'Account': 'Test', 'Balance': 0}, # Different amount
        {'Transaction': "Other", 'Amount': test_amount, 'Type': 'Out', 'Transaction Date': '2023-01-01', 'Bank': 'Test', 'Account': 'Test', 'Balance': 0} # Different name
    ])
    
    # 2. Add Override
    print("Adding override...")
    add_amount_override(test_trans, test_amount, "Test Category", "Test Sub", "Out")
    
    # Verify it's loaded
    overwrites = load_amount_overwrites()
    key = (test_trans, test_amount)
    if key in overwrites:
        print("Override loaded successfully.")
    else:
        print("FAILED: Override not found in load_amount_overwrites.")
        return

    # 3. Apply Categorization
    print("Applying categorization...")
    result_df = apply_categorization(df)
    
    # Check Row 0 (Should match)
    row0 = result_df.iloc[0]
    if row0['Category'] == "Test Category" and row0['Sub-Category'] == "Test Sub":
        print("PASS: Row 0 correctly categorized.")
    else:
        print(f"FAIL: Row 0 category mismatch. Got {row0['Category']}/{row0['Sub-Category']}")

    # Check Row 1 (Should NOT match - diff amount)
    row1 = result_df.iloc[1]
    if row1['Category'] != "Test Category":
        print("PASS: Row 1 correctly NOT categorized (diff amount).")
    else:
        print(f"FAIL: Row 1 incorrectly categorized.")

    # Check Row 2 (Should NOT match - diff name)
    row2 = result_df.iloc[2]
    if row2['Category'] != "Test Category":
        print("PASS: Row 2 correctly NOT categorized (diff name).")
    else:
        print(f"FAIL: Row 2 incorrectly categorized.")

    # 4. Clean up
    print("Cleaning up...")
    remove_amount_override(test_trans, test_amount)
    overwrites = load_amount_overwrites()
    if key not in overwrites:
        print("Override removed successfully.")
    else:
        print("FAILED: Override not removed.")

if __name__ == "__main__":
    test_amount_override()
