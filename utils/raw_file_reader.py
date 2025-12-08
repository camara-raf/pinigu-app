import pandas as pd
import yaml
import os
from typing import List, Dict, Optional, Tuple, Union
from .logger import get_logger

logger = get_logger()

class RawFileReader:
    def __init__(self, config_path: str = 'config/file_signatures.yaml'):
        self.config_path = config_path
        self.signatures = self._load_signatures()
        
    def _load_signatures(self) -> List[Dict]:
        """Load signatures from YAML configuration."""
        if not os.path.exists(self.config_path):
            # Fallback for dev/testing if running from different root
            if os.path.exists(os.path.join('..', self.config_path)):
                self.config_path = os.path.join('..', self.config_path)
            else:
                logger.warning(f"Warning: Configuration file not found at {self.config_path}")
                return []
                
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('signatures', [])

    def get_signature(self, bank: str, account: str) -> Optional[Dict]:
        """Find signature for specific bank and account."""
        for sig in self.signatures:
            if sig.get('bank') == bank and sig.get('account') == account:
                return sig
        return None

    def read_files(self, file_paths: List[str], bank: str, account: str) -> pd.DataFrame:
        """
        Read multiple files for the same Bank+Account, deduplicate, and standardize.
        
        Args:
            file_paths: List of absolute file paths.
            bank: Bank name.
            account: Account name.
            
        Returns:
            Consolidated and standardized DataFrame.
        """
        signature = self.get_signature(bank, account)
        if not signature:
            raise ValueError(f"No file signature definitions found for {bank} - {account}")

        # Final column selection
        standard_cols = ['Bank', 'Account', 'Transaction Date', 'Effective Date', 'Transaction', 'Type', 'Amount', 'Balance', 'Category', 'Sub-Category', 'Source_File', 'Source_RowNo']

        dfs = []
        for file_path in file_paths:
            try:
                df = self._read_single_file(file_path, signature)
                if df is not None:
                    dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                
        if not dfs:
            return pd.DataFrame(columns=standard_cols)
            
        # Concatenate all
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Rows before deduplication: {len(combined_df)}")
        # Deduplication Strategy: Keep duplicates within the same file but remove across files  
        dedup_cols = ['Transaction Date', 'Effective Date', 'Transaction', 'Amount', 'Balance']
        first_file_per_combination = combined_df.groupby(dedup_cols)['Source_File'].first()
        combined_df['FirstFile'] = combined_df.set_index(dedup_cols).index.map(first_file_per_combination)
        combined_df = combined_df[combined_df['Source_File'] == combined_df['FirstFile']].drop('FirstFile', axis=1).reset_index(drop=True)
        logger.info(f"Rows after deduplication: {len(combined_df)}")
        
        # Add metadata
        combined_df['Bank'] = bank
        combined_df['Account'] = f"{bank} {account}" # Standard format used in app: "Bank Account"
        
        # Add derivative columns
        combined_df['Type'] = combined_df['Amount'].apply(lambda x: 'In' if x > 0 else 'Out')
        combined_df['Category'] = 'Uncategorized'
        combined_df['Sub-Category'] = 'Uncategorized'
        
        # Ensure all cols exist
        for col in standard_cols:
            if col not in combined_df.columns:
                combined_df[col] = None
                
        return combined_df[standard_cols]

    def _read_single_file(self, file_path: str, signature: Dict) -> Optional[pd.DataFrame]:
        """Read a single file and apply transformations."""
        ext = os.path.splitext(file_path)[1].lower()
        skiprows = signature.get('skiprows', 0)
        
        if ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, skiprows=skiprows)
        elif ext == '.csv':
            df = pd.read_csv(file_path, skiprows=skiprows)
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return None
                       
        # Apply Column Mapping
        mapping = signature.get('columns_mapping', {})
        source_columns = set(df.columns)
        

        for target_col, source_val in mapping.items():
            try:
                # 1. Check for Constructed Column (contains {})
                if isinstance(source_val, str) and '{' in source_val and '}' in source_val:
                     # Using apply with format
                     df[target_col] = df.apply(lambda x: source_val.format(**x.to_dict()), axis=1)
                
                # 2. Check for 1-to-1 Mapping (source_val is a column name)
                elif source_val in source_columns:
                    df[target_col] = df[source_val]
                    
                # 3. Assume Constant
                else:
                    df[target_col] = source_val
            except Exception as e:
                logger.error(f"Error mapping column {target_col} from {source_val}: {e}")

        # 4. Date Parsing (on the newly created target columns)
        date_format = signature.get('date_format')
        date_cols = ['Transaction Date', 'Effective Date']
        for col in date_cols:
            if col in df.columns:
                if date_format:
                     df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce')
                else:
                     df[col] = pd.to_datetime(df[col], errors='coerce')

        # Keep Target columns only
        df = df[list(mapping.keys())]
        
        # Add Source Row Number (1-based, relative to data)
        offset = skiprows + 1 + 1 
        df['Source_File'] = os.path.basename(file_path)
        df['Source_RowNo'] = df.index + offset

        return df
