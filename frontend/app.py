"""
IntelliKnow KMS - Streamlit Admin Dashboard
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Color scheme
COLORS = {
    "frontend": "#3B82F6",  # Blue
    "knowledge": "#10B981",  # Green
    "intent": "#8B5CF6",  # Purple
    "analytics": "#F59E0B",  # Orange
    "background": "#F8FAFC",  # Light gray
    "card_bg": "#FFFFFF",  # White
    "text": "#1E293B",  # Dark slate
    "text_secondary": "#64748B",  # Slate
}

# Page configuration
st.set_page_config(
    page_title="IntelliKnow KMS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .module-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #E2E8F0;
    }
    .frontend-card { border-left: 4px solid #3B82F6; }
    .knowledge-card { border-left: 4px solid #10B981; }
    .intent-card { border-left: 4px solid #8B5CF6; }
    .analytics-card { border-left: 4px solid #F59E0B; }
    .stButton>button {
        border-radius: 8px;
        padding: 8px 16px;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
    }
    h1, h2, h3 { color: #1E293B; }
    .stMetric { background-color: #F1F5F9; border-radius: 8px; padding: 8px; }
    .stExpander { border-radius: 12px; border: 1px solid #E2E8F0; }
</style>
""",
    unsafe_allow_html=True,
)


