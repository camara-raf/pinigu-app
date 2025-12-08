"""
Utility functions for transaction categorization using rules and pattern matching.
Handles category assignment through rules-based matching with wildcard support.
Supports Category + Sub-Category + Direction hierarchical combinations.
"""
import re
import pandas as pd
import polars as pl
import os
from .transaction_keys import create_transaction_key

MAPPING_RULES_FILE = os.path.join("data", "mapping_rules.csv")
MAPPING_PAIRS_FILE = os.path.join("data", "mapping_pairs.csv")


def validate_pattern(pattern_str):
    """
    Validate if pattern can compile as regex.
    Returns True if valid, False otherwise.
    """
    if not pattern_str:
        return False
    
    try:
        regex_pattern = re.escape(pattern_str).replace(r'\*', '.*')
        re.compile(regex_pattern)
        return True
    except Exception:
        return False


def match_pattern(text, pattern):
    """
    Match transaction text against pattern with wildcard support.
    * at start: ends with
    * at end: starts with
    * in middle: contains
    """
    text = text.lower()
    pattern = pattern.lower()
    
    # Escape special regex characters except *
    regex_pattern = re.escape(pattern).replace(r'\*', '.*')
    #regex_pattern = re.escape(pattern).replace(r'\*', '.*')
    #if 'concepto papas' in text and 'papas' in pattern:
    #    print(f"Test pattern: {pattern}")

    try:
        matched = bool(re.match(f'^{regex_pattern}$', text))
        #matched = bool(re.search(regex_pattern, text))
        return matched
    except:
        return False


def load_mapping_rules():
    """Load mapping rules from CSV and join with pairs to get full details."""
    if not os.path.exists(MAPPING_RULES_FILE):
        return pd.DataFrame(columns=['Rule_ID', 'Pattern', 'Category', 'Sub-Category', 'Direction', 'Priority', 'Is_Wildcard'])

    rules_df = pd.read_csv(MAPPING_RULES_FILE, keep_default_na=False, na_values=['NaN'])
    
    if os.path.exists(MAPPING_PAIRS_FILE):
        pairs_df = pd.read_csv(MAPPING_PAIRS_FILE, keep_default_na=False, na_values=['NaN'])
        # Merge rules with pairs
        if 'Pair_ID' in rules_df.columns and 'Pair_ID' in pairs_df.columns:
            # Ensure Pair_ID is int for merging
            rules_df['Pair_ID'] = pd.to_numeric(rules_df['Pair_ID'], errors='coerce').fillna(0).astype(int)
            pairs_df['Pair_ID'] = pd.to_numeric(pairs_df['Pair_ID'], errors='coerce').fillna(0).astype(int)
            
            df = pd.merge(rules_df, pairs_df, on='Pair_ID', how='left')
        else:
            # Fallback if migration hasn't happened or something is wrong
            df = rules_df
    else:
        df = rules_df

    # Ensure all required columns exist (fill missing from merge with empty strings)
    required_cols = ['Rule_ID', 'Pattern', 'Category', 'Sub-Category', 'Direction', 'Priority', 'Is_Wildcard']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
            
    return df.sort_values('Priority', ascending=False).reset_index(drop=True)


def get_category_subcategory_combinations():
    """
    Get all unique (Category, Sub-Category, Direction) combinations from rules.
    Returns a list of dicts with hierarchy information for UI selection.
    """
    rules = load_mapping_rules()
    
    if rules.empty:
        return []
    
    # Get distinct combinations from pairs file directly if possible
    if os.path.exists(MAPPING_PAIRS_FILE):
        pairs_df = pd.read_csv(MAPPING_PAIRS_FILE, keep_default_na=False, na_values=['NaN'])
        combinations = pairs_df[['Category', 'Sub-Category', 'Direction']].drop_duplicates().reset_index(drop=True)
    else:
        # Fallback to rules file
        combinations = rules[['Category', 'Sub-Category', 'Direction']].drop_duplicates().reset_index(drop=True)

    #order combinations by cateory and sub-category
    combinations = combinations.sort_values(['Category', 'Sub-Category']).reset_index(drop=True)
    
    # Build hierarchy: Category -> [(Sub-Category, Direction), ...]
    hierarchy = {}
    for _, row in combinations.iterrows():
        cat = row['Category']
        sub_cat = row['Sub-Category']
        direction = row['Direction']
        
        if cat not in hierarchy:
            hierarchy[cat] = []
        
        hierarchy[cat].append({
            'sub_category': sub_cat,
            'direction': direction
        })
    
    return hierarchy


