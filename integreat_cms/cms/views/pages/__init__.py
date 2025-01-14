"""
This package contains all views related to pages
"""
from .page_tree_view import PageTreeView
from .page_view import PageView
from .page_actions import (
    archive_page,
    restore_page,
    view_page,
    delete_page,
    expand_page_translation_id,
    export_pdf,
    download_xliff,
    upload_xliff,
    move_page,
    grant_page_permission_ajax,
    revoke_page_permission_ajax,
    get_page_order_table_ajax,
    get_new_page_order_table_ajax,
    render_mirrored_page_field,
    post_translation_state_ajax,
)
from .page_sbs_view import PageSideBySideView
from .page_revision_view import PageRevisionView
from .page_xliff_import_view import PageXliffImportView
