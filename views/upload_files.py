import streamlit as st
import pandas as pd
import os
from utils import (
    parse_excel_file, RAW_FILES_DIR, read_bank_mapping, update_file_summary, 
    get_transaction_capable_banks, get_accounts_for_bank, detect_bank_account_pair,
    detect_all_files
)
from utils.logger import get_logger

logger = get_logger()


def render_upload_files_tab():
    """Render the Upload Files tab."""
    st.header("📤 Upload Files")
    
    # Initialize session state for preview management
    if 'show_preview' not in st.session_state:
        st.session_state.show_preview = False
    if 'preview_data' not in st.session_state:
        st.session_state.preview_data = {}
    if 'preview_summaries' not in st.session_state:
        st.session_state.preview_summaries = {}
    if 'use_auto_detect' not in st.session_state:
        st.session_state.use_auto_detect = True  # Auto-detect enabled by default
    if 'file_detection_results' not in st.session_state:
        st.session_state.file_detection_results = {}
    if 'manual_overrides' not in st.session_state:
        st.session_state.manual_overrides = {}  # Maps file_name -> (bank, account)
    
    # Show banner if data needs refresh
    if st.session_state.data_refresh_needed:
        st.warning("⚠️ **New files uploaded.** Go to 'File Management' tab and click 'Reload Data' to refresh the consolidated dataset.")
    
    # Show success message after upload completes
    if st.session_state.get("show_success", False):
        st.success("✅ File(s) uploaded successfully! Ready to upload another file.")
        st.session_state.show_success = False
    
    # MODE SELECTION: Auto-detect vs Manual
    st.subheader("Upload Mode")
    col_mode1, col_mode2 = st.columns(2)
    
    with col_mode1:
        use_auto_detect = st.checkbox(
            "🤖 Auto-detect Bank+Account",
            value=st.session_state.use_auto_detect,
            help="Automatically detect the Bank and Account from file structure"
        )
        st.session_state.use_auto_detect = use_auto_detect
    
    st.divider()
    
    # FILE UPLOADER
    uploaded_file = st.file_uploader(
        "Upload Excel file (.xls, .xlsx, .csv)",
        type=["xls", "xlsx", "csv"],
        help="Select one or more XLS, XLSX or CSV files from your bank",
        key="file_uploader_key",
        accept_multiple_files=True
    )
    
    # When files are selected, analyze them and store preview data
    if len(uploaded_file) > 0 and not st.session_state.show_preview:
        try:
            preview_data = {}
            preview_summaries = {}
            file_detection_results = {}
            manual_overrides = {}
            
            # Create temp file list for auto-detection
            temp_files = []
            for file in uploaded_file:
                temp_file_path = os.path.join(RAW_FILES_DIR, 'temp', file.name)
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                with open(temp_file_path, 'wb') as f:
                    f.write(file.getbuffer())
                temp_files.append((file.name, temp_file_path))
            
            # Auto-detect if enabled
            if use_auto_detect:
                detection_results = detect_all_files([path for _, path in temp_files])
                file_detection_results = {
                    name: detection_results.get(path)
                    for name, path in temp_files
                }
            
            # Process each file
            for file in uploaded_file:
                # Find the temp file path we created
                temp_file_path = next((path for name, path in temp_files if name == file.name), None)
                
                if use_auto_detect and file_detection_results.get(file.name):
                    bank, account, confidence = file_detection_results[file.name]
                    manual_overrides[file.name] = (bank, account)
                else:
                    # Will need manual selection
                    manual_overrides[file.name] = None
                
                # Try to parse the file (will be parsed again during upload, but we need preview)
                try:
                    bank_override, account_override = manual_overrides.get(file.name, (None, None))
                    if bank_override and account_override and temp_file_path:
                        # Pass the temp file path, not the UploadedFile object
                        df, df_file_summary = parse_excel_file(temp_file_path, bank_override, account_override, temp=False)
                        # Drop unnecessary columns for preview
                        df_display = df.drop(columns=['Source_File', 'Category', 'Sub-Category'])
                        preview_data[file.name] = (df_display, len(df), bank_override, account_override)
                        preview_summaries[file.name] = df_file_summary
                except Exception as e:
                    st.warning(f"⚠️ Could not preview '{file.name}': {str(e)}")
            
            st.session_state.preview_data = preview_data
            st.session_state.preview_summaries = preview_summaries
            st.session_state.file_detection_results = file_detection_results
            st.session_state.manual_overrides = manual_overrides
            st.session_state.show_preview = True
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
    
    # PREVIEW AND FILE MANAGEMENT
    if st.session_state.show_preview:
        
        # RE-PARSE CHECK: Ensure previews match current overrides
        for file in uploaded_file:
            file_name = file.name
            bank, account = st.session_state.manual_overrides.get(file_name, (None, None))
            
            # Check if we need to parse/re-parse
            need_parse = False
            current_preview = st.session_state.preview_data.get(file_name)
            
            if bank and account:
                if not current_preview:
                    need_parse = True
                elif len(current_preview) >= 4 and (current_preview[2], current_preview[3]) != (bank, account):
                    need_parse = True
                elif len(current_preview) < 4:
                    # Old format or incomplete
                    need_parse = True
            
            if need_parse:
                temp_file_path = os.path.join(RAW_FILES_DIR, 'temp', file_name)
                if os.path.exists(temp_file_path):
                    try:
                        df, df_file_summary = parse_excel_file(temp_file_path, bank, account, temp=False)
                        df_display = df.drop(columns=['Source_File', 'Category', 'Sub-Category'])
                        st.session_state.preview_data[file_name] = (df_display, len(df), bank, account)
                        st.session_state.preview_summaries[file_name] = df_file_summary
                    except Exception:
                        # If parse fails, clear the preview
                        if file_name in st.session_state.preview_data:
                            del st.session_state.preview_data[file_name]
                        if file_name in st.session_state.preview_summaries:
                            del st.session_state.preview_summaries[file_name]

        st.divider()
        st.subheader("📄 File Preview & Configuration")
        
        # Get list of all files (uploaded)
        # We iterate through the uploaded_file list to maintain order
        for file in uploaded_file:
            file_name = file.name
            
            # Get current state for this file
            detection_result = st.session_state.file_detection_results.get(file_name)
            current_override = st.session_state.manual_overrides.get(file_name)
            
            # Determine effective bank/account
            # If we have an override, use it. Otherwise use detection result.
            if current_override:
                bank, account = current_override
            elif detection_result:
                bank, account, _ = detection_result
            else:
                bank, account = None, None
            
            # Container for this file's section
            with st.container():
                # Layout: Status Icon | File Name | Bank Select | Account Select | Info/Count
                col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 2, 2])
                
                # 1. Status Icon & File Name
                with col1:
                    if bank and account:
                        st.success("✅")
                    else:
                        st.error("⚠️")
                
                with col2:
                    st.write(f"**{file_name}**")
                    if detection_result:
                        _, _, conf = detection_result
                        st.caption(f"Auto-detected ({conf*100:.0f}%)")
                    else:
                        st.caption("Auto-detect failed")

                # 2. Bank & Account Selection
                transaction_combos = get_transaction_capable_banks()
                available_banks = sorted(list(set([combo[0] for combo in transaction_combos])))
                
                with col3:
                    # Determine index for selectbox
                    bank_index = 0
                    if bank in available_banks:
                        bank_index = available_banks.index(bank)
                    
                    selected_bank = st.selectbox(
                        "Bank",
                        available_banks,
                        index=bank_index if bank else None,
                        key=f"bank_select_{file_name}",
                        label_visibility="collapsed",
                        placeholder="Select Bank"
                    )

                with col4:
                    available_accounts = get_accounts_for_bank(selected_bank) if selected_bank else []
                    account_index = 0
                    if account in available_accounts:
                        account_index = available_accounts.index(account)
                        
                    selected_account = st.selectbox(
                        "Account",
                        available_accounts,
                        index=account_index if account and account in available_accounts else None,
                        key=f"account_select_{file_name}",
                        label_visibility="collapsed",
                        placeholder="Select Account"
                    )
                
                # Update manual overrides based on selection
                if selected_bank and selected_account:
                    # If selection changed or wasn't set, update it
                    if (selected_bank, selected_account) != (bank, account):
                        st.session_state.manual_overrides[file_name] = (selected_bank, selected_account)
                        # Trigger rerun to update preview if needed? 
                        # Streamlit reruns on widget change, so next pass will have new values.
                
                # 3. Preview or Warning
                with col5:
                    if bank and account:
                        # Find the preview data for this file
                        preview_item = st.session_state.preview_data.get(file_name)
                        
                        if preview_item:
                            count = preview_item[1] # Index 1 is count in new tuple? No, index 1 is len(df) in new tuple?
                            # Tuple: (df_display, len(df), bank, account)
                            count = preview_item[1]
                            st.info(f"{count} transactions")
                        else:
                            st.warning("Pending parse...")
                    else:
                        st.error("Missing details")

                # 4. Dataframe Preview (Full Width)
                if bank and account:
                    # Find preview data
                    preview_item = st.session_state.preview_data.get(file_name)
                    
                    if preview_item:
                        with st.expander("Show Preview", expanded=False):
                            st.dataframe(preview_item[0].head(5), width='stretch')
                else:
                    st.warning(f"⚠️ Could not auto-detect format for '{file_name}'. Please manually select the Bank and Account above.")
            
            st.divider()
    
    # UPLOAD BUTTON
    st.divider()
    col_button = st.columns(3)
    
    with col_button[1]:
        # Check if ready to upload (all files have bank/account selection)
        all_selections_made = True
        if st.session_state.show_preview:
            for file_name in st.session_state.file_detection_results.keys():
                bank, account = st.session_state.manual_overrides.get(file_name, (None, None))
                if not bank or not account:
                    all_selections_made = False
                    break
        
        upload_button_disabled = len(uploaded_file) == 0 or not st.session_state.show_preview or not all_selections_made
        upload_clicked = st.button("📥 Upload Files", key="upload_button", width="stretch", disabled=upload_button_disabled)
    
    # HANDLE UPLOAD
    if upload_clicked:
        try:
            for file in uploaded_file:
                # Get summary from dict
                df_file_summary = st.session_state.preview_summaries.get(file.name)
                if df_file_summary is None:
                    # Should not happen if logic is correct, but skip if missing
                    continue
                    
                bank, account = st.session_state.manual_overrides[file.name]
                
                # Determine file path based on bank selection
                file_path = os.path.join(RAW_FILES_DIR, str.lower(bank), file.name)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save file to final location
                with open(file_path, 'wb') as f:
                    f.write(file.getbuffer())
                
                # Set file path in summary and update
                df_file_summary["File Name"] = file_path
                update_file_summary(df_file_summary)
            
            # Clean up ALL temp files after successful upload
            temp_dir = os.path.join(RAW_FILES_DIR, 'temp')
            if os.path.exists(temp_dir):
                for temp_file in os.listdir(temp_dir):
                    temp_file_path = os.path.join(temp_dir, temp_file)
                    try:
                        if os.path.isfile(temp_file_path):
                            os.remove(temp_file_path)
                            logger.info(f"Deleted temp file: {temp_file_path}")
                    except Exception as temp_error:
                        logger.warning(f"Could not delete temp file {temp_file}: {temp_error}")
            
            # Clear preview and file uploader state
            st.session_state.show_preview = False
            st.session_state.preview_data = {}
            st.session_state.preview_summaries = {}
            st.session_state.file_detection_results = {}
            st.session_state.manual_overrides = {}
            if "file_uploader_key" in st.session_state:
                del st.session_state.file_uploader_key
            
            # Set session state flags for next rerun
            st.session_state.data_refresh_needed = True
            st.session_state.show_success = True
            st.rerun()
        
        except Exception as upload_error:
            st.error(f"❌ Error uploading files: {str(upload_error)}")

