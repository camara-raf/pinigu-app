# 💰 Finance Analysis App - Architecture & Features

**Last Updated:** November 29, 2025  
**Status:** Production Ready ✅

---

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Complete Folder Structure](#complete-folder-structure)
4. [File Inventory](#file-inventory)
5. [Application Tabs (Features)](#application-tabs-features)
6. [Data Flow](#data-flow)
7. [CSV Schemas](#csv-schemas)
8. [Technology Stack](#technology-stack)

---

## Project Overview

A comprehensive Streamlit-based personal finance analysis application that:
- Consolidates transactions from multiple bank accounts (Santander, BBVA, Wise, Revolut, Degiro, etc.)
- Applies intelligent categorization with wildcard pattern matching
- Supports manual transaction overrides for fine-tuned categorization
- Generates captured transactions from categorized transfers to non-transaction accounts
- Creates synthetic balance-adjustment transactions for non-transaction account reconciliation
- Provides rich visualizations and analytics via interactive dashboards
- Manages bulk mapping rules for efficient categorization at scale

**Key Innovation:** Non-Transaction Accounts feature allows balance-only accounts to be tracked alongside transaction-based accounts with automatic synthetic transaction generation.

---

## System Architecture

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    STREAMLIT WEB APP                         │
│                   (Main Entry: app.py)                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           NAVIGATION: 6 Main Tabs                   │    │
│  │  1️⃣  📤 Upload Files                              │    │
│  │  2️⃣  📁 File Management                            │    │
│  │  3️⃣  🏷️  Category Mapping                          │    │
│  │  4️⃣  ⚙️  Bulk Mapping                              │    │
│  │  5️⃣  ✏️  Manual Overwrites                         │    │
│  │  6️⃣  ⚖️  Non-Transaction Accounts (NEW)            │    │
│  │  7️⃣  📊 Dashboard                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │     VIEWS LAYER (views/ directory)                 │    │
│  │  - Each tab renders via dedicated view module       │    │
│  │  - Session state management                         │    │
│  │  - User input handling                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │    UTILITIES LAYER (utils/ directory)              │    │
│  │  - Data consolidation                               │    │
│  │  - Categorization engine                            │    │
│  │  - File management                                  │    │
│  │  - Transaction keys (deduplication)                 │    │
│  │  - Manual overrides                                 │    │
│  │  - Non-transaction account logic (NEW)              │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │      DATA LAYER (data/ directory - CSV files)       │    │
│  │  - consolidated_transactions.csv                    │    │
│  │  - mapping_rules.csv                                │    │
│  │  - manual_overwrites.csv                            │    │
│  │  - balance_entries.csv (NEW)                        │    │
│  │  - bank_mapping.csv (extended)                      │    │
│  │  - files_summary.csv                                │    │
│  │  - raw_files/ (uploaded Excel files)                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Data Processing Pipeline

```
User Uploads Files (Tab 1)
    ↓
[File Management Tab] - Click "Reload Data"
    ↓
Consolidation Process:
    1. Load all Excel files from raw_files/
    2. Parse with bank-specific modules (santander.py, bbva.py)
    3. Standardize columns (Date, Bank, Account, Amount, etc.)
    4. Concatenate all dataframes
    5. Create transaction keys (MD5 hash of 6 fields)
    6. Deduplicate (keep first)
    7. Apply categorization rules (Category Mapping tab)
    8. Apply manual overrides (Manual Overwrites tab)
    9. Generate captured transactions (Non-Transaction Accounts)
    10. Generate synthetic transactions (Balance adjustments)
    11. Save to consolidated_transactions.csv
    ↓
Dashboard displays categorized, deduplicated transactions
```

---

## Complete Folder Structure

```
finance/
│
├── 📄 app.py                              # Main Streamlit application (entry point)
├── 📄 requirements.txt                    # Python package dependencies
│
├── 📁 views/                              # Streamlit tab implementations
│   ├── __init__.py
│   ├── upload_files.py                    # Tab 1: Upload Files UI
│   ├── file_management.py                 # Tab 2: File Management UI
│   ├── mapping.py                         # Tab 3: Category Mapping UI
│   ├── bulk_mapping.py                    # Tab 4: Bulk Mapping UI
│   ├── bulk_mapping (Copy).py             # Backup of bulk mapping
│   ├── manual_overwrite.py                # Tab 5: Manual Overwrites UI
│   ├── non_transaction_accounts.py        # Tab 6: Non-Transaction Accounts UI (NEW)
│   ├── dashboard.py                       # Tab 7: Dashboard UI
│   └── __pycache__/
│
├── 📁 utils/                              # Core business logic & utilities
│   ├── __init__.py
│   ├── consolidation.py                   # Main consolidation pipeline
│   ├── categorization.py                  # Categorization rules engine
│   ├── file_management.py                 # File I/O and metadata
│   ├── transaction_keys.py                # MD5 transaction key generation
│   ├── manual_overrides.py                # Manual override management
│   ├── non_transaction_logic.py           # Non-transaction account logic (NEW)
│   └── __pycache__/
│
├── 📁 data/                               # CSV data storage
│   ├── consolidated_transactions.csv      # All transactions (deduplicated, categorized)
│   ├── mapping_rules.csv                  # Categorization rules
│   ├── manual_overwrites.csv              # User category overrides
│   ├── balance_entries.csv                # Manual balance snapshots (NEW)
│   ├── bank_mapping.csv                   # Bank/account registry (extended with Category_Source)
│   ├── files_summary.csv                  # Uploaded files metadata
│   └── raw_files/                         # Uploaded Excel files
│       ├── santander/                     # Santander transaction exports
│       ├── bbva/                          # BBVA transaction exports
│       ├── revolut/                       # Revolut balance exports
│       └── temp/                          # Temporary processing
│
├── 📁 management/                         # Bank-specific parsers
│   ├── santander.py                       # Santander Excel parser
│   ├── bbva.py                            # BBVA Excel parser
│   └── __pycache__/
│
├── 📁 doc/                                # Documentation
│   ├── README.md                          # Full user documentation
│   ├── QUICKSTART.md                      # 5-minute setup guide
│   ├── ARCHITECTURE.md                    # Visual architecture diagrams
│   ├── FEATURES.md                        # Feature checklist
│   ├── PROJECT_SUMMARY.md                 # Project overview
│   ├── IMPLEMENTATION.md                  # Technical details
│   ├── BULK_MAPPING_GUIDE.md              # Bulk mapping user guide
│   ├── BULK_MAPPING_QUICKSTART.md         # Bulk mapping quick start
│   ├── BULK_MAPPING_IMPLEMENTATION.md     # Bulk mapping technical details
│   ├── BULK_MAPPING_CODE_WALKTHROUGH.md   # Code walkthrough
│   ├── finance_app_design.md              # Original design document
│   ├── finance_app_mockup.html            # Visual mockup reference
│   └── create_sample_data.py              # Sample data generator
│
├── 📁 input_data/                         # Reference input files
│   ├── BBVA/
│   └── Santander/
│
├── 📁 to_delete/                          # Deprecated/archive files
│
└── 🔧 Configuration Files
    ├── .venv/                             # Python virtual environment
    ├── .venv/bin/activate                 # Virtual environment activation
    ├── .vscode/                           # VS Code settings
    ├── .gitignore                         # Git ignore patterns
    └── __pycache__/
```

---

## File Inventory

### Core Application Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `app.py` | Main Streamlit app with 7 tabs | ~73 | ✅ Active |
| `requirements.txt` | Python dependencies | ~10 | ✅ Active |

### Views (Tab Implementations)

| File | Tab Name | Purpose | Lines |
|------|----------|---------|-------|
| `views/upload_files.py` | 📤 Upload Files | File upload UI and validation | ~80 |
| `views/file_management.py` | 📁 File Management | File listing and data reload | ~120 |
| `views/mapping.py` | 🏷️ Category Mapping | Categorization rule UI | ~150 |
| `views/bulk_mapping.py` | ⚙️ Bulk Mapping | Bulk rule creation UI | ~250 |
| `views/manual_overwrite.py` | ✏️ Manual Overwrites | Manual categorization override UI | ~180 |
| `views/non_transaction_accounts.py` | ⚖️ Non-Transaction Accounts | Balance account management UI (NEW) | ~200 |
| `views/dashboard.py` | 📊 Dashboard | Analytics and visualizations | ~300 |

### Utilities (Business Logic)

| File | Purpose | Key Functions | Lines |
|------|---------|----------------|-------|
| `utils/consolidation.py` | Main consolidation pipeline | `consolidate_data()`, `extract_distinct_uncategorized_transactions()` | ~110 |
| `utils/categorization.py` | Categorization rules engine | `apply_categorization()`, `match_pattern()`, validation functions | ~280 |
| `utils/file_management.py` | File I/O operations | `parse_multiple_files()`, `update_file_summary()` | ~180 |
| `utils/transaction_keys.py` | Transaction deduplication | `create_transaction_key()` (MD5 hash) | ~10 |
| `utils/manual_overrides.py` | Override management | `load_manual_overwrites()`, `add_manual_override()`, `remove_manual_override()` | ~80 |
| `utils/non_transaction_logic.py` | Non-transaction accounts (NEW) | `parse_category_source()`, `get_captured_transactions()`, `get_synthetic_transactions()`, `add_balance_entry()` | ~320 |

### Bank Parsers

| File | Bank | Purpose |
|------|------|---------|
| `management/santander.py` | Santander | Parse Santander Excel exports |
| `management/bbva.py` | BBVA | Parse BBVA Excel exports |

### Data Files

| File | Purpose | Columns | Status |
|------|---------|---------|--------|
| `data/consolidated_transactions.csv` | Main transaction table | Date, Bank, Account, Amount, Category, Type, Balance, Source_File, Transaction_Source | ✅ Generated |
| `data/mapping_rules.csv` | Categorization rules | Rule_ID, Pattern, Category, Sub-Category, Direction, Priority, Is_Wildcard | ✅ User-created |
| `data/manual_overwrites.csv` | Category overrides | Transaction_Key, Category, Sub-Category, Direction, Override_Date | ✅ User-created |
| `data/balance_entries.csv` | Balance snapshots (NEW) | Bank, Account, Date, Balance, Entered_Date | ✅ User-created |
| `data/bank_mapping.csv` | Bank/account registry (EXTENDED) | Bank_ID, Bank, Owner, Currency, Input, Account, Module, Category_Source | ✅ Config |
| `data/files_summary.csv` | Upload metadata | Bank, Account, File Name, Oldest Date, Newest Date, Upload Date | ✅ Generated |

---

## Application Tabs & Features

### Tab 1: 📤 Upload Files

**Purpose:** Import transaction data from Excel files

**UI Components:**
- Bank selector dropdown
- Account input field or auto-detect
- Excel file uploader (.xls, .xlsx)
- File preview (first 10 rows)
- Upload confirmation button

**Features:**
- Drag-and-drop file upload
- File type validation (only Excel)
- Preview before upload
- Success/error notifications
- Automatic file storage in `data/raw_files/{bank}/`

**Data Flow:**
```
User selects bank & account
    ↓
User uploads Excel file
    ↓
File type validation
    ↓
File preview displayed
    ↓
[Upload button] → File saved + Metadata updated
```

---

### Tab 2: 📁 File Management

**Purpose:** Manage uploaded files and trigger consolidation

**UI Components:**
- File listing table with metadata
- Delete button per file
- Primary "🔄 Reload Data" button
- Last load timestamp display

**Features:**
- Lists all uploaded files with:
  - File Name
  - Bank
  - Account
  - Date Range (oldest/newest transaction)
  - Upload Date
- Delete file functionality (removes from raw_files and updates metadata)
- **Reload Data** triggers complete consolidation pipeline:
  1. Parses all files
  2. Consolidates and deduplicates
  3. Applies categorization rules
  4. Applies manual overrides
  5. Generates captured transactions
  6. Generates synthetic transactions
  7. Saves consolidated output

**Data Flow:**
```
[Reload Data button]
    ↓
Parse all files (raw_files/*.xlsx)
    ↓
Consolidate + Deduplicate
    ↓
Apply Categorization Rules
    ↓
Apply Manual Overrides
    ↓
Generate Captured Transactions
    ↓
Generate Synthetic Transactions
    ↓
Save consolidated_transactions.csv
    ↓
Display success + transaction count
```

---

### Tab 3: 🏷️ Category Mapping

**Purpose:** Create and manage categorization rules

**UI Components - Existing Rules Section:**
- Table showing all rules
- Columns: Pattern, Category, Sub-Category, Direction, Priority
- Delete button per rule
- Sort controls

**UI Components - Create New Rule Section:**
- Pattern input field
- Category dropdown (dynamic from consolidated data)
- Sub-Category input field
- Direction dropdown (In, Out, None)
- Priority input (numeric)
- "🔍 Test Rule" button
- "💾 Save Rule" button

**Features:**
- Pattern matching with wildcards:
  - `*netflix*` = contains "netflix"
  - `salary*` = starts with "salary"
  - `*tax` = ends with "tax"
  - `exact` = exact match
- Test Rule preview shows matching transactions:
  - Uncategorized matches highlighted
  - Already-categorized matches shown separately
  - Match count displayed
  - Transaction details (date, amount, description)
- Rules sorted by priority (higher = checked first)
- Direction filtering:
  - `In` = income transactions only
  - `Out` = expense transactions only
  - `None` = both directions
- Rule deletion with confirmation

**Data Flow:**
```
User enters pattern
    ↓
[Test Rule] → Find matching uncategorized transactions
    ↓
Display matches with count
    ↓
[Save Rule] → Add to mapping_rules.csv
    ↓
Rule applies on next consolidation
```

---

### Tab 4: ⚙️ Bulk Mapping

**Purpose:** Efficiently create multiple categorization rules in bulk

**UI Components:**
- Bulk rule creation form
- Pattern input with multi-line support
- Category selector
- Sub-Category input
- Direction dropdown
- Priority setting
- "🚀 Apply Bulk Rules" button
- Progress indicator

**Features:**
- Create multiple rules at once
- Pattern validation before saving
- Automatic priority assignment
- Batch rule import/export
- Conflict detection
- Bulk rule preview before apply

**Data Flow:**
```
User enters multiple patterns + category
    ↓
[Apply Bulk Rules] → Validate all patterns
    ↓
Check for conflicts
    ↓
Assign priorities
    ↓
Save to mapping_rules.csv
    ↓
Display success + rules created count
```

---

### Tab 5: ✏️ Manual Overwrites

**Purpose:** Override automatic categorization for specific transactions

**UI Components:**
- Transaction search/filter
- Transaction details display
- Category/Sub-Category override fields
- Direction selector
- "💾 Save Override" button
- Remove override button

**Features:**
- Search transactions by:
  - Description/merchant name
  - Date range
  - Amount range
  - Bank/Account
- View current categorization
- Override with new category/subcategory
- Manual overrides take precedence over rules
- Remove individual overrides
- Override history/timestamp

**Data Flow:**
```
User searches for transaction
    ↓
Display transaction details + current category
    ↓
User selects new category/subcategory
    ↓
[Save Override] → Add to manual_overwrites.csv with transaction key
    ↓
Override applies on next consolidation
```

---

### Tab 6: ⚖️ Non-Transaction Accounts (NEW)

**Purpose:** Manage balance-only accounts and generate synthetic transactions

**Sub-Tab A: Manage Accounts**

**UI Components:**
- Account selector (from Balance-type accounts in bank_mapping.csv)
- Category link management
- Add/remove category+subcategory pairs

**Features:**
- Select any Balance-type account (Wise, Revolut, Degiro, etc.)
- Define category+subcategory pairs for transfer capture:
  - Example: `(Inter-Transfer,Invest)|(Income,Dividend)`
  - Stored in `bank_mapping.csv` Column_Source field
- Display current linked categories
- Add new category links
- Remove individual category links
- Edit multiple pairs per account

**Data Flow:**
```
User selects Balance account
    ↓
Display current category links
    ↓
[Add Category Link] → Add (Category,Sub-Category) pair
    ↓
Update bank_mapping.csv Category_Source
    ↓
Linked categories apply on next consolidation
```

**Sub-Tab B: Balance Entries**

**UI Components:**
- Account selector
- Date picker
- Balance amount input
- Save button
- Balance entries table
- Delete button per entry

**Features:**
- Enter manual balance snapshots by date
- Support arbitrary dates (not restricted to specific days)
- Store entries in `balance_entries.csv`
- View all balance entries with entered date/time
- Delete individual balance entries
- Entries are used to generate synthetic transactions

**Data Flow:**
```
User selects account
    ↓
User enters date + balance
    ↓
[Save Balance Entry] → Add to balance_entries.csv
    ↓
Balance entry used on next consolidation to generate synthetic transactions
```

**Captured Transaction Generation:**
- System finds all transactions matching linked categories
- Creates mirror transactions with:
  - Reversed amount (positive → negative, negative → positive)
  - Same date, category, sub-category
  - Non-transaction account (Bank/Account)
  - Marked as `Transaction_Source='Captured'`

**Synthetic Transaction Generation:**
- For each balance entry date:
  1. Sum all captured transactions up to that date
  2. Calculate delta: `manual_balance - running_sum`
  3. If delta ≠ 0, generate synthetic transaction:
     - Amount = delta
     - Date = balance entry date
     - Description = `"Adjustment - {Bank} {Account} | Balance {manual_balance}"`
     - Category = "Balance Adjustment"
     - Marked as `Transaction_Source='Synthetic'`

**Example Scenario:**
```
Configuration:
- Account: Wise Chequing
- Category links: (Inter-Transfer,Invest)
- Balance entries:
  - 2025-03-03: 200
  - 2025-04-04: 250
  - 2025-05-05: 210

Consolidation Result:
- Captured transactions: All (Inter-Transfer,Invest) categorized as Wise Chequing with reversed amounts
- Running sum on 2025-03-03: 200 captured → Delta: 0 → No synthetic
- Running sum on 2025-04-04: 200 + 50 captured → Delta: 0 → No synthetic
- Running sum on 2025-05-05: 200 + 50 - 40 captured → Delta: 0 → No synthetic
(Example assumes exact matching)
```

---

### Tab 7: 📊 Dashboard

**Purpose:** Visualize and analyze categorized transactions

**UI Components:**
- Date filters (Year, Quarter, Month)
- Account/Bank filters
- Transaction category filter
- Transactions table with sorting/pagination

**Visualizations:**
- 📋 **Transactions Table:** Full transaction details (Date, Description, Bank, Amount, Category, Sub-Category, Type, Transaction_Source)
- 🥧 **Pie Chart:** Balance/spending by category
- 📊 **Bar Chart:** Monthly spending trends
- 📈 **Line Chart:** Cumulative balance over time
- 💰 **Summary Metrics:**
  - Total Income
  - Total Expenses
  - Net Balance
  - Average Transaction
  - Transaction Count

**Features:**
- Real-time filtering
- Export capability (CSV)
- Date range selection
- Multi-select filters
- Transaction_Source indicator (File, Captured, Synthetic)
- Responsive design (desktop/mobile)

**Data Flow:**
```
Dashboard loads consolidated_transactions.csv
    ↓
User applies filters (date, category, bank, etc.)
    ↓
Filtered data displayed in table + visualizations
    ↓
Charts update in real-time
    ↓
User can export filtered data
```

---

## Data Flow

### Complete Consolidation Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│  USER UPLOADS FILES (Tab 1)                         │
│  raw_files/{bank}/{file}.xlsx                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  USER CLICKS "RELOAD DATA" (Tab 2)                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 1: Parse Excel Files                          │
│  - Load raw_files/*.xlsx                            │
│  - Call bank-specific parsers                       │
│    (santander.py, bbva.py, etc.)                    │
│  - Standardize columns to common format             │
│  Output: DataFrame                                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 2: Consolidate & Concatenate                  │
│  - Combine all bank dataframes                      │
│  - Standardize data types                           │
│  Output: master_df with all transactions            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 3: Generate Transaction Keys                  │
│  - Create MD5 hash of:                              │
│    (Date + Bank + Account + Description +           │
│     Amount + Balance)                               │
│  - Add _key column                                  │
│  Output: master_df with _key column                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 4: Deduplication                              │
│  - Drop duplicates on _key                          │
│  - Keep first occurrence                            │
│  - Remove _key column                               │
│  Output: deduplicated master_df                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 5: Apply Categorization Rules                 │
│  - Load mapping_rules.csv                           │
│  - Match patterns (with wildcard support)           │
│  - Assign Category/Sub-Category                     │
│  - Priority sorting (higher = checked first)        │
│  - Direction filtering (In/Out/None)                │
│  Output: master_df with Category columns            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 6: Apply Manual Overrides                     │
│  - Load manual_overwrites.csv                       │
│  - Match by transaction key                         │
│  - Override Category/Sub-Category                   │
│  Output: master_df with overrides applied           │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 7: Generate Captured Transactions (NEW)       │
│  - Load balance_entries.csv                         │
│  - Load bank_mapping.csv with Category_Source       │
│  - Find transactions matching linked categories     │
│  - Create mirror transactions with reversed amounts │
│  - Mark as Transaction_Source='Captured'            │
│  Output: captured_df                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 8: Generate Synthetic Transactions (NEW)      │
│  - For each balance account with entries:           │
│    1. Load captured transactions for account        │
│    2. Sum captured transactions by date             │
│    3. For each balance entry:                       │
│       delta = manual_balance - running_sum          │
│       if delta ≠ 0: create synthetic transaction    │
│  - Deduplicate synthetic transactions               │
│  - Mark as Transaction_Source='Synthetic'           │
│  Output: synthetic_df                               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 9: Combine All Transactions                   │
│  - Concatenate:                                     │
│    - master_df (File source)                        │
│    - captured_df (Captured source)                  │
│    - synthetic_df (Synthetic source)                │
│  - Add Transaction_Source column                    │
│  - Ensure all columns match                         │
│  Output: final_master_df                            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  STEP 10: Save to CSV                               │
│  - Save to consolidated_transactions.csv            │
│  - Sort by Transaction Date (descending)            │
│  Output: consolidated_transactions.csv              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  RESULT: Dashboard displays all transactions        │
│  with Transaction_Source indicator                  │
└─────────────────────────────────────────────────────┘
```

---

## CSV Schemas

### consolidated_transactions.csv

**Purpose:** Main transaction table with all processed transactions

| Column | Type | Example | Source |
|--------|------|---------|--------|
| Transaction Date | datetime | 2025-11-15 | File/Generated |
| Effective Date | datetime | 2025-11-15 | File/Generated |
| Bank | string | Santander | File/Generated |
| Account | string | Chequing | File/Generated |
| Transaction | string | GROCERY STORE ABC | File/Generated |
| Type | string | Out | File/Generated |
| Amount | float | -45.50 | File/Generated |
| Balance | float | 1234.56 | File (None for generated) |
| Category | string | Groceries | Rule/Override |
| Sub-Category | string | Supermarket | Rule/Override |
| Source_File | string | export.xlsx | File only |
| Transaction_Source | string | File/Captured/Synthetic | Generated |

---

### mapping_rules.csv

**Purpose:** Categorization rules for pattern matching

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| Rule_ID | string | rule_001 | Unique identifier |
| Pattern | string | *netflix* | Wildcard pattern |
| Category | string | Entertainment | Main category |
| Sub-Category | string | Streaming | Sub-category |
| Direction | string | Out | In/Out/None |
| Priority | int | 100 | Higher = checked first |
| Is_Wildcard | bool | True | Uses regex matching |

---

### manual_overwrites.csv

**Purpose:** User-defined category overrides for specific transactions

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| Transaction_Key | string | abc123def456 | MD5 hash of transaction |
| Category | string | Income | Override category |
| Sub-Category | string | Bonus | Override sub-category |
| Direction | string | In | In/Out/None |
| Override_Date | datetime | 2025-11-29 18:45:00 | When override was created |

---

### balance_entries.csv (NEW)

**Purpose:** Manual balance snapshots for non-transaction accounts

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| Bank | string | Wise | Balance account bank |
| Account | string | Chequing | Balance account name |
| Date | date | 2025-11-30 | Snapshot date |
| Balance | float | 5000.00 | Balance amount |
| Entered_Date | datetime | 2025-11-29 18:00:00 | When entry was created |

---

### bank_mapping.csv (EXTENDED)

**Purpose:** Registry of all bank/account combinations with category sources

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| Bank_ID | int | 4 | Unique identifier |
| Bank | string | Wise | Bank name |
| Owner | string | Rafa | Account owner |
| Currency | string | EUR | Account currency |
| Input | string | Balance | Transactions/Balance |
| Account | string | Chequing | Account type |
| Module | string | | Parser module (if Transactions) |
| Category_Source | string | (Inter-Transfer,Invest)\|(Income,Div) | Linked category+subcategory pairs |

---

### mapping_rules.csv Example Content

```csv
Rule_ID,Pattern,Category,Sub-Category,Direction,Priority,Is_Wildcard
rule_001,*netflix*,Entertainment,Streaming,Out,100,True
rule_002,*amazon*,Shopping,Online,Out,95,True
rule_003,*salary*,Income,Salary,In,200,True
rule_004,*transfer,Inter-Transfer,Transfer,None,50,True
rule_005,groceries,Groceries,Supermarket,Out,80,True
```

---

### files_summary.csv

**Purpose:** Metadata about uploaded Excel files

| Column | Type | Example |
|--------|------|---------|
| Bank | string | Santander |
| Account | string | Chequing |
| File Name | string | export202311.xlsx |
| Oldest Date | date | 2023-01-01 |
| Newest Date | date | 2025-11-15 |
| Upload Date | datetime | 2025-11-15 10:30:00 |

---

## Technology Stack

### Frontend
- **Streamlit** - Web application framework
- **Plotly** - Interactive visualizations
- **Pandas** - Data manipulation and display

### Backend
- **Python 3.10+** - Programming language
- **Pandas** - Data processing and CSV I/O
- **Openpyxl** - Excel file parsing

### Data Storage
- **CSV files** - Simple, version-control friendly storage
  - `data/consolidated_transactions.csv`
  - `data/mapping_rules.csv`
  - `data/manual_overwrites.csv`
  - `data/balance_entries.csv` (NEW)
  - `data/bank_mapping.csv` (EXTENDED)
  - `data/files_summary.csv`

### Development Tools
- **Git** - Version control
- **Python venv** - Virtual environment
- **VS Code** - Development IDE

---

## Key Design Decisions

### 1. CSV-Based Storage
- Simple, human-readable format
- Easy version control (Git-friendly)
- No database installation required
- Easy backup and sharing

### 2. Transaction Keys (MD5 Hash)
- Unique identifier for each transaction: `MD5(Date + Bank + Account + Description + Amount + Balance)`
- Used for deduplication and override matching
- Ensures consistency across consolidation runs

### 3. Categorization Pipeline
1. Rules processed by priority (descending)
2. First matching rule wins
3. Direction filtering enforced (In/Out/None)
4. Manual overrides take highest precedence
5. Default fallback: "Uncategorized"

### 4. Transaction_Source Column
- Tracks origin of each transaction:
  - `File` - Imported from Excel
  - `Captured` - Mirror of categorized transfer to non-transaction account
  - `Synthetic` - Generated from balance delta

### 5. Non-Transaction Account Architecture
- Separates transaction-based accounts (Santander, BBVA) from balance-only accounts (Wise, Revolut, Degiro)
- Captured transactions mirror categorized transfers
- Synthetic transactions reconcile balance entries with captured totals
- Deduplication ensures no double-counting

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Parse single 100-row Excel file | <1s | Depends on file size |
| Consolidate 1000 transactions | ~2s | Includes dedup + categorization |
| Generate captured transactions | ~1s | Depends on rule matches |
| Generate synthetic transactions | <1s | Depends on balance entries |
| Full reload (all tabs) | ~5-10s | Network + UI rendering |
| Dashboard rendering | ~2s | Depends on filtered data size |

---

## Future Enhancement Opportunities

1. **Database Integration**
   - Migrate from CSV to SQLite/PostgreSQL
   - Enables complex queries and relationships

2. **Advanced Analytics**
   - Trend analysis and forecasting
   - Budget vs actual comparison
   - Spending patterns machine learning

3. **Multi-user Support**
   - User authentication
   - Shared account management
   - Audit logging

4. **Mobile App**
   - React Native or Flutter app
   - API backend (FastAPI/Flask)

5. **Real-time Sync**
   - API integrations with banks (Open Banking)
   - Automatic transaction import

6. **Export Formats**
   - PDF reports
   - Excel workbooks
   - Tax form templates

7. **Notifications**
   - Budget alerts
   - Unusual transaction detection
   - Monthly summaries

---

## Troubleshooting

### Common Issues

**Q: Consolidation is slow**
- A: Check raw_files/ directory size. Large Excel files take longer to parse. Consider archiving old files.

**Q: Transactions not appearing in Dashboard**
- A: Ensure "Reload Data" was clicked in Tab 2. Check that transactions have valid dates and amounts.

**Q: Category rules not applying**
- A: Verify pattern syntax. Check Direction setting (In/Out/None). Ensure Priority is set correctly.

**Q: Manual override not working**
- A: Manual overrides require exact transaction key match. Try from Tab 5 directly.

---

## Contact & Support

For issues or feature requests, please refer to the QUICKSTART_AND_USAGE.md file for additional guidance.

---

**Document Version:** 1.0  
**Last Updated:** November 29, 2025  
**Status:** Production Ready ✅
