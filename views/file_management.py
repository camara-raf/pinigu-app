import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    get_uploaded_files_info,
    delete_uploaded_file
)


def render_file_management_tab():
    """Render the File Management tab."""
    st.header("📁 File Management")
    
    files_info = get_uploaded_files_info()
    
    # Status and reload button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.last_load_timestamp:
            st.write(f"**Last loaded:** {st.session_state.last_load_timestamp}")
        else:
            st.write("**Status:** Data needs to be loaded")
    
    with col2:
        # Reload button moved to sidebar
        pass
    
    st.divider()
    
    if files_info:
        # Create dataframe for display
        display_df = pd.DataFrame([
            {
                'File Name': f.get('File Name', ''),
                'Processed': f.get('Processed', ''),
                'Bank': f.get('Bank', ''),
                'Account': f.get('Account', ''),
                'Oldest Date': datetime.strptime(f.get('Oldest Date', ''), '%Y-%m-%d').strftime('%Y-%m-%d') if f.get('Oldest Date') else '',
                'Newest Date': datetime.strptime(f.get('Newest Date', ''), '%Y-%m-%d').strftime('%Y-%m-%d') if f.get('Newest Date') else '',
                'Upload Date': datetime.strptime(f.get('Upload Date', ''), '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') if f.get('Upload Date') else '',
            }
            for f in files_info
        ])
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Delete file buttons
        st.subheader("🗑️ Delete Files")
        for file_info in files_info:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(file_info['File Name'])
            with col2:
                if st.button("Delete", key=f"delete_{file_info['File Name']}"):
                    delete_uploaded_file(file_info['File Name'])
                    st.success(f"✅ Deleted {file_info['File Name']}")
                    st.session_state.data_refresh_needed = True
                    st.rerun()
    else:
        st.info("📭 No files uploaded yet. Go to 'Upload Files' tab to add files.")