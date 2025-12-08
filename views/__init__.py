"""
Views package for Finance Analyzer application.

This package contains modular UI components for each tab of the Streamlit application.
"""

from .upload_files import render_upload_files_tab
from .file_management import render_file_management_tab
from .mapping import render_mapping_tab
from .manual_overwrite import render_manual_overwrite_tab
from .dashboard import render_dashboard_tab

__all__ = [
    "render_upload_files_tab",
    "render_file_management_tab",
    "render_mapping_tab",
    "render_manual_overwrite_tab",
    "render_dashboard_tab",
]