def get_subcategories_for_category(category):
    """Get all sub-categories for a given category with their directions."""
    hierarchy = get_category_subcategory_combinations()
    
    if category not in hierarchy:
        return []
    
    return hierarchy[category]


def get_direction_for_subcategory(category, sub_category):
    """Get the direction for a specific category + sub-category combination."""
    hierarchy = get_category_subcategory_combinations()
    
    if category not in hierarchy:
        return None
    
    for item in hierarchy[category]:
        if item['sub_category'] == sub_category:
            return item['direction']
    
    return None


def apply_categorization(df, manual_overwrites=None):
    """
    Apply categorization rules and manual overwrites to dataframe.
    
    Applies Category, Sub-Category, and Type (Direction) from matching rules.
    Filters rules by transaction Type (In/Out) to match:
    - In transactions: rules with Direction in [In, None]
    - Out transactions: rules with Direction in [Out, None]
    
    Type is replaced with Direction value from rule (except when Direction='None', 
    in which case original Type is preserved).
    """
    from .manual_overrides import load_manual_overwrites, load_amount_overwrites
    
    print("DF before categorization:", df.shape)
    if df.empty:
        return df
        
    # Convert to Polars
    # Ensure numeric columns are actually numeric to avoid ArrowInvalid errors
    # This handles cases where Amount/Balance might be object type with mixed strings
    for col in ['Amount', 'Balance']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # Ensure we have a clean dataframe to start with
    pl_df = pl.from_pandas(df)
    
    # Create transaction keys
    # We use map_elements because create_transaction_key uses hashlib which is not native to Polars expressions yet
    # But we can optimize by constructing the string in Polars and only hashing in python if needed,
    # or just use the python function as is since it's one pass.
    # To match original logic exactly:
    pl_df = pl_df.with_columns(
        pl.struct(['Transaction Date', 'Bank', 'Account', 'Transaction', 'Amount', 'Balance'])
        .map_elements(lambda x: create_transaction_key(x), return_dtype=pl.String)
        .alias('_key')
    )
    
    # Load mapping rules
    rules = load_mapping_rules()
    print("DF as Polars:", pl_df.shape)
    # 1. Apply Rules
    # Strategy: Apply rules from LOWEST to HIGHEST priority.
    # This way, higher priority rules overwrite lower priority ones (simulating "first match wins" from the top).
    if not rules.empty:
        # Sort by Priority ASCENDING (Low -> High)
        rules = rules.sort_values('Priority', ascending=True)
        
        # Pre-calculate regex patterns
        # match_pattern logic: re.escape(pattern).replace(r'\*', '.*')
        # We can do this in python list comprehension
        patterns = []
        for _, rule in rules.iterrows():
            pat = re.escape(rule['Pattern'].lower()).replace(r'\*', '.*')
            # Add start/end anchors to match match_pattern logic:
            # match_pattern uses re.match(f'^{regex_pattern}$', text)
            # So we need exact match of the pattern (which might contain .*)
            pat = f"^{pat}$"
            patterns.append({
                'regex': pat,
                'category': rule['Category'],
                'sub_category': rule['Sub-Category'],
                'direction': rule.get('Direction', 'None')
            })
            
        # We will build expressions or iterate. Iterating 100-1000 rules is fast enough in Polars.
        # For very large rule sets, we might want to combine them, but regex matching is the constraint.
        
        # We can use a fold or iteration. Iteration is clearer.
        for rule in patterns:
            # Condition: Transaction matches pattern            
            regex = rule['regex']
            cat = rule['category']
            sub = rule['sub_category']
            direction = rule['direction']
            
            # Create mask for matching transactions
            mask = pl.col('Transaction').str.to_lowercase().str.contains(regex, strict=False)
            
            pl_df = pl_df.with_columns([
                pl.when(mask).then(pl.lit(cat)).otherwise(pl.col('Category')).alias('Category'),
                pl.when(mask).then(pl.lit(sub)).otherwise(pl.col('Sub-Category')).alias('Sub-Category'),
                pl.when(mask).then(pl.lit(direction)).otherwise(pl.col('Type')).alias('Type')
            ])

    print("DF after step 1 categorization:", pl_df.shape)
    # 2. Apply Amount Overrides
    amount_overwrites = load_amount_overwrites()
    if amount_overwrites:
        # Convert to DataFrame for joining
        # Key is (Transaction, Amount)
        # We need to handle Amount carefully (float).
        # The original code casts to float.
        
        ao_list = []
        for (trans, amt), val in amount_overwrites.items():
            ao_list.append({
                'Transaction': trans,
                'Amount': amt,
                'Category_AO': val['Category'],
                'Sub-Category_AO': val['Sub-Category'],
                'Direction_AO': val['Direction']
            })
            
        if ao_list:
            ao_df = pl.DataFrame(ao_list)
            
            # Join on Transaction and Amount
            # We need to ensure types match.
            # Transaction is string, Amount is float.
            
            pl_df = pl_df.join(
                ao_df, 
                on=['Transaction', 'Amount'], 
                how='left'
            )
            
            # Coalesce
            pl_df = pl_df.with_columns([
                pl.col('Category_AO').fill_null(pl.col('Category')).alias('Category'),
                pl.col('Sub-Category_AO').fill_null(pl.col('Sub-Category')).alias('Sub-Category'),
                pl.col('Direction_AO').fill_null(pl.col('Type')).alias('Type')
            ]).drop(['Category_AO', 'Sub-Category_AO', 'Direction_AO'])

    print("DF after step 2 amount overrides:", pl_df.shape)
    # 3. Apply Manual Overrides (Highest Priority)
    if manual_overwrites is None:
        manual_overwrites = load_manual_overwrites()
        
    if manual_overwrites:
        # Convert to DataFrame
        mo_list = []
        for key, val in manual_overwrites.items():
            mo_list.append({
                '_key': key,
                'Category_MO': val['Category'],
                'Sub-Category_MO': val['Sub-Category'],
                'Direction_MO': val['Direction']
            })
            
        if mo_list:
            mo_df = pl.DataFrame(mo_list)
            
            # Join on _key
            pl_df = pl_df.join(mo_df, on='_key', how='left')
            
            # Coalesce
            pl_df = pl_df.with_columns([
                pl.col('Category_MO').fill_null(pl.col('Category')).alias('Category'),
                pl.col('Sub-Category_MO').fill_null(pl.col('Sub-Category')).alias('Sub-Category'),
                pl.col('Direction_MO').fill_null(pl.col('Type')).alias('Type')
            ]).drop(['Category_MO', 'Sub-Category_MO', 'Direction_MO'])

    print("DF after step 3 manual overrides:", pl_df.shape)
    # Remove internal key column and convert back to Pandas
    result_df = pl_df.drop('_key').to_pandas()
    
    print("DF after step 4 final conversion:", result_df.shape)
    return result_df


