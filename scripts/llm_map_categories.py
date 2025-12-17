import pandas as pd
import requests
import json
import time

# Configuration
OLD_CSV_PATH = 'data/old.csv'
NEW_CSV_PATH = 'data/new.csv'
OUTPUT_CSV_PATH = 'data/mapped_categories.csv'
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "ministral-3:latest"

def load_data():
    """Loads old and new CSV files."""
    try:
        old_df = pd.read_csv(OLD_CSV_PATH)
        new_df = pd.read_csv(NEW_CSV_PATH)
        return old_df, new_df
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        exit(1)

def format_category_pair(row):
    """Formats a row into a string 'Category - Sub-Category (Direction)'."""
    return f"{row['Category']} - {row['Sub-Category']} ({row['Direction']})"

def get_llm_mapping(old_item_str, new_items_dict):
    """
    Asks the LLM to map the old item to one of the new items.
    Returns the Pair_ID of the matched new item, or None if no match/new proposed.
    """
    
    new_items_list_str = "\n".join([f"ID {pid}: {desc}" for pid, desc in new_items_dict.items()])
    
    prompt = f"""
You are a helpful assistant assisting with financial data migration.
Your task is to map an "Old Category Pair" to the best matching "New Category Pair" from a provided list.

Old Category Pair: "{old_item_str}"

Available New Category Pairs:
{new_items_list_str}

Instructions:
1. Analyze the meaning of the Old Category Pair.
2. Select the most appropriate New Category Pair from the list based on semantic similarity and financial purpose.
3. If no existing pair fits well, you may propose a mapping, but PREFER existing items.
4. Output specific JSON only.

Output JSON format:
{{
  "match_found": true/false,
  "new_pair_id": <ID from list if found, else null>,
  "reasoning": "short explanation"
}}
    """

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
         "format": "json"
    }

    try:
        response = requests.post(OLLAMA_URL, json=data)
        response.raise_for_status()
        result = response.json()
        content = json.loads(result['response'])
        return content
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return None

def main():
    print("Loading data...")
    old_df, new_df = load_data()
    
    # Pre-process new categories for the prompt
    # dictionary: Pair_ID -> Description String
    new_items_dict = {}
    for _, row in new_df.iterrows():
        new_items_dict[row['Pair_ID']] = format_category_pair(row)

    mapped_rows = []
    matched_new_ids = set()

    print(f"Processing {len(old_df)} records...")
    
    try:
        for index, old_row in old_df.iterrows():
            old_item_str = format_category_pair(old_row)
            print(f"Mapping: {old_item_str}...")
            
            llm_response = get_llm_mapping(old_item_str, new_items_dict)
            
            new_id = None
            new_cat = None
            new_sub = None
            new_dir = None
            
            if llm_response and llm_response.get("match_found") and llm_response.get("new_pair_id"):
                try:
                    # LLM might return ID as string or int, ensure compatibility
                    # Assuming Pair_ID is integer in CSV, but let's be safe
                    potential_id = llm_response["new_pair_id"]
                    
                    # handling if LLM returns a string ID that matches numeric ID in DF
                    # Convert to the type of the index/ID column in new_df
                    target_type = new_df['Pair_ID'].dtype
                    if pd.api.types.is_numeric_dtype(target_type):
                        new_id = int(str(potential_id).strip())
                    else:
                        new_id = str(potential_id).strip()

                    # Find the row in new_df
                    match_row = new_df[new_df['Pair_ID'] == new_id]
                    
                    if not match_row.empty:
                        new_cat = match_row.iloc[0]['Category']
                        new_sub = match_row.iloc[0]['Sub-Category']
                        new_dir = match_row.iloc[0]['Direction']
                        matched_new_ids.add(new_id)
                    else:
                        print(f"  Warning: LLM returned ID {new_id} not found in new.csv")
                except ValueError:
                     print(f"  Warning: Could not parse ID {llm_response['new_pair_id']}")
            
            mapped_rows.append({
                "Old_id": old_row['Pair_ID'],
                "old_category": old_row['Category'],
                "old_subcategory": old_row['Sub-Category'],
                "old_directrion": old_row['Direction'],
                "new_id": new_id,
                "new_category": new_cat,
                "new_subcategory": new_sub,
                "new_direction": new_dir
            })
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving partial progress...")
    except Exception as e:
        print(f"\nAn error occurred: {e}. Saving partial progress...")
        
    print("Processing unmatched new items...")
    # Identify pairs from new.csv that were not mapped
    all_new_ids = set(new_df['Pair_ID'].tolist())
    unmatched_ids = all_new_ids - matched_new_ids
    
    for unmatched_id in unmatched_ids:
        row = new_df[new_df['Pair_ID'] == unmatched_id].iloc[0]
        mapped_rows.append({
            "Old_id": None,
            "old_category": None,
            "old_subcategory": None,
            "old_directrion": None,
            "new_id": row['Pair_ID'],
            "new_category": row['Category'],
            "new_subcategory": row['Sub-Category'],
            "new_direction": row['Direction']
        })

    # Create final DataFrame
    output_df = pd.DataFrame(mapped_rows)
    
    # Save
    print(f"Saving to {OUTPUT_CSV_PATH}...")
    output_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
