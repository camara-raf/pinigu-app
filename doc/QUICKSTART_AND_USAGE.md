# 💰 Finance Analysis App - Quick Start & User Guide

**Last Updated:** November 29, 2025  
**Version:** Production Ready ✅

---

## 📖 Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [Tab-by-Tab Walkthrough](#tab-by-tab-walkthrough)
3. [Real-World Workflows](#real-world-workflows)
4. [Tips & Best Practices](#tips--best-practices)
5. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+ installed
- Excel transaction export files from your banks

### Step 1: Install & Run (2 minutes)

```bash
# Navigate to project directory
cd /home/camarao/home-server/my-apps/finance

# Install dependencies (first time only)
pip install -r requirements.txt

# Activate virtual environment (optional but recommended)
source .venv/bin/activate

# Start the app
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

### Step 2: Upload Your First File (1 minute)

1. Go to **Tab 1: 📤 Upload Files**
2. Select your bank (e.g., "Santander")
3. Select account (e.g., "Chequing")
4. Upload an Excel file (.xls or .xlsx)
5. Review the preview
6. Click **Upload** ✅

### Step 3: Consolidate Data (1 minute)

1. Go to **Tab 2: 📁 File Management**
2. Verify your file appears in the list
3. Click **🔄 Reload Data** (large button)
4. Wait for consolidation to complete
5. See "Successfully consolidated X transactions" ✅

### Step 4: Create Your First Category Rule (1 minute)

1. Go to **Tab 3: 🏷️ Category Mapping**
2. In "Create New Rule" section:
   - Pattern: `*grocery*` (any transaction with "grocery")
   - Category: Select "Groceries"
   - Click **🔍 Test Rule** to preview matches
   - Click **💾 Save Rule** to apply
3. Rule applies to future consolidations ✅

### Step 5: View Dashboard

1. Go to **Tab 7: 📊 Dashboard**
2. Set date filters (Year/Month)
3. View transactions and visualizations
4. Explore spending by category
5. Done! 🎉

---

## Tab-by-Tab Walkthrough

### Tab 1️⃣: 📤 Upload Files

**What it does:** Import your bank transaction data

**Step-by-step:**

1. **Select Bank**
   - Dropdown menu at top
   - Options: Santander, BBVA, Wise, Revolut, Degiro, Sunlife, E-trade
   - Choose the bank where you downloaded the file from

2. **Select Account**
   - Input field with options
   - Examples: Chequing, Credit, Savings, Investments
   - Or leave blank for auto-detect

3. **Upload File**
   - Click file upload area or drag-and-drop
   - Accepts: .xls, .xlsx files
   - Typical size: 50-500 KB per file

4. **Preview**
   - App shows first 10 rows of data
   - Verify column names match your bank's format
   - Check for any obvious data issues

5. **Confirm Upload**
   - Click **Upload** button
   - File saved to `data/raw_files/{bank}/`
   - Success message confirms upload

**💡 Tips:**
- Export files directly from your bank's website
- Name files with dates (e.g., `2025-11-export.xlsx`)
- Upload monthly or weekly for regular data refresh
- Can upload multiple files at once

**⚠️ Common Issues:**
- "Invalid file format" → Ensure file is .xls or .xlsx
- "Column mismatch" → Check your bank's export format
- "File already exists" → Files with same name are skipped

---

### Tab 2️⃣: 📁 File Management

**What it does:** Manage uploaded files and trigger consolidation

**Key Components:**

**File List Table:**
- Shows all uploaded files
- Columns: File Name, Bank, Account, Date Range, Upload Date
- Delete button on each row

**Actions:**
- **Delete file:** Click trash icon → File removed from system
- **🔄 Reload Data:** Main consolidation button
  - Processes ALL uploaded files
  - Consolidates, deduplicates, categorizes
  - Generates captured & synthetic transactions
  - Takes 5-30 seconds depending on file size

**Status Display:**
- "Last load: [timestamp]"
- "Transaction count: X"
- Shows consolidation progress with spinner

**Step-by-step to Reload:**

1. Click **🔄 Reload Data** button
2. Wait for processing:
   - "Consolidating data..." - reading files
   - "Generating captured transactions..." - transfer mirrors
   - "Generating synthetic transactions..." - balance adjustments
3. See final count of transactions
4. Success! ✅

**💡 Tips:**
- Click "Reload Data" after uploading new files
- Click "Reload Data" after creating new categorization rules
- Run weekly to keep data current
- Dashboard auto-refreshes after reload

**⚠️ Common Issues:**
- "No files found" → Upload files first in Tab 1
- "Consolidation failed" → Check file format in Tab 1
- "Transaction count drops" → Deduplication removed duplicates (expected)

---

### Tab 3️⃣: 🏷️ Category Mapping

**What it does:** Create rules to automatically categorize transactions

**Two Sections:**

**Section A: Existing Rules (View & Manage)**

Shows all current rules in a table:
- Pattern
- Category
- Sub-Category
- Direction (In/Out/None)
- Priority (100 = highest)
- Delete button

**Section B: Create New Rule**

**How to create a rule:**

1. **Enter Pattern**
   - Examples:
     - `*netflix*` - contains "netflix" (case-insensitive)
     - `salary*` - starts with "salary"
     - `*tax` - ends with "tax"
     - `exactly_this` - exact match only
   - Use `*` as wildcard anywhere in pattern

2. **Select Category**
   - Dropdown with available categories
   - Common: Income, Groceries, Entertainment, Transport, Home Spends, etc.
   - Select one that matches your pattern

3. **Enter Sub-Category**
   - More specific classification
   - Examples for "Groceries": Supermarket, Restaurant, Coffee
   - Examples for "Transport": Gas, Public, Parking
   - Can be custom text

4. **Set Direction** (optional)
   - `In` - income transactions only
   - `Out` - expense transactions only
   - `None` - both income and expenses (default)

5. **Test Rule** (preview)
   - Click **🔍 Test Rule** button
   - Shows matching transactions
   - Count displayed (e.g., "Found 12 matches")
   - Review matches before saving

6. **Save Rule**
   - Click **💾 Save Rule** button
   - Rule added to system
   - Applies on next "Reload Data"

**💡 Tips:**
- Start with broad patterns (`*word*`)
- Test before saving to see matches
- Higher priority = checked first
- Most common expenses go first
- Use direction to avoid false matches

**Real-world Example:**

| Pattern | Category | Sub-Category | Direction | Use Case |
|---------|----------|--------------|-----------|----------|
| `*netflix*` | Entertainment | Streaming | Out | Monthly subscription |
| `*supermarket*` | Groceries | Supermarket | Out | Weekly shopping |
| `salary` | Income | Salary | In | Monthly paycheck |
| `*transfer*` | Inter-Transfer | Transfer | None | Account transfers |

**⚠️ Common Mistakes:**
- Pattern too generic → Matches everything (test first!)
- Forgetting wildcards → `netflix` won't match "NETFLIX SUBSCRIPTION"
- Wrong direction → Income rule with Out direction won't match
- Duplicate patterns → Last one wins, delete old ones

---

### Tab 4️⃣: ⚙️ Bulk Mapping

**What it does:** Create MULTIPLE categorization rules at once

**Why use Bulk Mapping?**
- Faster than creating 20+ rules one-by-one
- Batch import existing rules
- Apply consistent naming across categories

**How to use:**

1. **Prepare patterns** (multi-line input)
   ```
   *netflix*
   *spotify*
   *hulu*
   *disney*
   ```

2. **Select Category**
   - Common category for all patterns
   - Example: "Entertainment"

3. **Set Priority**
   - Higher number = checked first
   - Example: 100 for high-priority rules

4. **Preview Patterns**
   - System validates all patterns
   - Shows count: "Ready to create 4 rules"

5. **Apply Bulk Rules**
   - Click **🚀 Apply Bulk Rules** button
   - All rules created at once
   - Success: "Created 4 rules successfully"

**💡 Tips:**
- One pattern per line
- Use bulk mapping for similar categories
- Create 10-20 rules at once for efficiency
- Still test individual rules afterward if needed

**Example Bulk Import:**

**Entertainment Streaming:**
```
*netflix*
*amazon prime*
*hulu*
*disney*
*hbo*
```
→ Category: Entertainment, Sub-Category: Streaming

**Grocery Stores:**
```
*supermarket*
*carrefour*
*alcampo*
*mercadona*
*whole foods*
```
→ Category: Groceries, Sub-Category: Supermarket

---

### Tab 5️⃣: ✏️ Manual Overwrites

**What it does:** Fix categorization for specific transactions

**When to use:**
- Transaction auto-categorized incorrectly
- One-off purchase that doesn't fit rules
- Personal categorization preferences

**How to override:**

1. **Search for Transaction**
   - Text search: "Netflix"
   - Date range filter
   - Amount range filter
   - Bank/Account filter

2. **View Current Categorization**
   - Shows current: Category / Sub-Category
   - Shows direction: In / Out / None

3. **Change Categorization**
   - Select new Category from dropdown
   - Enter new Sub-Category
   - Confirm direction

4. **Save Override**
   - Click **💾 Save Override** button
   - Transaction_key stored in system
   - Override applies on next "Reload Data"

5. **Remove Override** (optional)
   - Find the override in the list
   - Click **🗑️ Remove** button
   - Reverts to rule-based categorization

**💡 Tips:**
- Use for exceptions, not the rule
- Most transactions should be covered by rules
- Override applies to that specific transaction only
- Remove overrides when you create a better rule
- Document unusual overrides for future reference

**Real-world Scenarios:**

| Transaction | Current | Override | Reason |
|-------------|---------|----------|--------|
| "Amazon - Office Supplies" | Shopping | Office Expenses | Specific allocation |
| "Shell Gas Station" | Transport | Fuel | More accurate |
| "Transfer to Savings" | Inter-Transfer | Savings | Personal preference |
| "Refund - Previous Order" | Shopping | Refunds | Income vs expense |

---

### Tab 6️⃣: ⚖️ Non-Transaction Accounts (NEW)

**What it does:** Track balance-only accounts and auto-generate adjustments

**Background:**
- Some accounts only show current balance (no transaction history)
- Examples: Wise, Revolut, Degiro, Sunlife, E-trade
- This tab bridges the gap between transaction and balance accounts

**Sub-Tab A: Manage Accounts**

**Purpose:** Define which categories trigger transfer capture

**Step 1: Select Account**
- Dropdown showing all Balance-type accounts
- Example: "Wise - Chequing", "Revolut - Investments"

**Step 2: View Current Category Links**
- Shows linked category+subcategory pairs
- Format: `(Category,Sub-Category)|(Category2,Sub-Category2)`
- Example: `(Inter-Transfer,Invest)|(Income,Dividend)`

**Step 3: Add Category Link**
1. Enter Category name (e.g., "Inter-Transfer")
2. Enter Sub-Category name (e.g., "Invest")
3. Click **➕ Add Category Link**
4. Category appears in "Current linked pairs"

**Step 4: Remove Category Link** (optional)
- Find the pair you want to remove
- Click **❌** button next to it
- Pair removed immediately

**Example Configuration:**

**Wise Chequing Account:**
- Link: `(Inter-Transfer,Transfer)` - Capture all transfers TO this account
- Link: `(Income,Dividend)` - Capture dividend income

**Revolut Investments:**
- Link: `(Inter-Transfer,Invest)` - Capture investment transfers
- Link: `(Income,Bonus)` - Capture bonus income

**💡 What happens:**
- When you "Reload Data", system finds transactions matching these categories
- Creates mirror transactions in this account with reversed amounts
- These are called "Captured transactions"

**Sub-Tab B: Balance Entries**

**Purpose:** Manually enter account balance snapshots

**Why this matters:**
- Captured transactions might not equal actual balance
- Balance entries create "adjustments" to reconcile
- Final balance = captured transactions + adjustment

**Step 1: Select Account**
- Choose which Balance account to enter balance for
- Example: "Wise - Chequing"

**Step 2: Enter Balance Snapshot**
1. Date picker: Select date of balance
2. Balance amount: Enter current balance (number)
3. Click **💾 Save Balance Entry**

**Step 3: View Existing Entries**
- Table shows all balance snapshots
- Columns: Bank, Account, Date, Balance, Entered_Date
- Shows when each entry was created

**Step 4: Delete Entry** (optional)
1. Select entry from list
2. Click **🗑️ Delete Entry**
3. Entry removed from system

**Example Balance Entry Flow:**

```
Date: 2025-03-03
Balance: 200.00

↓ [Reload Data]

System finds captured transactions up to 2025-03-03
Calculates: actual_balance - captured_sum
If difference exists: creates synthetic "Balance Adjustment" transaction

Date: 2025-04-04
Balance: 250.00

↓ [Reload Data]

System adds new captured transactions from 2025-03-03 to 2025-04-04
Calculates: 250.00 - (previous captured + new captured)
Creates new synthetic adjustment if difference ≠ 0
```

**💡 Best Practices:**
- Enter balance on same day each month (e.g., last day)
- Or enter whenever you check account
- Don't need to enter every month (skip months are OK)
- Used for reconciliation, not daily tracking

**What Gets Generated:**
- **Captured Transactions:** Mirror of categorized transfers (auto-generated)
- **Synthetic Transactions:** Balance adjustments (auto-generated)
- Both appear in Dashboard with `Transaction_Source` indicator

---

### Tab 7️⃣: 📊 Dashboard

**What it does:** Analyze and visualize all transactions

**Components:**

**1. Filters (Top Section)**

**Date Filters:**
- Year selector: 2023, 2024, 2025, etc.
- Month selector: January through December
- Click to apply, auto-updates all charts

**Category Filters:**
- Multi-select: Choose categories to display
- Leave blank for all categories
- Examples: Groceries, Entertainment, Transport, Income, etc.

**Bank/Account Filters:**
- Filter by specific bank
- Filter by account type
- Combine with other filters

**2. Transactions Table**

Shows all transactions matching filters:

| Column | Content | Example |
|--------|---------|---------|
| Date | Transaction date | 2025-11-15 |
| Description | Merchant/transaction name | SUPERMARKET ABC |
| Bank | Source bank | Santander |
| Account | Account type | Chequing |
| Amount | Transaction amount | -45.50 |
| Category | Assigned category | Groceries |
| Sub-Category | Subcategory | Supermarket |
| Type | Direction | Out |
| Source | File/Captured/Synthetic | File |

**Features:**
- Sort by any column (click header)
- Pagination: See 100 rows at a time
- Export: Download filtered data as CSV

**3. Visualizations**

**Pie Chart: Balance by Category**
- Shows total spending per category
- Percentage breakdown
- Hover for amounts
- Interactive: Click legend to toggle categories

**Bar Chart: Monthly Spending Trends**
- X-axis: Month
- Y-axis: Amount spent
- Different colors per category
- Hover for exact amounts

**Line Chart: Cumulative Balance**
- X-axis: Date
- Y-axis: Running total
- Shows account balance over time
- Helpful for trend analysis

**4. Summary Metrics**

At top or bottom of dashboard:

| Metric | Meaning | Example |
|--------|---------|---------|
| Total Income | Sum of "In" transactions | +5000.00 |
| Total Expenses | Sum of "Out" transactions | -2500.00 |
| Net Balance | Income minus expenses | +2500.00 |
| Avg Transaction | Average transaction amount | 125.50 |
| Transaction Count | Number of transactions | 342 |

**How to Use Dashboard:**

**Scenario 1: Monthly Spending Review**
1. Set month filter (e.g., November 2025)
2. View pie chart → spending by category
3. Scroll down → see all transactions
4. Sort by Amount descending → biggest expenses first

**Scenario 2: Category Deep Dive**
1. Select one category filter (e.g., "Groceries")
2. View table with all grocery transactions
3. Check for patterns (same stores repeating)
4. Verify categorization is correct

**Scenario 3: Income Analysis**
1. Set Type filter to "In"
2. View pie chart → income sources
3. Check for missing income (should appear)
4. Verify amounts match bank

**Scenario 4: Trend Analysis**
1. Select date range (multi-month)
2. View line chart → spending trend
3. Identify months with higher/lower spending
4. Make budget decisions

**💡 Tips:**
- Use filters for focused analysis
- Export data for spreadsheet analysis
- Check Dashboard after each consolidation
- Verify automatic categorization is correct
- Look for "Synthetic" transactions - these are balance adjustments

---

## Real-World Workflows

### Workflow 1: Setup New Account (30 minutes)

**Goal:** Start tracking a new bank account

**Steps:**
1. Export transactions from bank website (last 6-12 months)
2. Tab 1 → Upload file with correct bank/account
3. Tab 2 → "Reload Data" to consolidate
4. Tab 3 → Create 5-10 category rules for common expenses
5. Tab 2 → "Reload Data" again to apply rules
6. Tab 5 → Fix any miscategorizations manually
7. Tab 7 → Review dashboard to verify data looks correct

**Time Estimate:** 30-60 minutes first time, 5 minutes for future uploads

---

### Workflow 2: Monthly Financial Review (15 minutes)

**Goal:** Understand spending patterns monthly

**Steps:**
1. Export this month's transactions from each bank
2. Tab 1 → Upload all new files
3. Tab 2 → "Reload Data"
4. Tab 7 → Set month filter to current month
5. Review pie chart → spending by category
6. Scroll table → check for unusual transactions
7. Tab 5 → Fix any miscategorizations
8. Tab 2 → "Reload Data" to finalize
9. Take screenshot/export for records

**Frequency:** Monthly (or weekly)
**Time:** 10-20 minutes

---

### Workflow 3: Create Category Rule Set (30 minutes)

**Goal:** Automate categorization for common patterns

**Steps:**
1. Tab 7 → View dashboard
2. Find "Uncategorized" transactions
3. Tab 3 → Note patterns in uncategorized items
4. Decide categories for each pattern
5. Create rules (or use Tab 4 bulk mapping)
6. Test each rule before saving
7. Tab 2 → "Reload Data" to apply all rules
8. Tab 7 → Verify "Uncategorized" count decreased

**Expected Result:** 80%+ of transactions auto-categorized

---

### Workflow 4: Track Non-Transaction Account (10 minutes)

**Goal:** Monitor Wise/Revolut balance with auto-adjustments

**Steps:**
1. Tab 6 → Manage Accounts sub-tab
2. Select account (e.g., "Wise - Chequing")
3. Add category links (e.g., `Inter-Transfer,Invest`)
4. Tab 6 → Balance Entries sub-tab
5. Enter monthly balance snapshot
6. Tab 2 → "Reload Data"
7. Tab 7 → View dashboard, see captured + synthetic transactions
8. Verify balance matches actual account balance

**Monthly Frequency:** 1 time per month (5 minutes)

---

### Workflow 5: Bulk Import Rules (20 minutes)

**Goal:** Create 50+ categorization rules efficiently

**Preparation:**
1. Compile list of patterns for each category
2. Organize by category (all Entertainment together, etc.)

**Steps:**
1. Tab 4 → Bulk Mapping
2. Paste patterns (one per line)
3. Select category
4. Click "Apply Bulk Rules"
5. Repeat for each category
6. Tab 2 → "Reload Data"
7. Tab 7 → Check coverage of auto-categorization

**Result:** Most transactions auto-categorized without manual work

---

## Tips & Best Practices

### Pattern Naming Tips

**✅ Good Patterns:**
- `*netflix*` - Catches "Netflix Subscription", "NETFLIX", "netflix.com"
- `*whole foods*` - Store name variations
- `*shell*` - Gas station chains
- `salary` - Specific income source

**❌ Bad Patterns:**
- `a` - Too generic, matches everything
- `NETFLIX` - Case matters, won't match "netflix"
- `netflix` - Works but less flexible than `*netflix*`
- `grocery` - Misses "groceries", "supermarket", etc.

---

### Category Structure Tips

**Best Practice:**
- Use 5-10 main categories (Income, Groceries, Transport, Entertainment, etc.)
- Use 2-5 sub-categories per main category
- Keep sub-categories consistent across months

**Example Hierarchy:**
```
Income
├── Salary
├── Bonus
└── Dividends

Groceries
├── Supermarket
├── Restaurant
└── Coffee Shop

Transport
├── Fuel
├── Public
├── Parking
└── Maintenance
```

---

### Consolidation Best Practices

**When to "Reload Data":**
- ✅ After uploading new files
- ✅ After creating new categorization rules
- ✅ After setting manual overrides
- ✅ Weekly or monthly for fresh data

**When NOT to "Reload Data":**
- ❌ Just viewing dashboard (not needed)
- ❌ Searching old transactions (not needed)
- ❌ While another consolidation is running (wait)

**Performance Tips:**
- Reload during off-hours if lots of files
- Archive very old files to separate directory
- Keep current year's files in active directory

---

### Dashboard Analysis Tips

**Quick Wins:**
1. Look at pie chart first - see spending breakdown
2. Sort transactions by Amount descending - find biggest expenses
3. Check for duplicate patterns - negotiate better rates
4. Look at "Uncategorized" - create rules for coverage

**Monthly Goals:**
- [ ] Review income vs expenses
- [ ] Identify top 3 spending categories
- [ ] Find one area to reduce spending
- [ ] Verify all major transactions are categorized

**Yearly Analysis:**
- [ ] Compare each month's totals
- [ ] Calculate average monthly spending per category
- [ ] Identify seasonal expenses
- [ ] Plan budget for next year

---

## FAQ & Troubleshooting

### General Questions

**Q: How often should I upload files?**
A: Weekly or monthly is typical. Upload whenever you want fresh data in the dashboard.

**Q: Can I delete old transactions?**
A: No direct deletion, but you can delete the original Excel file from Tab 1. The consolidated data will update on next "Reload Data".

**Q: Is my data secure?**
A: Data is stored locally in CSV files. No cloud sync or external servers. As secure as your computer.

**Q: Can multiple people use the same app?**
A: Not currently. App is single-user. Consider separate installations for multiple users.

---

### Upload Issues

**Q: "Invalid file format" error**
A:
- Ensure file is .xls or .xlsx
- Not .csv, .pdf, or other formats
- Try opening file in Excel first to verify it's valid
- Save/export again from your bank

**Q: "File already exists" message**
A:
- System detects duplicate file
- Either delete old file first or rename new file
- Helps prevent duplicate transactions in consolidation

**Q: File uploaded but doesn't appear in Tab 2**
A:
- Click "Reload Data" to refresh
- Check Tab 1 again - was upload successful?
- Check browser console for errors (F12)

---

### Categorization Issues

**Q: Rule not matching transactions**
A:
- Use **🔍 Test Rule** to debug
- Check pattern syntax (wildcards needed? case?)
- Verify Direction setting (In/Out/None)
- Check if Priority is high enough
- Reload Data after creating rule

**Q: Rule matching too many transactions**
A:
- Pattern too generic
- Example: `a` matches everything with 'a'
- Use more specific patterns: `*netflix*` not `*net*`
- Test before saving

**Q: Transaction categorized wrong despite rule**
A:
- Manual override takes precedence
- Check if manual override exists in Tab 5
- Check if higher-priority rule exists
- Create more specific rule
- Use manual override for exceptions

**Q: "Uncategorized" transactions not decreasing**
A:
- Rules might not be matching
- Test each rule individually
- Check transaction description spelling
- Add more patterns/rules
- Some transactions might be legitimately uncategorized

---

### Data & Consolidation Issues

**Q: Transaction count drops after consolidation**
A:
- Expected behavior - duplicates removed
- System detects same transaction uploaded twice
- Correct behavior, not a problem

**Q: Balance doesn't match bank**
A:
- Check date filter (should be up-to-date)
- Some transactions might be pending
- Verify all bank files uploaded
- Check for skipped/uncategorized transactions
- Balance = Income - Expenses (check math)

**Q: "Reload Data" is very slow**
A:
- Many large Excel files in raw_files/
- Archive old files to separate directory
- Delete old files not needed
- Split into yearly subdirectories

**Q: Consolidated file looks wrong**
A:
- Check source Excel files are correct format
- Verify bank parser supports your bank
- Check for column name changes in bank export
- Contact support if issue persists

---

### Non-Transaction Accounts Issues

**Q: Captured transactions not appearing**
A:
- Ensure category links configured (Tab 6 sub-tab A)
- Ensure matching transactions exist with that category
- Verify category name spelling matches exactly
- Click "Reload Data" to generate

**Q: Synthetic transactions wrong amount**
A:
- Check balance entry values
- Verify balance is accurate for that date
- Check if transactions exist between balance entries
- Difference = manual_balance - captured_sum

**Q: Balance entry not working**
A:
- Verify account selected correctly
- Check date format (should be YYYY-MM-DD)
- Verify amount is numeric
- Click "Reload Data" to trigger synthesis

---

### Dashboard Issues

**Q: Dashboard shows no data**
A:
- Click "Reload Data" in Tab 2 first
- Check date filters (might be filtering out all data)
- Check category filter (might be filtering everything)
- Verify transactions exist (check Tab 5 table)

**Q: Charts look wrong**
A:
- Clear filters to see all data
- Check if "Synthetic" or "Captured" transactions are correct
- Verify categorization is accurate
- Refresh browser (Ctrl+R or Cmd+R)

**Q: Export/Download not working**
A:
- Different browsers handle exports differently
- Try different browser (Chrome, Firefox, Safari)
- Check pop-up blocker settings
- Try exporting fewer rows

---

### Performance Issues

**Q: App runs very slow**
A:
- Close other browser tabs
- Close other applications
- Restart Streamlit app
- Archive old files
- Check internet connection

**Q: Dashboard takes long to render**
A:
- Add more filters to reduce data
- Export small date ranges
- Refresh page (Ctrl+R)

---

### Getting Help

**If you get stuck:**
1. Check this FAQ section
2. Review relevant tab section above
3. Check ARCHITECTURE_AND_FEATURES.md for technical details
4. Try restarting the app (`Ctrl+C` in terminal, then `streamlit run app.py`)

---

## Common Workflows Quick Reference

| Goal | Tab | Action | Time |
|------|-----|--------|------|
| Add new bank file | 1 | Upload Excel | 2 min |
| Update data | 2 | Click "Reload Data" | 5 min |
| Create category rule | 3 | Enter pattern, test, save | 3 min |
| Bulk import rules | 4 | Paste patterns, apply | 5 min |
| Fix one transaction | 5 | Search, override, save | 2 min |
| Track balance account | 6 | Link categories, enter balance | 3 min |
| View spending | 7 | Set filters, view charts | 5 min |
| Monthly review | All | Upload → Reload → Review → Export | 20 min |

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh Dashboard | `F5` or `Ctrl+R` |
| Open Browser Console | `F12` |
| Restart App | Terminal: `Ctrl+C`, then `streamlit run app.py` |

---

## Feature Support Matrix

| Feature | Supported | Status |
|---------|-----------|--------|
| Multiple banks | ✅ | Yes, 7+ banks |
| Bulk file upload | ✅ | Yes, up to 100 MB |
| Wildcard patterns | ✅ | Yes, flexible matching |
| Manual overrides | ✅ | Yes, per transaction |
| Bulk rule import | ✅ | Yes, up to 100 rules |
| Non-transaction accounts | ✅ | Yes, with synthetic generation |
| Dashboard export | ✅ | Yes, CSV format |
| Multi-user | ❌ | No, single user only |
| Mobile app | ❌ | No, web only |
| Cloud backup | ❌ | No, local storage only |
| API access | ❌ | No, UI only |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-29 | Non-Transaction Accounts feature added |
| 0.9 | 2025-11-15 | Bulk Mapping feature added |
| 0.8 | 2025-11-01 | Manual Overwrites added |
| 0.7 | 2025-10-15 | Category Mapping enhanced |
| 0.1 | 2025-09-01 | Initial release |

---

**Need more help?** Check ARCHITECTURE_AND_FEATURES.md for technical details or reach out for support.

**Ready to start?** Go to "Quick Start (5 Minutes)" section at the top and follow along!

---

**Document Version:** 1.0  
**Last Updated:** November 29, 2025  
**Status:** Production Ready ✅