def add_mapping_rule(pattern, category, sub_category, direction):
    """Add a new mapping rule with Category, Sub-Category, and Direction."""
    rules = load_mapping_rules() # This loads the joined view
    
    # Check if pattern already exists
    if not rules.empty and (rules['Pattern'].str.lower() == pattern.lower()).any():
        raise ValueError("Rule with this pattern already exists")
    
    # Validate required fields
    if not pattern or not category or not sub_category or not direction:
        raise ValueError("Pattern, Category, Sub-Category, and Direction are all required")
    
    # Handle Pair_ID logic
    pair_id = None
    
    # Load or create pairs file
    if os.path.exists(MAPPING_PAIRS_FILE):
        pairs_df = pd.read_csv(MAPPING_PAIRS_FILE, keep_default_na=False, na_values=['NaN'])
    else:
        pairs_df = pd.DataFrame(columns=['Pair_ID', 'Category', 'Sub-Category', 'Direction'])
        
    # Check if pair exists
    existing_pair = pairs_df[
        (pairs_df['Category'] == category) & 
        (pairs_df['Sub-Category'] == sub_category) & 
        (pairs_df['Direction'] == direction)
    ]
    
    if not existing_pair.empty:
        pair_id = existing_pair.iloc[0]['Pair_ID']
    else:
        # Create new pair
        new_pair_id = int(pairs_df['Pair_ID'].max()) + 1 if not pairs_df.empty else 1
        new_pair = {
            'Pair_ID': new_pair_id,
            'Category': category,
            'Sub-Category': sub_category,
            'Direction': direction
        }
        pairs_df = pd.concat([pairs_df, pd.DataFrame([new_pair])], ignore_index=True)
        pairs_df.to_csv(MAPPING_PAIRS_FILE, index=False)
        pair_id = new_pair_id
    
    # Calculate priority based on pattern specificity
    is_wildcard = '*' in pattern
    priority = len(pattern) if is_wildcard else len(pattern) + 100  # Exact matches higher priority
    
    # Reload raw rules file to append new rule (we don't want the joined version for saving)
    if os.path.exists(MAPPING_RULES_FILE):
        raw_rules = pd.read_csv(MAPPING_RULES_FILE, keep_default_na=False, na_values=['NaN'])
    else:
        raw_rules = pd.DataFrame(columns=['Rule_ID', 'Pattern', 'Pair_ID', 'Priority', 'Is_Wildcard'])

    # Generate new Rule_ID
    new_id = int(raw_rules['Rule_ID'].max()) + 1 if not raw_rules.empty else 1
    
    new_rule = {
        'Rule_ID': new_id,
        'Pattern': pattern,
        'Pair_ID': pair_id,
        'Priority': priority,
        'Is_Wildcard': is_wildcard
    }
    
    raw_rules = pd.concat([raw_rules, pd.DataFrame([new_rule])], ignore_index=True)
    raw_rules = raw_rules.sort_values('Rule_ID', ascending=True).reset_index(drop=True)
    raw_rules.to_csv(MAPPING_RULES_FILE, index=False)
    
    return new_id