def api_request(method, endpoint, files=None, data=None, json=None, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if files and isinstance(files, list):
            # Handle multiple files upload - send as list for FastAPI List[UploadFile]
            files_list = []
            for name, file_tuple in files:
                files_list.append((name, (file_tuple[0], file_tuple[1])))

            response = requests.post(url, files=files_list, data=data)
        elif files:
            if method == "POST":
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.put(url, files=files, data=data)
        else:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=json if json is not None else data)
            elif method == "PUT":
                response = requests.put(url, json=json if json is not None else data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                return None, f"Unknown method: {method}"

        if response.status_code < 400:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API. Make sure the backend is running."
    except Exception as e:
        return None, str(e)


def card_container(color_class: str):
    """Create a card container div"""
    return f'<div class="module-card {color_class}">'


# ============== Sidebar Navigation ==============
st.sidebar.markdown(
    """
<style>
.sidebar-title { font-size: 1.4em; font-weight: bold; color: #1E293B; }
.menu-header { font-size: 0.9em; font-weight: bold; color: #64748B; padding: 4px 0; }
.nav-link { 
    display: block; 
    padding: 6px 12px; 
    margin: 2px 0; 
    border-radius: 6px; 
    text-decoration: none;
    color: #1E293B;
}
.nav-link:hover { background: #E2E8F0; }
.nav-link.active { background: #DBEAFE; color: #1D4ED8; font-weight: 500; }
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("🧠 IntelliKnow KMS")
st.sidebar.markdown("---")

# Initialize page state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Override to View/Update page if needed
if st.session_state.get("view_doc_id"):
    page = "View Document"
elif st.session_state.get("update_doc_id"):
    page = "Update Document"
else:
    page = st.session_state.current_page

# Admin Menu
st.sidebar.markdown(
    '<p class="menu-header">👨‍💼 Admin Menu</p>', unsafe_allow_html=True
)

admin_pages = [
    ("📊", "Dashboard"),
    ("📚", "KB Management"),
    ("🎯", "Intent Configuration"),
    ("🔗", "Frontend Integration"),
    ("📈", "Analytics"),
]

for icon, page_name in admin_pages:
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        st.write(icon)
    with col2:
        is_active = page == page_name
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            f"  {page_name}",
            key=f"nav_{page_name}",
            type=btn_type,
            use_container_width=True,
        ):
            st.session_state.current_page = page_name
            st.rerun()
    page = st.session_state.current_page

st.sidebar.markdown("---")

# User Menu
st.sidebar.markdown('<p class="menu-header">👤 User Menu</p>', unsafe_allow_html=True)

user_pages = [("🔍", "Query")]

for icon, page_name in user_pages:
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        st.write(icon)
    with col2:
        is_active = page == page_name
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            f"  {page_name}",
            key=f"nav_{page_name}",
            type=btn_type,
            use_container_width=True,
        ):
            st.session_state.current_page = page_name
            st.rerun()
    page = st.session_state.current_page

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
<div style="font-size: 0.8em; color: #64748B;">
<b>IntelliKnow KMS</b><br>
• RAG-powered query responses<br>
• Multi-frontend integration
</div>
""",
    unsafe_allow_html=True,
)


# ============== Dashboard Page ==============
if page == "Dashboard":
    st.markdown(
        """
    <div style="padding: 20px; border-radius: 12px; border-left: 4px solid #3B82F6; margin-bottom: 20px;">
        <h1 style="color: #1E293B; margin: 0;">🧠 IntelliKnow KMS</h1>
        <p style="color: #64748B; margin: 8px 0 0 0;">Gen AI-powered Knowledge Management System</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Fetch stats
    stats, error = api_request("GET", "/api/analytics/dashboard")

    if error:
        st.error(error)
    else:
        # Metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Queries", stats.get("total_queries", 0))
        with col2:
            st.metric("Today's Queries", stats.get("today_queries", 0))
        with col3:
            st.metric("Accuracy", f"{stats.get('accuracy', 0):.1f}%")
        with col4:
            st.metric("Documents", stats.get("document_count", 0))
        with col5:
            st.metric("Intents", stats.get("intent_count", 0))

        st.markdown("---")

        # Quick actions
        st.markdown(
            """
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px;">
            <h3 style="color: #1E293B; margin: 0 0 12px 0;">⚡ Quick Actions</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success("✅ Backend: Running")
        with col2:
            st.success("✅ Database: Connected")
        with col3:
            if st.button("🔄 Refresh Stats", key="btn_refresh_stats"):
                st.rerun()
        with col4:
            st.info("🚀 System Ready")


# ============== KB Management Page ==============
elif page == "KB Management":
    st.markdown(
        """
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">📚 KB Management</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Manage knowledge base documents and content</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Display persistent operation results (outside tabs so it shows after upload)
    if "operation_result" in st.session_state and st.session_state.operation_result:
        result = st.session_state.operation_result

        if result.get("type") == "success":
            st.markdown(
                f"""
            <div style="background: #DCFCE7; padding: 16px; border-radius: 12px; border-left: 4px solid #22C55E; margin-bottom: 16px;">
                <h4 style="color: #15803D; margin: 0;">{result.get("icon", "✅")} {result.get("message", "Success!")}</h4>
                {f'<p style="color: #166534; margin: 8px 0 0 0;">{result.get("detail", "")}</p>' if result.get("detail") else ""}
            </div>
            """,
                unsafe_allow_html=True,
            )

            if result.get("files"):
                st.markdown(f"**{result.get('file_label', 'Files')}:**")
                for f in result.get("files", []):
                    st.write(f"• {f}")

            if result.get("show_progress", False):
                st.markdown("**📊 Processing Progress:**")
                st.progress(
                    result.get("progress", 0), text=result.get("progress_text", "")
                )

        elif result.get("type") == "error":
            st.markdown(
                f"""
            <div style="background: #FEE2E2; padding: 16px; border-radius: 12px; border-left: 4px solid #EF4444; margin-bottom: 16px;">
                <h4 style="color: #DC2626; margin: 0;">❌ {result.get("message", "Error!")}</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if result.get("errors"):
                for e in result.get("errors", []):
                    st.error(e)

        # Clear operation result after displaying (use expander for manual dismiss)
        with st.expander("📋 Operation Details", expanded=True):
            st.write(result.get("message", ""))
            if result.get("files"):
                st.write(f"**{result.get('file_label', 'Files')}:**")
                for f in result.get("files", []):
                    st.write(f"  • {f}")
            if result.get("errors"):
                st.write("**Errors:**")
                for e in result.get("errors", []):
                    st.write(f"  • {e}")
            if st.button("✅ Dismiss", key="btn_dismiss_result"):
                st.session_state.operation_result = None
                st.rerun()
    else:
        st.session_state.operation_result = None

    tab1, tab2 = st.tabs(["📋 Document List", "📤 Upload Documents"])

    with tab1:
        # Initialize selection state
        if "selected_docs" not in st.session_state:
            st.session_state.selected_docs = set()
        if "show_reparse_modal" not in st.session_state:
            st.session_state.show_reparse_modal = False
        if "show_edit_modal" not in st.session_state:
            st.session_state.show_edit_modal = False
        if "edit_doc_id" not in st.session_state:
            st.session_state.edit_doc_id = None

        # Fetch document settings for default values
        doc_settings, _ = api_request("GET", "/api/intents/settings/document")
        default_chunk_size = (
            doc_settings.get("chunk_size", 256) if doc_settings else 256
        )
        default_chunk_overlap = (
            doc_settings.get("chunk_overlap", 50) if doc_settings else 50
        )

        # Fetch intents for filter
        intents, _ = api_request("GET", "/api/intents")
        intent_options = {"All Intents": None}
        if intents:
            for intent in intents:
                intent_options[intent["name"]] = intent["id"]

        # Search and Filter Bar
        st.markdown(
            """
        <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="color: #10B981; margin: 0 0 12px 0;">🔍 Search & Filter</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col_search, col_format, col_intent, col_status = st.columns(4)

        with col_search:
            search_query = st.text_input(
                "Search by name", placeholder="Enter document name..."
            )

        with col_format:
            format_options = ["All Formats", "pdf", "docx"]
            selected_format = st.selectbox("Format", format_options)

        with col_intent:
            selected_intent_name = st.selectbox(
                "Intent Space", list(intent_options.keys())
            )

        with col_status:
            status_options = ["All Status", "completed", "pending", "failed"]
            selected_status = st.selectbox("Status", status_options)

        # Fetch documents with filters
        params = []
        if selected_format != "All Formats":
            params.append(f"file_type={selected_format}")
        if selected_status != "All Status":
            params.append(f"status={selected_status}")
        if intent_options[selected_intent_name]:
            params.append(f"intent_id={intent_options[selected_intent_name]}")
        if search_query:
            params.append(f"search={search_query}")

        query_string = "&".join(params) if params else ""
        docs, error = api_request("GET", f"/api/documents?{query_string}")

        if error:
            st.error(error)
        else:
            st.markdown(f"**Total: {docs.get('total', 0)} documents found**")

            if docs.get("items"):
                # Helper functions
                def format_status(status):
                    if status == "completed":
                        return "✅ Processed"
                    elif status == "pending":
                        return "⏳ Pending"
                    elif status == "failed":
                        return "❌ Error"
                    return status

                def format_size(size_bytes):
                    if size_bytes < 1024:
                        return f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        return f"{size_bytes / 1024:.1f} KB"
                    else:
                        return f"{size_bytes / (1024 * 1024):.1f} MB"

                # Clear stale selections and build docs data map
                doc_ids = [d["id"] for d in docs["items"]]
                st.session_state.selected_docs = (
                    st.session_state.selected_docs.intersection(set(doc_ids))
                )

                # Store document data for file list display
                docs_data = {}
                for d in docs["items"]:
                    docs_data[d["id"]] = {
                        "name": d["name"],
                        "size": d["file_size"],
                        "status": d["status"],
                    }
                st.session_state.selected_docs_data = docs_data

                # Table header
                header_cols = st.columns([0.5, 3, 1.5, 1, 1, 1.5, 1.5, 1])
                headers = [
                    "☑️",
                    "Document Name",
                    "Upload Date",
                    "Format",
                    "Size",
                    "Intent",
                    "Status",
                    "Actions",
                ]
                for i, h in enumerate(headers):
                    header_cols[i].write(f"**{h}**")

                st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)

                # Display document rows
                for d in docs["items"]:
                    doc_id = d["id"]
                    is_selected = doc_id in st.session_state.selected_docs
                    checkbox_key = f"doc_cb_{doc_id}"

                    row_cols = st.columns([0.5, 3, 1.5, 1, 1, 1.5, 1.5, 1.5])

                    with row_cols[0]:
                        checked = st.checkbox("", value=is_selected, key=checkbox_key)
                        if checked:
                            st.session_state.selected_docs.add(doc_id)
                        else:
                            st.session_state.selected_docs.discard(doc_id)

                    with row_cols[1]:
                        st.write(f"**{d['name']}**")
                    with row_cols[2]:
                        # Format date with time (HH:MM:SS)
                        created_at = d.get("created_at", "")
                        if created_at:
                            # Format: 2024-01-15T10:30:45 -> Jan 15, 2024 10:30:45
                            try:
                                dt = datetime.fromisoformat(
                                    created_at.replace("Z", "+00:00")
                                )
                                formatted_date = dt.strftime("%b %d, %Y %H:%M:%S")
                            except:
                                formatted_date = created_at[:19].replace("T", " ")
                        else:
                            formatted_date = "-"
                        st.write(formatted_date)
                    with row_cols[3]:
                        st.write(d["file_type"].upper())
                    with row_cols[4]:
                        st.write(format_size(d["file_size"]))
                    with row_cols[5]:
                        st.write(d.get("intent_name", "-"))
                    with row_cols[6]:
                        status = d.get("status", "unknown")
                        if status == "failed":
                            with st.expander("❌ Error"):
                                error_msg = d.get("error_message", "Unknown error")
                                st.error(
                                    error_msg if error_msg else "Processing failed"
                                )
                                # Quick fix button
                                if st.button(f"🔄 Fix", key=f"fix_{doc_id}"):
                                    fix_result, fix_err = api_request(
                                        "POST",
                                        f"/api/documents/{doc_id}/reparse",
                                        data={},
                                    )
                                    if fix_err:
                                        st.error(f"Failed: {fix_err}")
                                    else:
                                        st.success("Document queued for reprocessing")
                                        st.rerun()
                        elif status == "processing":
                            st.warning("⏳ Processing...")
                        else:
                            st.write(format_status(status))

                    with row_cols[7]:
                        if st.button("👁️ View", key=f"view_{doc_id}"):
                            st.session_state.view_doc_id = doc_id
                            st.rerun()

                st.markdown("---")

                # Batch actions section
                selected_count = len(st.session_state.selected_docs)
                if selected_count > 0:
                    # Check batch limit
                    if selected_count > 20:
                        st.warning(
                            f"⚠️ Maximum 20 documents can be processed at once. {selected_count} selected."
                        )

                    st.markdown(
                        f"""
                    <div style="background: #EFF6FF; padding: 12px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-bottom: 12px;">
                        <span style="color: #1D4ED8; font-weight: bold;">☑️ {selected_count} document(s) selected</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Action buttons
                    col_reparse, col_edit, col_delete = st.columns(3)

                    with col_reparse:
                        if st.button(
                            f"🔄 Reparse ({min(selected_count, 20)})",
                            key="btn_reparse_docs",
                            help="Re-parse selected documents",
                        ):
                            st.session_state.show_reparse_modal = True
                            st.rerun()

                    with col_edit:
                        if selected_count == 1:
                            doc_id = list(st.session_state.selected_docs)[0]
                            if st.button(
                                "✏️ Edit Content",
                                key="btn_edit_content",
                                help="Edit document content",
                            ):
                                st.session_state.show_edit_modal = True
                                st.session_state.edit_doc_id = doc_id
                                st.rerun()
                        else:
                            st.button(
                                "✏️ Edit Content",
                                disabled=True,
                                key="btn_edit_disabled",
                                help="Select only one document to edit",
                            )

                    with col_delete:
                        if st.button(
                            f"🗑️ Delete ({selected_count})",
                            key="btn_delete_docs",
                            type="secondary",
                        ):
                            deleted = 0
                            failed = 0
                            deleted_files = []
                            failed_files = []

                            # Get document names before deleting
                            docs_data = st.session_state.get("selected_docs_data", {})

                            for doc_id in list(st.session_state.selected_docs):
                                doc_name = docs_data.get(doc_id, {}).get(
                                    "name", f"Document {doc_id}"
                                )
                                result, err = api_request(
                                    "DELETE", f"/api/documents/{doc_id}"
                                )
                                if err:
                                    failed += 1
                                    failed_files.append(doc_name)
                                else:
                                    deleted += 1
                                    deleted_files.append(doc_name)
                                    st.session_state.selected_docs.discard(doc_id)

                            # Store result in session state
                            if deleted > 0:
                                st.session_state.operation_result = {
                                    "type": "success",
                                    "icon": "🗑️",
                                    "message": f"{deleted} document(s) deleted successfully!",
                                    "files": deleted_files,
                                    "file_label": "🗑️ Deleted Files",
                                }

                            if failed > 0:
                                st.session_state.operation_result = {
                                    "type": "error",
                                    "message": f"{failed} document(s) failed to delete",
                                    "errors": failed_files,
                                }

                            st.rerun()
                else:
                    st.info(
                        "☐ Select documents using checkboxes to enable batch actions"
                    )

                # Reparse Modal
                if st.session_state.show_reparse_modal:
                    with st.container():
                        st.markdown(
                            """
                        <div style="background: #FEF3C7; padding: 16px; border-radius: 12px; border: 2px solid #F59E0B; margin-top: 16px;">
                            <h4 style="color: #D97706; margin: 0 0 12px 0;">🔄 Batch Reparse Documents</h4>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        st.write(f"Selected: {selected_count} document(s)")

                        # Reparse options
                        reparse_option = st.radio(
                            "Reparse Option",
                            [
                                "Only reparse text (keep chunks)",
                                "Re-chunk and re-vectorize",
                            ],
                            index=1,
                            horizontal=True,
                            label_visibility="collapsed",
                        )
                        rechunk = reparse_option == "Re-chunk and re-vectorize"

                        # Chunk settings
                        st.write("**Chunk Configuration:**")
                        col_size, col_overlap = st.columns(2)
                        with col_size:
                            chunk_size = st.number_input(
                                "Chunk Size",
                                min_value=50,
                                max_value=2000,
                                value=default_chunk_size,
                                step=16,
                                key="reparse_chunk_size",
                            )
                        with col_overlap:
                            chunk_overlap = st.number_input(
                                "Chunk Overlap",
                                min_value=0,
                                max_value=500,
                                value=default_chunk_overlap,
                                step=10,
                                key="reparse_chunk_overlap",
                            )

                        # Action buttons
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button(
                                "✅ Start Reparsing",
                                key="btn_start_reparse",
                                type="primary",
                            ):
                                # Get document names
                                docs_data = st.session_state.get(
                                    "selected_docs_data", {}
                                )
                                selected_doc_ids = list(st.session_state.selected_docs)[
                                    :20
                                ]
                                selected_names = [
                                    docs_data.get(did, {}).get(
                                        "name", f"Document {did}"
                                    )
                                    for did in selected_doc_ids
                                ]

                                # Call batch reparse API
                                payload = {
                                    "document_ids": selected_doc_ids,
                                    "chunk_size": chunk_size,
                                    "chunk_overlap": chunk_overlap,
                                    "rechunk": rechunk,
                                }
                                result, err = api_request(
                                    "POST", "/api/documents/reparse-batch", data=payload
                                )

                                st.session_state.show_reparse_modal = False

                                if err:
                                    st.session_state.operation_result = {
                                        "type": "error",
                                        "message": f"Failed to queue documents: {err}",
                                    }
                                else:
                                    success_count = result.get("success_count", 0)
                                    failed_count = result.get("failed_count", 0)
                                    results = result.get("results", [])

                                    # Get queued file names
                                    queued_files = [
                                        r.get("document_name", "Unknown")
                                        for r in results
                                        if r.get("status") == "queued"
                                    ]
                                    failed_files = [
                                        f"{r.get('document_name', 'Unknown')}: {r.get('error', 'Unknown')}"
                                        for r in results
                                        if r.get("status") == "failed"
                                    ]

                                    if success_count > 0:
                                        st.session_state.operation_result = {
                                            "type": "success",
                                            "icon": "🔄",
                                            "message": f"{success_count} document(s) queued for reprocessing!",
                                            "detail": "Processing will begin automatically...",
                                            "files": queued_files,
                                            "file_label": "📄 Queued Files",
                                            "show_progress": True,
                                            "progress": 0,
                                            "progress_text": f"0/{success_count} completed, 0 failed, {success_count} pending...",
                                        }
                                    elif failed_count > 0:
                                        st.session_state.operation_result = {
                                            "type": "error",
                                            "message": f"{failed_count} document(s) failed to queue",
                                            "errors": failed_files,
                                        }
                                    else:
                                        st.session_state.operation_result = None

                                st.rerun()

                        with col_cancel:
                            if st.button("❌ Cancel", key="cancel_reparse_btn"):
                                st.session_state.show_reparse_modal = False
                                st.rerun()

                # Edit Modal
                if st.session_state.show_edit_modal and st.session_state.edit_doc_id:
                    doc_id = st.session_state.edit_doc_id

                    # Fetch document content
                    content_result, content_err = api_request(
                        "GET", f"/api/documents/{doc_id}/content"
                    )

                    if content_err:
                        st.error(f"Failed to load content: {content_err}")
                    else:
                        with st.container():
                            st.markdown(
                                """
                            <div style="background: #FAF5FF; padding: 16px; border-radius: 12px; border: 2px solid #8B5CF6; margin-top: 16px;">
                                <h4 style="color: #8B5CF6; margin: 0 0 12px 0;">📝 Edit Document Content</h4>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            st.write(
                                f"**Document:** {content_result.get('document_name', 'Unknown')}"
                            )
                            st.write(
                                f"**Word Count:** {content_result.get('word_count', 0)}"
                            )

                            # Edit options
                            edit_option = st.radio(
                                "Edit Option",
                                [
                                    "Only reparse text (keep chunks)",
                                    "Re-chunk and re-vectorize",
                                ],
                                index=1,
                                horizontal=True,
                                label_visibility="collapsed",
                                key="edit_rechunk_option",
                            )
                            edit_rechunk = edit_option == "Re-chunk and re-vectorize"

                            # Content editor (using text_area as rich text editor placeholder)
                            st.write("**Content (editable):**")
                            new_content = st.text_area(
                                "Edit document content",
                                value=content_result.get("content", ""),
                                height=400,
                                label_visibility="collapsed",
                                key="edit_content_area",
                            )

                            # Chunk settings
                            if edit_rechunk:
                                st.write("**Chunk Configuration:**")
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    edit_chunk_size = st.number_input(
                                        "Chunk Size",
                                        min_value=50,
                                        max_value=2000,
                                        value=default_chunk_size,
                                        step=16,
                                        key="edit_chunk_size",
                                    )
                                with col_e2:
                                    edit_chunk_overlap = st.number_input(
                                        "Chunk Overlap",
                                        min_value=0,
                                        max_value=500,
                                        value=default_chunk_overlap,
                                        step=10,
                                        key="edit_chunk_overlap",
                                    )
                            else:
                                edit_chunk_size = default_chunk_size
                                edit_chunk_overlap = default_chunk_overlap

                            # Action buttons
                            col_save, col_close = st.columns(2)
                            with col_save:
                                if st.button(
                                    "💾 Save & Reprocess",
                                    key="btn_save_reprocess",
                                    type="primary",
                                ):
                                    word_count = len(new_content.split())
                                    payload = {
                                        "content": new_content,
                                        "chunk_size": edit_chunk_size,
                                        "chunk_overlap": edit_chunk_overlap,
                                        "rechunk": edit_rechunk,
                                    }
                                    result, err = api_request(
                                        "PUT",
                                        f"/api/documents/{doc_id}/content",
                                        data=payload,
                                    )

                                    st.session_state.show_edit_modal = False
                                    st.session_state.edit_doc_id = None

                                    if err:
                                        st.session_state.operation_result = {
                                            "type": "error",
                                            "message": f"Failed to update document: {err}",
                                        }
                                    else:
                                        st.session_state.operation_result = {
                                            "type": "success",
                                            "icon": "✏️",
                                            "message": "Document content updated!",
                                            "detail": f"Word count: {word_count} | Processing queued...",
                                            "files": [
                                                content_result.get(
                                                    "document_name", "Unknown"
                                                )
                                            ],
                                            "file_label": "📝 Document",
                                            "show_progress": True,
                                            "progress": 0,
                                            "progress_text": "0/1 completed, 0 failed, 1 pending...",
                                        }
                                    st.rerun()

                            with col_close:
                                if st.button("❌ Cancel", key="cancel_edit_btn"):
                                    st.session_state.show_edit_modal = False
                                    st.session_state.edit_doc_id = None
                                    st.rerun()
            else:
                st.info("No documents found. Try adjusting your search or filters.")

    with tab2:
        st.markdown(
            """
        <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="color: #10B981; margin: 0;">📤 Upload Documents</h4>
            <p style="color: #64748B; margin: 8px 0 0 0;">Supported formats: PDF, DOCX | Upload multiple files at once</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Initialize session state
        if "upload_in_progress" not in st.session_state:
            st.session_state.upload_in_progress = False
        if "uploaded_doc_ids" not in st.session_state:
            st.session_state.uploaded_doc_ids = []
        if "pending_files" not in st.session_state:
            st.session_state.pending_files = []
        if "duplicate_files" not in st.session_state:
            st.session_state.duplicate_files = []

        # Fetch existing documents for duplicate check (ALL documents, not just completed)
        existing_docs, _ = api_request("GET", "/api/documents?limit=1000")
        existing_names = set()
        existing_doc_map = {}
        if existing_docs and existing_docs.get("items"):
            for d in existing_docs["items"]:
                # Include ALL documents for duplicate detection
                existing_names.add(d["name"].lower())
                existing_doc_map[d["name"].lower()] = d

        uploaded_files = st.file_uploader(
            "Choose files (multiple allowed)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX. You can select multiple files.",
        )

        intents, _ = api_request("GET", "/api/intents")
        intent_options = {}
        if intents:
            for intent in intents:
                intent_options[intent["name"]] = intent["id"]

        # Make intent selection required
        intent_names = list(intent_options.keys())
        selected_intent_name = st.selectbox(
            "Intent Space (Required)",
            options=["-- Select an Intent --"] + intent_names,
            index=0,
        )

        if uploaded_files:
            # Check for duplicates and invalid files
            duplicates = []
            new_files = []
            invalid_files = []

            # Get base names (without extension) for better duplicate detection
            existing_base_names = set()
            for name in existing_names:
                base_name = ".".join(name.split(".")[:-1]) if "." in name else name
                existing_base_names.add(base_name.lower())

            for f in uploaded_files:
                file_ext = f.name.split(".")[-1].lower() if "." in f.name else ""
                base_name = (
                    ".".join(f.name.split(".")[:-1]) if "." in f.name else f.name
                )

                if file_ext not in ["pdf", "docx"]:
                    invalid_files.append(f)
                elif f.name.lower() in existing_names:
                    duplicates.append(f)
                elif base_name.lower() in existing_base_names:
                    # Same base name but different extension - treat as new
                    new_files.append(f)
                else:
                    new_files.append(f)

            if invalid_files:
                st.error(f"❌ {len(invalid_files)} file(s) have invalid format:")
                for inv in invalid_files:
                    st.write(f"  - **{inv.name}** (not PDF or DOCX)")
                st.warning("Only PDF and DOCX files are supported")

            if duplicates:
                st.warning(f"⚠️ {len(duplicates)} file(s) already exist:")
                for dup in duplicates:
                    existing = existing_doc_map.get(dup.name.lower(), {})
                    st.write(
                        f"  - **{dup.name}** (exists, status: {existing.get('status', 'unknown')})"
                    )
                st.info(
                    "Select 'Upload All' to overwrite existing files, or remove duplicates from selection"
                )

            if new_files:
                st.write(f"**New files: {len(new_files)}**")
                for f in new_files[:5]:
                    st.write(f"  - {f.name}")
                if len(new_files) > 5:
                    st.write(f"  ... and {len(new_files) - 5} more")

            st.session_state.pending_files = new_files
            st.session_state.duplicate_files = duplicates

        # Check if upload is in progress
        if st.session_state.upload_in_progress:
            st.info("⏳ Upload in progress. Please wait...")

            # Poll processing status
            completed = 0
            failed = 0
            for doc_id in st.session_state.uploaded_doc_ids:
                status_result, _ = api_request("GET", f"/api/documents/{doc_id}")
                if status_result:
                    if status_result.get("status") == "completed":
                        completed += 1
                    elif status_result.get("status") == "failed":
                        failed += 1

            total = len(st.session_state.uploaded_doc_ids)
            progress = (completed + failed) / total if total > 0 else 0
            st.progress(
                progress,
                text=f"Processing: {completed} completed, {failed} failed, {total - completed - failed} pending...",
            )

            # All done
            if completed + failed >= total:
                st.session_state.upload_in_progress = False
                st.session_state.uploaded_doc_ids = []
                st.rerun()
        else:
            all_files = uploaded_files or []
            pending = st.session_state.pending_files
            disabled = not (
                all_files and selected_intent_name != "-- Select an Intent --"
            )

            if st.button(
                "📤 Upload All Documents",
                key="btn_upload_all",
                type="primary",
                disabled=disabled,
            ):
                if not all_files:
                    st.error("Please select at least one file")
                elif selected_intent_name == "-- Select an Intent --":
                    st.error(
                        "Please select an Intent Space to associate with these documents"
                    )
                else:
                    files_to_upload = []

                    # Handle new files
                    for f in pending:
                        files_to_upload.append(("new", f))

                    # Handle duplicates - delete old and upload new
                    for dup in st.session_state.duplicate_files:
                        files_to_upload.append(("duplicate", dup))

                    if not files_to_upload:
                        st.warning("No files to upload")
                    else:
                        # Delete duplicates first
                        deleted_count = 0
                        for _, dup in files_to_upload:
                            if dup.name.lower() in existing_doc_map:
                                old_doc = existing_doc_map[dup.name.lower()]
                                result, err = api_request(
                                    "DELETE", f"/api/documents/{old_doc['id']}"
                                )
                                if not err:
                                    deleted_count += 1

                        if deleted_count > 0:
                            st.info(f"Removing {deleted_count} existing file(s)...")

                        # Upload all files
                        with st.spinner("📤 Uploading files..."):
                            files_data = []
                            for file_type, f in files_to_upload:
                                files_data.append(("files", (f.name, f.getvalue())))

                            data = {"intent_id": intent_options[selected_intent_name]}

                            result, error = api_request(
                                "POST",
                                "/api/documents/upload-batch",
                                files=files_data,
                                data=data,
                            )

                        if error:
                            st.session_state.operation_result = {
                                "type": "error",
                                "message": f"Upload failed: {error}",
                            }
                        else:
                            successful = result.get("successful", 0)
                            failed_count = result.get("failed", 0)
                            results = result.get("results", [])

                            # Show success message with file list
                            if successful > 0:
                                uploaded_files_list = [
                                    r.get("name")
                                    for r in results
                                    if r.get("status") == "uploaded"
                                ]
                                st.session_state.operation_result = {
                                    "type": "success",
                                    "icon": "✅",
                                    "message": f"{successful} document(s) uploaded!",
                                    "detail": "Processing will begin automatically...",
                                    "files": uploaded_files_list,
                                    "file_label": "📤 Uploaded Files",
                                    "show_progress": True,
                                    "progress": 0,
                                    "progress_text": f"0/{successful} completed, 0 failed, {successful} pending...",
                                }

                            if failed_count > 0:
                                failed_files = [
                                    f"{r.get('name')}: {r.get('error', 'Unknown')}"
                                    for r in results
                                    if r.get("status") == "failed"
                                ]
                                st.session_state.operation_result = {
                                    "type": "error",
                                    "message": f"{failed_count} document(s) failed to upload",
                                    "errors": failed_files,
                                }

                            if successful > 0:
                                # Set upload state
                                doc_ids = [
                                    r.get("id")
                                    for r in results
                                    if r.get("status") == "uploaded"
                                ]
                                st.session_state.upload_in_progress = True
                                st.session_state.uploaded_doc_ids = doc_ids
                                st.session_state.pending_files = []
                                st.session_state.duplicate_files = []

                            st.rerun()

        # Show hint if no intent selected
        if uploaded_files and selected_intent_name == "-- Select an Intent --":
            st.warning("⚠️ Please select an Intent Space to upload documents")


# ============== View Document Page ==============
elif page == "View Document":
    doc_id = st.session_state.get("view_doc_id")

    if st.button("← Back to Document List", key="btn_back_view"):
        st.session_state.view_doc_id = None
        st.rerun()

    st.markdown(
        """
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">📄 View Document</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if doc_id:
        doc_detail, err = api_request("GET", f"/api/documents/{doc_id}")

        if err:
            st.error(err)
        else:

            def format_size(size_bytes):
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"

            def format_status(status):
                if status == "completed":
                    return "✅ Processed"
                elif status == "pending":
                    return "⏳ Pending"
                elif status == "failed":
                    return "❌ Error"
                return status

            # Display document details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    """
                <div style="background: #F0FDF4; padding: 16px; border-radius: 12px;">
                    <h4 style="color: #10B981; margin: 0 0 12px 0;">Document Information</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.write(f"**ID:** {doc_detail.get('id')}")
                st.write(f"**Name:** {doc_detail.get('name')}")
                st.write(f"**Format:** {doc_detail.get('file_type', '').upper()}")
                st.write(f"**Intent:** {doc_detail.get('intent_name', '-')}")

            with col2:
                st.markdown(
                    """
                <div style="background: #F0FDF4; padding: 16px; border-radius: 12px;">
                    <h4 style="color: #10B981; margin: 0 0 12px 0;">Processing Status</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.write(f"**Size:** {format_size(doc_detail.get('file_size', 0))}")
                st.write(f"**Status:** {format_status(doc_detail.get('status', ''))}")
                st.write(f"**Created:** {doc_detail.get('created_at', '')[:19]}")
                st.write(f"**Updated:** {doc_detail.get('updated_at', '')[:19]}")

            st.markdown("---")

            # Action buttons
            col_download, col_update = st.columns([1, 3])
            with col_download:
                # Download button
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/api/documents/{doc_id}/download"
                    )
                    if response.status_code == 200:
                        st.download_button(
                            label="📥 Download Document",
                            data=response.content,
                            file_name=doc_detail.get("name", "document"),
                            mime="application/octet-stream",
                        )
                    else:
                        st.warning("Download not available")
                except Exception as e:
                    st.warning(f"Download error: {e}")

            with col_update:
                if st.button(
                    "🔄 Update Document", key="btn_update_doc", type="primary"
                ):
                    st.session_state.update_doc_id = doc_id
                    st.session_state.view_doc_id = None
                    st.rerun()

            # Document Content
            st.markdown("---")
            st.markdown(
                """
            <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-top: 16px;">
                <h4 style="color: #10B981; margin: 0 0 12px 0;">📝 Document Content</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Fetch content
            with st.spinner("Loading document content..."):
                content_data, content_err = api_request(
                    "GET", f"/api/documents/{doc_id}/content"
                )

            if content_err:
                st.warning("⚠️ Unable to extract document content")
                st.info(
                    "The document may be encrypted, password-protected, or in an unsupported format."
                )
                st.caption(f"Error: {content_err}")
            elif content_data:
                word_count = content_data.get("word_count", 0)
                content = content_data.get("content", "")

                if not content or content.startswith("[Unable to"):
                    st.warning("⚠️ Document content could not be extracted")
                    st.info(
                        "The document may be encrypted, password-protected, or in an unsupported format."
                    )
                else:
                    st.success(f"Word count: {word_count}")

                    # Show preview or full content
                    if st.checkbox("Show Full Content", value=False):
                        st.text_area(
                            "Document Text",
                            value=content,
                            height=500,
                            label_visibility="collapsed",
                        )
                    else:
                        st.text_area(
                            "Preview (first 500 characters)",
                            value=content_data.get("preview", content[:500]),
                            height=300,
                            label_visibility="collapsed",
                        )
    else:
        st.warning("No document selected")
        st.session_state.view_doc_id = None


# ============== Update Document Page ==============
elif page == "Update Document":
    doc_id = st.session_state.get("update_doc_id")

    if st.button("← Back to Document List", key="btn_back_update"):
        st.session_state.update_doc_id = None
        st.rerun()

    st.markdown(
        """
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">🔄 Update Document</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if doc_id:
        # Get current document info
        doc_detail, err = api_request("GET", f"/api/documents/{doc_id}")

        if err:
            st.error(err)
        else:
            st.info(f"Current document: **{doc_detail.get('name')}**")
            st.info(f"Current intent: **{doc_detail.get('intent_name', 'None')}**")

            st.markdown(
                """
            <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin: 16px 0;">
                <h4 style="color: #10B981; margin: 0;">Upload New File</h4>
                <p style="color: #64748B; margin: 8px 0 0 0;">Select a new PDF or DOCX file to replace the current document</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Intent selection
            intents, _ = api_request("GET", "/api/intents")
            intent_options = {}
            if intents:
                for intent in intents:
                    intent_options[intent["name"]] = intent["id"]

            intent_names = list(intent_options.keys())
            current_intent = doc_detail.get("intent_name", "")
            current_index = (
                intent_names.index(current_intent)
                if current_intent in intent_names
                else 0
            )

            selected_intent_name = st.selectbox(
                "Intent Space", options=intent_names, index=current_index
            )

            # File upload
            new_file = st.file_uploader(
                "Choose new file (PDF or DOCX)",
                type=["pdf", "docx"],
                help="Select a new file to replace the current document",
            )

            if new_file:
                st.success(f"Selected: {new_file.name}")

                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button(
                        "📤 Replace Document", key="btn_replace_doc", type="primary"
                    ):
                        with st.spinner("Replacing document..."):
                            # Delete old document
                            delete_result, del_err = api_request(
                                "DELETE", f"/api/documents/{doc_id}"
                            )

                            if del_err:
                                st.error(f"Delete failed: {del_err}")
                            else:
                                # Upload new file
                                files_data = [
                                    ("files", (new_file.name, new_file.getvalue()))
                                ]
                                data = {
                                    "intent_id": intent_options[selected_intent_name]
                                }

                                result, upload_err = api_request(
                                    "POST",
                                    "/api/documents/upload-batch",
                                    files=files_data,
                                    data=data,
                                )

                                if upload_err:
                                    st.error(f"Upload failed: {upload_err}")
                                else:
                                    st.success("✅ Document replaced successfully!")
                                    st.session_state.update_doc_id = None
                                    st.rerun()
            else:
                st.info("Please select a new file to upload")
    else:
        st.warning("No document selected for update")
        st.session_state.update_doc_id = None


# ============== Intent Configuration Page ==============
elif page == "Intent Configuration":
    st.markdown(
        """
    <div class="intent-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #8B5CF6; margin-bottom: 20px;">
        <h2 style="color: #8B5CF6; margin: 0;">🎯 Intent Configuration</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Create and manage intent spaces with keywords for classification accuracy</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state for confirmations
    if "confirm_save" not in st.session_state:
        st.session_state.confirm_save = None
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None
    if "pending_edit" not in st.session_state:
        st.session_state.pending_edit = None

    # Fetch intents and stats
    intents, error = api_request("GET", "/api/intents")
    intent_stats, _ = api_request("GET", "/api/analytics/intents")

    if error:
        st.error(error)
    else:
        # Build accuracy map
        accuracy_map = {}
        if intent_stats:
            for stat in intent_stats:
                accuracy_map[stat.get("intent_name")] = stat.get("accuracy", 0)

        st.markdown(
            f"""
        <div style="background: #FAF5FF; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;">
            <span style="color: #8B5CF6; font-weight: bold;">Total: {len(intents)} intent spaces</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Handle confirmation dialogs
        if st.session_state.confirm_save == "show":
            intent = st.session_state.pending_edit
            st.warning(f"Confirm update for intent '{intent['name']}'?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm", key=f"confirm_save_{intent['id']}"):
                    keywords_list = [
                        k.strip()
                        for k in st.session_state[f"keywords_{intent['id']}"].split(",")
                        if k.strip()
                    ]
                    result, err = api_request(
                        "PUT",
                        f"/api/intents/{intent['id']}",
                        json={
                            "name": st.session_state[f"name_{intent['id']}"],
                            "description": st.session_state[f"desc_{intent['id']}"],
                            "keywords": keywords_list,
                        },
                    )
                    if err:
                        st.error(f"Failed to save: {err}")
                    else:
                        st.success("Saved successfully!")
                    st.session_state.confirm_save = None
                    st.session_state.pending_edit = None
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_save_{intent['id']}"):
                    st.session_state.confirm_save = None
                    st.session_state.pending_edit = None
                    st.rerun()

        elif st.session_state.confirm_delete == "show":
            intent = st.session_state.pending_edit
            doc_count = intent.get("document_count", 0)
            st.warning(f"Confirm delete intent '{intent['name']}'?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm", key=f"confirm_delete_{intent['id']}"):
                    if doc_count > 0:
                        st.error("This intent has documents and cannot be deleted")
                    else:
                        result, err = api_request(
                            "DELETE", f"/api/intents/{intent['id']}"
                        )
                        if err:
                            st.error(f"Failed to delete: {err}")
                        else:
                            st.success("Deleted successfully!")
                    st.session_state.confirm_delete = None
                    st.session_state.pending_edit = None
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_delete_{intent['id']}"):
                    st.session_state.confirm_delete = None
                    st.session_state.pending_edit = None
                    st.rerun()

        # Intent forms
        for intent in intents:
            intent_name = intent.get("name", "")
            doc_count = intent.get("document_count", 0)
            accuracy = accuracy_map.get(intent_name, 0)

            with st.expander(
                f"**{intent_name}** (Documents: {doc_count}, Accuracy: {accuracy:.1f}%)"
            ):
                with st.form(f"edit_intent_{intent['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input(
                            "Name", value=intent_name, key=f"name_{intent['id']}"
                        )
                        edit_desc = st.text_input(
                            "Description",
                            value=intent.get("description", "") or "",
                            key=f"desc_{intent['id']}",
                        )
                    with col2:
                        edit_keywords = st.text_input(
                            "Keywords (comma-separated)",
                            value=", ".join(intent.get("keywords", [])) or "",
                            key=f"keywords_{intent['id']}",
                        )
                        st.write(f"**Documents:** {doc_count}")
                        st.write(f"**Classification Accuracy:** {accuracy:.1f}%")

                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                    with col_btn1:
                        save_clicked = st.form_submit_button("💾 Save")
                    with col_btn2:
                        delete_clicked = st.form_submit_button("🗑️ Delete")
                    with col_btn3:
                        st.write("")

                    if save_clicked:
                        if not edit_name:
                            st.error("Intent name is required")
                        else:
                            st.session_state.confirm_save = "show"
                            st.session_state.pending_edit = intent
                            st.rerun()

                    if delete_clicked:
                        if doc_count > 0:
                            st.error("This intent has documents and cannot be deleted")
                        else:
                            st.session_state.confirm_delete = "show"
                            st.session_state.pending_edit = intent
                            st.rerun()

        st.markdown("---")

        # Confidence Settings
        st.markdown(
            """
        <div style="background: #FAF5FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #8B5CF6; margin: 0 0 8px 0;">⚙️ Confidence Settings</h3>
            <p style="color: #64748B; margin: 0;">Configure intent classification thresholds and weights</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Fetch current settings
        conf_result, conf_error = api_request("GET", "/api/intents/settings/confidence")

        if conf_error:
            st.error(f"Failed to load confidence settings: {conf_error}")
        else:
            with st.form("confidence_settings_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    threshold = st.number_input(
                        "Confidence Threshold",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(conf_result.get("confidence_threshold", 0.6)),
                        step=0.05,
                        help="Minimum confidence to accept classification result",
                    )
                    st.caption(
                        f"Current: {conf_result.get('confidence_threshold', 0.6):.2f}"
                    )

                with col2:
                    llm_weight = st.number_input(
                        "LLM Weight (Fusion)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(conf_result.get("llm_weight", 0.5)),
                        step=0.1,
                        help="Weight for LLM classification in fusion mode",
                    )
                    st.caption(f"Current: {conf_result.get('llm_weight', 0.5):.1f}")

                with col3:
                    keyword_weight = st.number_input(
                        "Keyword Weight (Fusion)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(conf_result.get("keyword_weight", 0.5)),
                        step=0.1,
                        help="Weight for keyword matching in fusion mode",
                    )
                    st.caption(f"Current: {conf_result.get('keyword_weight', 0.5):.1f}")

                st.markdown(
                    """
                <div style="background: #FEF9C3; padding: 8px 12px; border-radius: 6px; margin-top: 8px;">
                    <b>Classification Logic:</b><br>
                    • If LLM confidence ≥ threshold → use LLM result<br>
                    • Else if keyword score ≥ threshold → use keyword result<br>
                    • Else → weighted fusion (LLM × weight + Keyword × weight)
                </div>
                """,
                    unsafe_allow_html=True,
                )

                submitted = st.form_submit_button("💾 Save Settings", type="primary")

                if submitted:
                    save_result, save_err = api_request(
                        "PUT",
                        "/api/intents/settings/confidence",
                        data={
                            "confidence_threshold": threshold,
                            "llm_weight": llm_weight,
                            "keyword_weight": keyword_weight,
                        },
                    )
                    if save_err:
                        st.error(f"Failed to save: {save_err}")
                    else:
                        st.success("Confidence settings saved!")
                        st.rerun()

        st.markdown("---")

        # Document Processing Settings
        st.markdown(
            """
        <div style="background: #FAF5FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #8B5CF6; margin: 0 0 8px 0;">📄 Document Processing Settings</h3>
            <p style="color: #64748B; margin: 0;">Configure text chunking for vectorization</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Fetch current document settings
        doc_result, doc_error = api_request("GET", "/api/intents/settings/document")

        if doc_error:
            st.error(f"Failed to load document settings: {doc_error}")
        else:
            with st.form("document_settings_form"):
                col1, col2 = st.columns(2)
                with col1:
                    chunk_size = st.number_input(
                        "Chunk Size",
                        min_value=50,
                        max_value=2000,
                        value=int(doc_result.get("chunk_size", 256)),
                        step=16,
                        help="Size of each text chunk in characters",
                    )
                    st.caption(f"Current: {doc_result.get('chunk_size', 256)} chars")

                with col2:
                    chunk_overlap = st.number_input(
                        "Chunk Overlap",
                        min_value=0,
                        max_value=500,
                        value=int(doc_result.get("chunk_overlap", 50)),
                        step=10,
                        help="Overlap between adjacent chunks",
                    )
                    st.caption(f"Current: {doc_result.get('chunk_overlap', 50)} chars")

                st.warning(
                    "⚠️ Changing chunk settings will only affect new documents. Existing documents need to be re-indexed."
                )

                submitted_doc = st.form_submit_button(
                    "💾 Save Settings", type="primary"
                )

                if submitted_doc:
                    save_doc_result, save_doc_err = api_request(
                        "PUT",
                        "/api/intents/settings/document",
                        data={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
                    )
                    if save_doc_err:
                        st.error(f"Failed to save: {save_doc_err}")
                    else:
                        st.success("Document settings saved!")
                        st.rerun()

        st.markdown("---")

        # Add New Intent
        st.markdown(
            """
        <div style="background: #FAF5FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #8B5CF6; margin: 0 0 8px 0;">➕ Create Intent Space</h3>
            <p style="color: #64748B; margin: 0;">Add a new intent space to classify queries</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("add_intent_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Intent Name", key="new_name")
                new_description = st.text_input("Description", key="new_desc")
            with col2:
                new_keywords = st.text_input(
                    "Keywords (comma-separated)",
                    help="Enter keywords to improve classification accuracy",
                    key="new_keywords",
                )

            submitted = st.form_submit_button("➕ Create Intent", type="primary")

            if submitted:
                if not new_name:
                    st.error("Intent name is required")
                else:
                    keywords_list = [
                        k.strip() for k in new_keywords.split(",") if k.strip()
                    ]
                    result, err = api_request(
                        "POST",
                        "/api/intents",
                        json={
                            "name": new_name,
                            "description": new_description,
                            "keywords": keywords_list,
                        },
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Intent '{result['name']}' created!")
                        st.rerun()


# ============== Query Page ==============
elif page == "Query":
    st.markdown(
        """
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">🔍 Query Knowledge Base</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Ask questions and get AI-powered answers from your knowledge base</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Query input
    query_text = st.text_area(
        "Your Question",
        height=100,
        placeholder="e.g., How do I apply for annual leave?",
    )

    # Frontend selector
    frontend = st.selectbox("Query Source", ["web", "telegram", "feishu"])

    if st.button("🚀 Submit Query", key="btn_submit_query", type="primary"):
        if not query_text.strip():
            st.error("Please enter a question")
        else:
            st.markdown("---")

            # Display processing status
            status_container = st.empty()
            response_container = st.empty()
            metrics_container = st.container()

            status_container.markdown(
                "⏳ **Processing query...** (Intent classification, Search, RAG generation)"
            )

            # Use streaming API
            import requests

            payload = {"query": query_text, "frontend": frontend}

            full_response = ""
            intent_info = {}
            response_time = 0

            try:
                # Call streaming endpoint
                with requests.post(
                    f"{API_BASE_URL}/api/query/stream",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    stream=True,
                    timeout=60,
                ) as response:
                    if response.status_code != 200:
                        st.error(f"Error: {response.text}")
                    else:
                        # Parse SSE stream
                        for line in response.iter_lines(decode_unicode=True):
                            if line.startswith("data: "):
                                data = line[6:]
                                try:
                                    event = json.loads(data)

                                    event_type = event.get("event")
                                    event_data = event.get("data", {})

                                    if event_type == "intent":
                                        intent_info = event_data
                                        status_container.markdown(
                                            "✅ **Intent classified** - Searching knowledge base..."
                                        )

                                    elif event_type == "search":
                                        count = event_data.get("count", 0)
                                        status_container.markdown(
                                            f"✅ **Search complete** - Found {count} results - Generating response..."
                                        )

                                    elif event_type == "rerank":
                                        status = event_data.get("status", "")
                                        if status == "skipped":
                                            reason = event_data.get("reason", "")
                                            status_container.markdown(
                                                f"✅ **Reranking skipped** ({reason}) - Generating response..."
                                            )
                                        else:
                                            status_container.markdown(
                                                "✅ **Reranking complete** - Generating response..."
                                            )

                                    elif event_type == "token":
                                        token = event_data.get("token", "")
                                        full_response += token
                                        # Display streaming response
                                        response_container.markdown(
                                            f"""
                                        <div style="background: #F0FDF4; padding: 16px; border-radius: 8px; margin-top: 8px;">
                                            <h4 style="color: #10B981; margin: 0 0 8px 0;">💬 Response</h4>
                                            <div style="line-height: 1.6;">{full_response}▌</div>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )

                                    elif event_type == "corrected_response":
                                        # Use corrected response if LLM said "not found" but we have contexts
                                        corrected_text = event_data.get("response", "")
                                        if corrected_text != full_response:
                                            status_container.markdown(
                                                "⚠️ **LLM couldn't find answer - showing knowledge base content instead**"
                                            )
                                            full_response = corrected_text

                                    elif event_type == "done":
                                        response_time = event_data.get(
                                            "response_time", 0
                                        )
                                        status_container.markdown(
                                            f"✅ **Complete!** (Response time: {response_time:.0f}ms)"
                                        )

                                        # Display final response (use full_response which may be corrected)
                                        response_text = (
                                            full_response
                                            if full_response
                                            else event_data.get("response", "")
                                        )
                                        sources = event_data.get("sources", [])

                                        response_container.markdown(
                                            f"""
                                        <div style="background: #F0FDF4; padding: 16px; border-radius: 8px; margin-top: 8px;">
                                            <h4 style="color: #10B981; margin: 0 0 8px 0;">💬 Response</h4>
                                            <div style="line-height: 1.6;">{response_text}</div>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )

                                        # Display metrics
                                        with metrics_container:
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric(
                                                    "Detected Intent",
                                                    intent_info.get("intent", "-"),
                                                )
                                            with col2:
                                                conf = intent_info.get("confidence", 0)
                                                st.metric("Confidence", f"{conf:.1%}")
                                            with col3:
                                                source = intent_info.get(
                                                    "source", "unknown"
                                                )
                                                source_display = {
                                                    "llm": "🤖 LLM",
                                                    "keyword": "🔑 Keyword",
                                                    "fusion": "⚖️ Fusion",
                                                    "hint": "💡 Hint",
                                                }.get(source, source)
                                                st.metric("Source", source_display)
                                            with col4:
                                                st.metric(
                                                    "Response Time",
                                                    f"{response_time:.0f}ms",
                                                )

                                        # Display sources
                                        if sources:
                                            st.markdown(
                                                """
                                            <div style="background: #F0FDF4; padding: 12px 16px; border-radius: 8px; margin-top: 16px;">
                                                <h4 style="color: #10B981; margin: 0;">📚 Sources</h4>
                                            </div>
                                            """,
                                                unsafe_allow_html=True,
                                            )
                                            for source in sources:
                                                st.info(
                                                    f"**{source['document_name']}** (Score: {source['score']:.2f})"
                                                )

                                except json.JSONDecodeError:
                                    continue

            except Exception as e:
                st.error(f"Error: {str(e)}")


# ============== Frontend Integration Page ==============
elif page == "Frontend Integration":
    st.markdown(
        """
    <div class="frontend-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #3B82F6; margin-bottom: 20px;">
        <h2 style="color: #3B82F6; margin: 0;">📱 Frontend Integration</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Configure Frontend bot integrations</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    status, error = api_request("GET", "/api/status/frontend")

    if error:
        st.error(error)
    else:
        # Telegram Section (Polling Mode)
        st.markdown(
            """
        <div style="background: #EFF6FF; padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid #229ED9;">
            <h3 style="color: #229ED9; margin: 0;">Telegram Bot</h3>
            <p style="color: #64748B; margin: 8px 0 0 0;">使用 Polling 模式接收消息</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            telegram_status = status.get("telegram", {})
            if telegram_status.get("configured"):
                st.success("✅ Telegram 已配置")
            else:
                st.warning("⚠️ Telegram 未配置")

        with col2:
            if telegram_status.get("configured"):
                if telegram_status.get("running"):
                    st.success("🔴 Bot 运行中")
                else:
                    st.info("⚪ Bot 未启动 (需要重启服务)")

                if st.button(
                    "🔄 测试 Telegram", key="btn_test_telegram", type="primary"
                ):
                    result, err = api_request(
                        "POST", "/api/credentials/telegram/test", json={}
                    )
                    if err:
                        st.error(f"API error: {err}")
                    elif result and result.get("success"):
                        st.success("✅ Telegram 连接验证通过")
                    else:
                        st.error(
                            f"❌ {result.get('error', '验证失败') if result else '验证失败'}"
                        )
            else:
                st.info("请配置 Bot Token")

        with st.expander("⚙️ 配置 Telegram Bot Token"):
            tg_token = st.text_input(
                "Bot Token",
                type="password",
                key="tg_token_input",
                placeholder="从 @BotFather 获取的 Token",
            )

            if st.button("💾 保存 Token", key="btn_save_telegram"):
                if tg_token:
                    result, err = api_request(
                        "PUT",
                        "/api/webhook/env/telegram",
                        json={"token": tg_token},
                    )
                    if err:
                        st.error(f"保存失败: {err}")
                    else:
                        st.success("✅ Token 已保存到 .env 文件，重启服务后生效")
                        st.rerun()
                else:
                    st.error("请输入 Token")

            if st.button("🔄 刷新状态", key="btn_refresh_telegram"):
                st.rerun()

        st.markdown("---")

        # Feishu Section
        st.markdown(
            """
        <div style="background: #FFF7ED; padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid #FF6917;">
            <h3 style="color: #FF6917; margin: 0;">飞书 Bot (Feishu)</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            feishu_status = status.get("feishu", {})
            if feishu_status.get("configured"):
                st.success("✅ 飞书已配置")
            else:
                st.warning("⚠️ 飞书未配置")

        with col2:
            if feishu_status.get("configured"):
                # Show running status
                if feishu_status.get("running"):
                    st.success("🔴 Bot 运行中")
                else:
                    st.info("⚪ Bot 未启动 (需要重启服务)")

                if st.button("🔄 测试飞书", key="btn_test_feishu", type="primary"):
                    result, err = api_request(
                        "POST", "/api/credentials/feishu/test", json={}
                    )
                    if err:
                        st.error(f"API error: {err}")
                    elif result and result.get("success"):
                        st.success("✅ 飞书连接验证通过")
                    else:
                        st.error(
                            f"❌ {result.get('error', '验证失败') if result else '验证失败'}"
                        )
            else:
                st.info("请先配置飞书凭据")

        with st.expander("⚙️ 配置飞书凭据 (Feishu Credentials)"):
            feishu_app_id = st.text_input(
                "App ID", key="feishu_app_id", placeholder="cli_xxxxx"
            )
            feishu_app_secret = st.text_input(
                "App Secret", type="password", key="feishu_app_secret"
            )

            if st.button("💾 保存飞书凭据", key="btn_save_feishu"):
                if feishu_app_id and feishu_app_secret:
                    result, err = api_request(
                        "PUT",
                        "/api/webhook/env/feishu",
                        json={
                            "app_id": feishu_app_id,
                            "app_secret": feishu_app_secret,
                        },
                    )
                    if err:
                        st.error(f"保存失败: {err}")
                    else:
                        st.success("✅ 飞书凭据已保存到 .env 文件，重启服务后生效")
                        st.rerun()
                else:
                    st.error("请填写所有字段")

        st.markdown("---")

        # Connection Info
        st.markdown(
            """
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px; margin-top: 16px;">
            <h4 style="color: #64748B; margin: 0 0 12px 0;">连接方式</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.info("🤖 **Telegram**: Polling 模式 (长轮询)")
            st.caption("使用 TELEGRAM_BOT_TOKEN 环境变量配置")
        with col2:
            st.info("📱 **飞书 (Feishu)**: WebSocket 长连接模式")


# ============== Analytics Page ==============
elif page == "Analytics":
    st.markdown(
        """
    <div class="analytics-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #F59E0B; margin-bottom: 20px;">
        <h2 style="color: #F59E0B; margin: 0;">📈 Analytics & Reports</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Track system usage and performance metrics</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Dashboard stats
    stats, error = api_request("GET", "/api/analytics/dashboard")

    if error:
        st.error(error)
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Queries", stats.get("total_queries", 0))
        with col2:
            st.metric("Today's Queries", stats.get("today_queries", 0))
        with col3:
            st.metric("Accuracy", f"{stats.get('accuracy', 0):.1f}%")
        with col4:
            st.metric("Documents", stats.get("document_count", 0))

    # Intent stats
    st.markdown(
        """
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📊 Intent Usage</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    intent_stats, error = api_request("GET", "/api/analytics/intents")

    if not error and intent_stats:
        df_intents = pd.DataFrame(intent_stats)
        if not df_intents.empty:
            st.dataframe(
                df_intents.rename(
                    columns={
                        "intent_name": "Intent",
                        "query_count": "Queries",
                        "accuracy": "Accuracy %",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No intent statistics yet")
    else:
        st.info("No intent statistics yet")

    # Popular documents
    st.markdown(
        """
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📄 Popular Documents</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    popular, error = api_request("GET", "/api/analytics/popular-documents")

    if not error and popular:
        df_popular = pd.DataFrame(popular)
        if not df_popular.empty:
            st.dataframe(
                df_popular.rename(
                    columns={
                        "document_id": "ID",
                        "document_name": "Document",
                        "access_count": "Access Count",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No document access data yet")
    else:
        st.info("No popular documents yet")

    # Query logs
    st.markdown(
        """
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📝 Query Classification Log</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Fetch intents for filter
    all_intents, _ = api_request("GET", "/api/intents")

    # Filters for query logs
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_intent = st.selectbox(
            "Filter by Intent",
            ["All Intents"] + [i.get("name") for i in (all_intents or [])],
        )
    with col_f2:
        filter_status = st.selectbox(
            "Filter by Status", ["All Status", "success", "failed"]
        )

    # Build query params
    log_params = []
    if filter_intent != "All Intents":
        log_params.append(f"intent_name={filter_intent}")
    if filter_status != "All Status":
        log_params.append(f"status={filter_status}")
    log_query = "&".join(log_params) if log_params else ""

    logs, error = api_request("GET", f"/api/analytics/logs?limit=50&{log_query}")

    if not error and logs.get("items"):
        # Format status with emoji
        def fmt_status(s):
            return "✅ Success" if s == "success" else "❌ Failed"

        df_logs = pd.DataFrame(
            [
                {
                    "Time": l["created_at"][:19],
                    "Query Content": l.get("query", ""),
                    "Detected Intent": l.get("intent_name", "-") or "General",
                    "Confidence Score": f"{l.get('confidence', 0):.1%}",
                    "Response Status": fmt_status(l.get("status", "failed")),
                }
                for l in logs["items"]
            ]
        )
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No query logs found")

    # Export
    st.markdown("---")
    st.subheader("Export")

    if st.button("📥 Download Query Logs (CSV)", key="btn_download_logs"):
        try:
            response = requests.get(f"{API_BASE_URL}/api/analytics/export-logs")
            if response.status_code == 200:
                st.download_button(
                    label="📥 Click to Download",
                    data=response.content,
                    file_name="query_logs.csv",
                    mime="text/csv",
                )
            else:
                st.error("Failed to export")
        except Exception as e:
            st.error(f"Error: {e}")
