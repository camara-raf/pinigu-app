"""
Utility functions for creating and managing transaction keys.
Used for deduplication and cross-referencing across modules.
"""
import hashlib


def create_transaction_key(row):
    """Create MD5 hash key for a transaction."""
    key_str = f"{row['Transaction Date']}{row['Bank']}{row['Account']}{row['Transaction']}{row['Amount']}{row['Balance']}"
    return hashlib.md5(key_str.encode()).hexdigest()