def delete_mapping_rule(rule_id):
    """Delete a mapping rule by ID."""
    # Load raw rules to delete
    if os.path.exists(MAPPING_RULES_FILE):
        rules = pd.read_csv(MAPPING_RULES_FILE)
        rules = rules[rules['Rule_ID'] != rule_id]
        rules.to_csv(MAPPING_RULES_FILE, index=False)


def test_rule(pattern, category, sub_category, direction, consolidated_data=None):
    """
    Test a pattern against uncategorized transactions.
    Returns (uncategorized_matches, already_categorized_matches).
    
    Filters results by direction (same logic as apply_categorization):
    - Direction 'None' matches both In and Out
    - Otherwise must match transaction Type exactly
    """
    from .file_management import load_consolidated_data
    
    if consolidated_data is None:
        df = load_consolidated_data()
    else:
        df = consolidated_data
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Find pattern matches
    matches = df[df['Transaction'].apply(lambda x: match_pattern(str(x), pattern))]
    
    if matches.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Filter by direction if not 'None'
    if direction != 'None':
        matches = matches[matches['Type'] == direction]
    
    # Split into uncategorized and already categorized
    uncategorized = matches[matches['Category'] == 'Uncategorized'].copy()
    already_categorized = matches[matches['Category'] != 'Uncategorized'].copy()
    
    return uncategorized, already_categorized

def get_flat_mapping_options():
    """Convert hierarchy to flat selectable strings."""
    hierarchy = get_category_subcategory_combinations()
    options = []
    for category, entries in hierarchy.items():
        for entry in entries:
            sub = entry["sub_category"]
            direction = entry["direction"]
            options.append(f"{category} -> {sub} ({direction})")
    return options


def apply_new_rule_to_consolidated_data(pattern, direction):
    """
    Apply a newly created rule to the consolidated dataset immediately.
    Only re-evaluates rows that match the new rule's pattern and direction.
    """
    from .file_management import load_consolidated_data, save_consolidated_data
    
    df = load_consolidated_data()
    if df.empty:
        return

    # Identify rows that match the new rule
    # We need to match pattern AND direction (if direction is not None)
    mask = df['Transaction'].apply(lambda x: match_pattern(str(x), pattern))
    
    if direction != 'None':
        mask = mask & (df['Type'] == direction)
    
    # Optimization: Only target Uncategorized rows as per user request
    mask = mask & (df['Category'] == 'Uncategorized')
        
    if not mask.any():
        return

    # Extract subset
    subset_df = df[mask].copy()
    
    # Re-run categorization on subset
    # This will check ALL rules (including the new one) against these rows
    # This ensures priorities and overrides are respected
    updated_subset = apply_categorization(subset_df)
    
    # Update original dataframe
    # update() aligns on index, so this works correctly
    df.update(updated_subset)
    
    save_consolidated_data(df)


def apply_new_rules_list_to_consolidated_data(rules_list):
    """
    Apply a list of newly created rules to the consolidated dataset.
    rules_list: list of dicts with {'pattern': str, 'direction': str}
    """
    from .file_management import load_consolidated_data, save_consolidated_data
    
    if not rules_list:
        return

    df = load_consolidated_data()
    if df.empty:
        return

    # Create a combined mask for all rules
    combined_mask = pd.Series(False, index=df.index)
    
    for rule in rules_list:
        pattern = rule['pattern']
        direction = rule['direction']
        
        rule_mask = df['Transaction'].apply(lambda x: match_pattern(str(x), pattern))
        if direction != 'None':
            rule_mask = rule_mask & (df['Type'] == direction)
            
        combined_mask = combined_mask | rule_mask
    
    # Optimization: Only target Uncategorized rows
    combined_mask = combined_mask & (df['Category'] == 'Uncategorized')
    
    if not combined_mask.any():
        return

    # Extract subset
    subset_df = df[combined_mask].copy()
    
    # Re-run categorization on subset
    updated_subset = apply_categorization(subset_df)
    
    # Update original dataframe
    df.update(updated_subset)
    
    save_consolidated_data(df)
