"""
Utils package - Transaction processing utilities for the finance app.

Modules:
- transaction_keys: Transaction key generation for deduplication
- file_management: File handling and consolidation data I/O
- file_detection: Auto-detection of Bank+Account from file structure
- categorization: Transaction categorization with rules and patterns
- consolidation: Data consolidation from multiple sources
- manual_overrides: Manual override management
"""

# Core utilities
from .transaction_keys import create_transaction_key
from .logger import get_logger

# File management
from .file_management import (
    parse_excel_file,
    load_consolidated_data,
    save_consolidated_data,
    get_uploaded_files_info,
    delete_uploaded_file,
    read_bank_mapping,
    update_file_summary,
    get_transaction_capable_banks,
    get_accounts_for_bank,
    RAW_FILES_DIR,
    CONSOLIDATED_FILE,
    DATA_DIR,
)

# File detection
from .file_detection import (
    detect_bank_account_pair,
    detect_all_files,
    get_module_signature_info,
)

# Constants
from .categorization import MAPPING_RULES_FILE

# Categorization and rules
from .categorization import (
    match_pattern,
#    validate_pattern,
    load_mapping_rules,
    apply_categorization,
    add_mapping_rule,
    delete_mapping_rule,
    test_rule,
    get_category_subcategory_combinations,
    get_subcategories_for_category,
    get_direction_for_subcategory,
    get_flat_mapping_options,
    apply_new_rules_list_to_consolidated_data
)

# Consolidation
from .consolidation import (
    ingest_transactions,
    map_transactions,
    synthesize_transactions,
    extract_distinct_uncategorized_transactions)

# Manual overrides
from .manual_overrides import (
    load_manual_overwrites,
    add_manual_override,
    remove_manual_override,
    load_amount_overwrites,
    add_amount_override,
    remove_amount_override,
)

__all__ = [
    # Transaction keys
    'create_transaction_key',
    # Logger
    'get_logger',
    # File management
    'parse_excel_file',
    'load_consolidated_data',
    'save_consolidated_data',
    'get_uploaded_files_info',
    'delete_uploaded_file',
    'read_bank_mapping',
    'update_file_summary',
    'get_transaction_capable_banks',
    'get_accounts_for_bank',
    # File detection
    'detect_bank_account_pair',
    'detect_all_files',
    'get_module_signature_info',
    # Categorization
    'match_pattern',
#    'validate_pattern',
    'load_mapping_rules',
    'apply_categorization',
    'add_mapping_rule',
    'delete_mapping_rule',
    'test_rule',
    # Consolidation
    'extract_distinct_uncategorized_transactions',
    # Manual overrides
    'load_manual_overwrites',
    'add_manual_override',
    'remove_manual_override',
    'load_amount_overwrites',
    'add_amount_override',
    'remove_amount_override'
]

