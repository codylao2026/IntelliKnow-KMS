"""
IntelliKnow KMS - Streamlit Admin Dashboard
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Color scheme
COLORS = {
    "frontend": "#3B82F6",   # Blue
    "knowledge": "#10B981",   # Green
    "intent": "#8B5CF6",      # Purple
    "analytics": "#F59E0B",   # Orange
    "background": "#F8FAFC",  # Light gray
    "card_bg": "#FFFFFF",     # White
    "text": "#1E293B",        # Dark slate
    "text_secondary": "#64748B"  # Slate
}

# Page configuration
st.set_page_config(
    page_title="IntelliKnow KMS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
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
""", unsafe_allow_html=True)


def api_request(method, endpoint, files=None, data=None, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if files and isinstance(files, list):
            # Handle multiple files upload
            files_dict = {}
            for name, file_tuple in files:
                files_dict[name] = (file_tuple[0], file_tuple[1])
            
            response = requests.post(url, files=files_dict, data=data)
        elif files:
            if method == "POST":
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.put(url, files=files, data=data)
        else:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
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
st.sidebar.markdown("""
<style>
.sidebar-title { font-size: 1.4em; font-weight: bold; color: #1E293B; }
.category-header { font-size: 0.9em; font-weight: bold; color: #64748B; padding: 8px 0 4px 0; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🧠 IntelliKnow KMS")
st.sidebar.markdown("---")

# Use session_state to track current page
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "nav_category" not in st.session_state:
    st.session_state.nav_category = "Admin"

# Category selection
st.sidebar.markdown('<p class="category-header">📂 Select Category</p>', unsafe_allow_html=True)
nav_category = st.sidebar.radio(
    "Category",
    ["Admin", "User"],
    index=0 if st.session_state.nav_category == "Admin" else 1,
    key="nav_category_radio",
    label_visibility="collapsed"
)
st.session_state.nav_category = nav_category

# Submenu based on category
def change_page():
    st.session_state.current_page = st.session_state.nav_radio

# Clear view/update states when navigating
def clear_doc_states():
    st.session_state.view_doc_id = None
    st.session_state.update_doc_id = None

if nav_category == "Admin":
    admin_options = ["Dashboard", "KB Management", "Intent Configuration", "Frontend Integration", "Analytics"]
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="category-header">👨‍💼 Admin Menu</p>', unsafe_allow_html=True)
    st.sidebar.radio(
        "Admin Navigation",
        admin_options,
        key="nav_radio",
        on_change=clear_doc_states
    )
else:
    user_options = ["Query"]
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="category-header">👤 User Menu</p>', unsafe_allow_html=True)
    st.sidebar.radio(
        "User Navigation",
        user_options,
        key="nav_radio",
        on_change=clear_doc_states
    )

page = st.session_state.current_page

# Override to View/Update page if needed
if st.session_state.get("view_doc_id"):
    page = "View Document"
elif st.session_state.get("update_doc_id"):
    page = "Update Document"

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.85em; color: #64748B;">
<b>Gen AI-powered Knowledge Management System</b><br>
• RAG-powered query responses<br>
• Multi-frontend integration<br>
• Intent-based classification
</div>
""", unsafe_allow_html=True)


# ============== Dashboard Page ==============
if page == "Dashboard":
    st.markdown("""
    <div style="padding: 20px; border-radius: 12px; border-left: 4px solid #3B82F6; margin-bottom: 20px;">
        <h1 style="color: #1E293B; margin: 0;">🧠 IntelliKnow KMS</h1>
        <p style="color: #64748B; margin: 8px 0 0 0;">Gen AI-powered Knowledge Management System</p>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown("""
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px;">
            <h3 style="color: #1E293B; margin: 0 0 12px 0;">⚡ Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success("✅ Backend: Running")
        with col2:
            st.success("✅ Database: Connected")
        with col3:
            if st.button("🔄 Refresh Stats"):
                st.rerun()
        with col4:
            st.info("🚀 System Ready")


# ============== KB Management Page ==============
elif page == "KB Management":
    st.markdown("""
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">📚 KB Management</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Manage knowledge base documents and content</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Document List", "📤 Upload Documents"])

    with tab1:
        # Initialize selection state
        if "selected_docs" not in st.session_state:
            st.session_state.selected_docs = set()

        # Fetch intents for filter
        intents, _ = api_request("GET", "/api/intents")
        intent_options = {"All Intents": None}
        if intents:
            for intent in intents:
                intent_options[intent["name"]] = intent["id"]

        # Search and Filter Bar
        st.markdown("""
        <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="color: #10B981; margin: 0 0 12px 0;">🔍 Search & Filter</h4>
        </div>
        """, unsafe_allow_html=True)

        col_search, col_format, col_intent, col_status = st.columns(4)
        
        with col_search:
            search_query = st.text_input("Search by name", placeholder="Enter document name...")
        
        with col_format:
            format_options = ["All Formats", "pdf", "docx"]
            selected_format = st.selectbox("Format", format_options)
        
        with col_intent:
            selected_intent_name = st.selectbox("Intent Space", list(intent_options.keys()))
        
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

                # Clear stale selections
                doc_ids = [d["id"] for d in docs["items"]]
                st.session_state.selected_docs = st.session_state.selected_docs.intersection(set(doc_ids))

                # Table header
                header_cols = st.columns([0.5, 3, 1.5, 1, 1, 1.5, 1.5, 1])
                headers = ["☑️", "Document Name", "Upload Date", "Format", "Size", "Intent", "Status", "Actions"]
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
                        st.write(d['created_at'][:10])
                    with row_cols[3]:
                        st.write(d['file_type'].upper())
                    with row_cols[4]:
                        st.write(format_size(d['file_size']))
                    with row_cols[5]:
                        st.write(d.get('intent_name', '-'))
                    with row_cols[6]:
                        st.write(format_status(d['status']))
                    
                    with row_cols[7]:
                        col_action1, col_action2 = st.columns(2)
                        with col_action1:
                            if st.button("👁️", key=f"view_{doc_id}"):
                                st.session_state.view_doc_id = doc_id
                                st.rerun()
                        with col_action2:
                            if st.button("🔄", key=f"update_{doc_id}"):
                                st.session_state.update_doc_id = doc_id
                                st.rerun()
                                st.write(f"Re-upload for: **{d['name']}**")
                                update_file = st.file_uploader(
                                    "Choose new file",
                                    type=["pdf", "docx"],
                                    key=f"update_file_{doc_id}"
                                )
                                if update_file is not None:
                                    st.info(f"Selected: {update_file.name}")
                                    if st.button("📤 Upload", key=f"do_update_{doc_id}"):
                                        # Delete old and upload new
                                        delete_result, del_err = api_request("DELETE", f"/api/documents/{doc_id}")
                                        if del_err:
                                            st.error(f"Delete failed: {del_err}")
                                        else:
                                            # Upload new file
                                            intent_id = d.get("intent_id")
                                            files_data = [("files", (update_file.name, update_file.getvalue()))]
                                            data = {"intent_id": intent_id} if intent_id else {}
                                            result, err = api_request(
                                                "POST",
                                                "/api/documents/upload-batch",
                                                files=files_data,
                                                data=data
                                            )
                                            if err:
                                                st.error(f"Upload failed: {err}")
                                            else:
                                                st.success("✅ Document updated successfully!")
                                                st.rerun()

                st.markdown("---")

                # Batch delete section
                selected_count = len(st.session_state.selected_docs)
                if selected_count > 0:
                    st.markdown(f"""
                    <div style="background: #FEF2F2; padding: 12px; border-radius: 8px; border-left: 4px solid #EF4444;">
                        <span style="color: #DC2626; font-weight: bold;">☑️ {selected_count} document(s) selected</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col_del_info, col_del_btn = st.columns([3, 1])
                    with col_del_info:
                        st.write(f"Ready to delete {selected_count} selected document(s)")
                    with col_del_btn:
                        if st.button(f"🗑️ Delete Selected ({selected_count})", type="primary"):
                            deleted = 0
                            failed = 0
                            for doc_id in list(st.session_state.selected_docs):
                                result, err = api_request("DELETE", f"/api/documents/{doc_id}")
                                if err:
                                    failed += 1
                                else:
                                    deleted += 1
                                    st.session_state.selected_docs.discard(doc_id)
                            
                            if deleted > 0:
                                st.success(f"✅ {deleted} document(s) deleted")
                            if failed > 0:
                                st.error(f"❌ {failed} document(s) failed to delete")
                            st.rerun()
                else:
                    st.info("☐ Select documents using checkboxes to enable batch deletion")
            else:
                st.info("No documents found. Try adjusting your search or filters.")

    with tab2:
        st.markdown("""
        <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h4 style="color: #10B981; margin: 0;">📤 Upload Documents</h4>
            <p style="color: #64748B; margin: 8px 0 0 0;">Supported formats: PDF, DOCX | Upload multiple files at once</p>
        </div>
        """, unsafe_allow_html=True)

        # Initialize session state
        if "upload_in_progress" not in st.session_state:
            st.session_state.upload_in_progress = False
        if "uploaded_doc_ids" not in st.session_state:
            st.session_state.uploaded_doc_ids = []
        if "pending_files" not in st.session_state:
            st.session_state.pending_files = []
        if "duplicate_files" not in st.session_state:
            st.session_state.duplicate_files = []

        # Fetch existing documents for duplicate check
        existing_docs, _ = api_request("GET", "/api/documents?limit=1000")
        existing_names = set()
        existing_doc_map = {}
        if existing_docs and existing_docs.get("items"):
            for d in existing_docs["items"]:
                existing_names.add(d["name"].lower())
                existing_doc_map[d["name"].lower()] = d

        uploaded_files = st.file_uploader(
            "Choose files (multiple allowed)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX. You can select multiple files."
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
            index=0
        )

        if uploaded_files:
            # Check for duplicates
            duplicates = []
            new_files = []
            for f in uploaded_files:
                if f.name.lower() in existing_names:
                    duplicates.append(f)
                else:
                    new_files.append(f)

            if duplicates:
                st.warning(f"⚠️ {len(duplicates)} file(s) already exist:")
                for dup in duplicates:
                    existing = existing_doc_map.get(dup.name.lower(), {})
                    st.write(f"  - **{dup.name}** (exists, status: {existing.get('status', 'unknown')})")
                st.info("Select 'Upload All' to overwrite existing files, or remove duplicates from selection")

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
            st.progress(progress, text=f"Processing: {completed} completed, {failed} failed, {total - completed - failed} pending...")
            
            # All done
            if completed + failed >= total:
                st.session_state.upload_in_progress = False
                st.session_state.uploaded_doc_ids = []
                st.rerun()
        else:
            all_files = uploaded_files or []
            pending = st.session_state.pending_files
            disabled = not (all_files and selected_intent_name != "-- Select an Intent --")
            
            if st.button("📤 Upload All Documents", type="primary", disabled=disabled):
                if not all_files:
                    st.error("Please select at least one file")
                elif selected_intent_name == "-- Select an Intent --":
                    st.error("Please select an Intent Space to associate with these documents")
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
                                result, err = api_request("DELETE", f"/api/documents/{old_doc['id']}")
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
                                data=data
                            )

                        if error:
                            st.error(f"Upload failed: {error}")
                        else:
                            successful = result.get("successful", 0)
                            failed_count = result.get("failed", 0)
                            results = result.get("results", [])

                            if successful > 0:
                                doc_ids = [r.get("id") for r in results if r.get("status") == "uploaded"]
                                st.session_state.upload_in_progress = True
                                st.session_state.uploaded_doc_ids = doc_ids
                                st.session_state.pending_files = []
                                st.session_state.duplicate_files = []
                                
                                st.success(f"✅ {successful} document(s) uploaded! Processing...")
                                st.rerun()
                            
                            if failed_count > 0:
                                st.warning(f"⚠️ {failed_count} document(s) failed:")
                                for r in results:
                                    if r.get("status") == "failed":
                                        st.error(f"  - {r.get('name')}: {r.get('error', 'Unknown error')}")

                            if successful > 0:
                                st.session_state.upload_in_progress = True
                                st.session_state.uploaded_doc_ids = doc_ids
                                st.session_state.pending_files = []
                                st.session_state.duplicate_files = []
                                
                                st.success(f"✅ {successful} document(s) uploaded! Processing...")
                                st.rerun()
                        
                        if failed_count > 0:
                            st.warning(f"⚠️ {failed_count} document(s) failed:")

        # Show hint if no intent selected
        if uploaded_files and selected_intent_name == "-- Select an Intent --":
            st.warning("⚠️ Please select an Intent Space to upload documents")


# ============== View Document Page ==============
elif page == "View Document":
    doc_id = st.session_state.get("view_doc_id")
    
    if st.button("← Back to Document List"):
        st.session_state.view_doc_id = None
        st.rerun()
    
    st.markdown("""
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">📄 View Document</h2>
    </div>
    """, unsafe_allow_html=True)
    
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
                st.markdown("""
                <div style="background: #F0FDF4; padding: 16px; border-radius: 12px;">
                    <h4 style="color: #10B981; margin: 0 0 12px 0;">Document Information</h4>
                </div>
                """, unsafe_allow_html=True)
                st.write(f"**ID:** {doc_detail.get('id')}")
                st.write(f"**Name:** {doc_detail.get('name')}")
                st.write(f"**Format:** {doc_detail.get('file_type', '').upper()}")
                st.write(f"**Intent:** {doc_detail.get('intent_name', '-')}")
            
            with col2:
                st.markdown("""
                <div style="background: #F0FDF4; padding: 16px; border-radius: 12px;">
                    <h4 style="color: #10B981; margin: 0 0 12px 0;">Processing Status</h4>
                </div>
                """, unsafe_allow_html=True)
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
                    response = requests.get(f"{API_BASE_URL}/api/documents/{doc_id}/download")
                    if response.status_code == 200:
                        st.download_button(
                            label="📥 Download Document",
                            data=response.content,
                            file_name=doc_detail.get('name', 'document'),
                            mime="application/octet-stream"
                        )
                    else:
                        st.warning("Download not available")
                except Exception as e:
                    st.warning(f"Download error: {e}")
            
            with col_update:
                if st.button("🔄 Update Document", type="primary"):
                    st.session_state.update_doc_id = doc_id
                    st.session_state.view_doc_id = None
                    st.rerun()
            
            # Document Content
            st.markdown("---")
            st.markdown("""
            <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin-top: 16px;">
                <h4 style="color: #10B981; margin: 0 0 12px 0;">📝 Document Content</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Fetch content
            with st.spinner("Loading document content..."):
                content_data, content_err = api_request("GET", f"/api/documents/{doc_id}/content")
            
            if content_err:
                st.warning("⚠️ Unable to extract document content")
                st.info("The document may be encrypted, password-protected, or in an unsupported format.")
                st.caption(f"Error: {content_err}")
            elif content_data:
                word_count = content_data.get('word_count', 0)
                content = content_data.get('content', '')
                
                if not content or content.startswith("[Unable to"):
                    st.warning("⚠️ Document content could not be extracted")
                    st.info("The document may be encrypted, password-protected, or in an unsupported format.")
                else:
                    st.success(f"Word count: {word_count}")
                    
                    # Show preview or full content
                    if st.checkbox("Show Full Content", value=False):
                        st.text_area(
                            "Document Text",
                            value=content,
                            height=500,
                            label_visibility="collapsed"
                        )
                    else:
                        st.text_area(
                            "Preview (first 500 characters)",
                            value=content_data.get('preview', content[:500]),
                            height=300,
                            label_visibility="collapsed"
                        )
    else:
        st.warning("No document selected")
        st.session_state.view_doc_id = None


# ============== Update Document Page ==============
elif page == "Update Document":
    doc_id = st.session_state.get("update_doc_id")
    
    if st.button("← Back to Document List"):
        st.session_state.update_doc_id = None
        st.rerun()
    
    st.markdown("""
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">🔄 Update Document</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if doc_id:
        # Get current document info
        doc_detail, err = api_request("GET", f"/api/documents/{doc_id}")
        
        if err:
            st.error(err)
        else:
            st.info(f"Current document: **{doc_detail.get('name')}**")
            st.info(f"Current intent: **{doc_detail.get('intent_name', 'None')}**")
            
            st.markdown("""
            <div style="background: #F0FDF4; padding: 16px; border-radius: 12px; margin: 16px 0;">
                <h4 style="color: #10B981; margin: 0;">Upload New File</h4>
                <p style="color: #64748B; margin: 8px 0 0 0;">Select a new PDF or DOCX file to replace the current document</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Intent selection
            intents, _ = api_request("GET", "/api/intents")
            intent_options = {}
            if intents:
                for intent in intents:
                    intent_options[intent["name"]] = intent["id"]
            
            intent_names = list(intent_options.keys())
            current_intent = doc_detail.get("intent_name", "")
            current_index = intent_names.index(current_intent) if current_intent in intent_names else 0
            
            selected_intent_name = st.selectbox(
                "Intent Space",
                options=intent_names,
                index=current_index
            )
            
            # File upload
            new_file = st.file_uploader(
                "Choose new file (PDF or DOCX)",
                type=["pdf", "docx"],
                help="Select a new file to replace the current document"
            )
            
            if new_file:
                st.success(f"Selected: {new_file.name}")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("📤 Replace Document", type="primary"):
                        with st.spinner("Replacing document..."):
                            # Delete old document
                            delete_result, del_err = api_request("DELETE", f"/api/documents/{doc_id}")
                            
                            if del_err:
                                st.error(f"Delete failed: {del_err}")
                            else:
                                # Upload new file
                                files_data = [("files", (new_file.name, new_file.getvalue()))]
                                data = {"intent_id": intent_options[selected_intent_name]}
                                
                                result, upload_err = api_request(
                                    "POST",
                                    "/api/documents/upload-batch",
                                    files=files_data,
                                    data=data
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
    st.markdown("""
    <div class="intent-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #8B5CF6; margin-bottom: 20px;">
        <h2 style="color: #8B5CF6; margin: 0;">🎯 Intent Configuration</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Create and manage intent spaces with keywords for classification accuracy</p>
    </div>
    """, unsafe_allow_html=True)

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

        st.markdown(f"""
        <div style="background: #FAF5FF; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;">
            <span style="color: #8B5CF6; font-weight: bold;">Total: {len(intents)} intent spaces</span>
        </div>
        """, unsafe_allow_html=True)

        # Handle confirmation dialogs
        if st.session_state.confirm_save == "show":
            intent = st.session_state.pending_edit
            st.warning(f"Confirm update for intent '{intent['name']}'?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm", key=f"confirm_save_{intent['id']}"):
                    keywords_list = [k.strip() for k in st.session_state[f"keywords_{intent['id']}"].split(",") if k.strip()]
                    result, err = api_request(
                        "PUT",
                        f"/api/intents/{intent['id']}",
                        json={
                            "name": st.session_state[f"name_{intent['id']}"],
                            "description": st.session_state[f"desc_{intent['id']}"],
                            "keywords": keywords_list
                        }
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
            doc_count = intent.get('document_count', 0)
            st.warning(f"Confirm delete intent '{intent['name']}'?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Confirm", key=f"confirm_delete_{intent['id']}"):
                    if doc_count > 0:
                        st.error("This intent has documents and cannot be deleted")
                    else:
                        result, err = api_request("DELETE", f"/api/intents/{intent['id']}")
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
            intent_name = intent.get('name', '')
            doc_count = intent.get('document_count', 0)
            accuracy = accuracy_map.get(intent_name, 0)
            
            with st.expander(f"**{intent_name}** (Documents: {doc_count}, Accuracy: {accuracy:.1f}%)"):
                with st.form(f"edit_intent_{intent['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Name", value=intent_name, key=f"name_{intent['id']}")
                        edit_desc = st.text_input("Description", value=intent.get('description', '') or '', key=f"desc_{intent['id']}")
                    with col2:
                        edit_keywords = st.text_input(
                            "Keywords (comma-separated)",
                            value=", ".join(intent.get('keywords', [])) or '',
                            key=f"keywords_{intent['id']}"
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
        st.markdown("""
        <div style="background: #FEF3C7; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #D97706; margin: 0 0 8px 0;">⚙️ Confidence Settings</h3>
            <p style="color: #92400E; margin: 0;">Configure intent classification thresholds and weights</p>
        </div>
        """, unsafe_allow_html=True)

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
                        help="Minimum confidence to accept classification result"
                    )
                    st.caption(f"Current: {conf_result.get('confidence_threshold', 0.6):.2f}")

                with col2:
                    llm_weight = st.number_input(
                        "LLM Weight (Fusion)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(conf_result.get("llm_weight", 0.5)),
                        step=0.1,
                        help="Weight for LLM classification in fusion mode"
                    )
                    st.caption(f"Current: {conf_result.get('llm_weight', 0.5):.1f}")

                with col3:
                    keyword_weight = st.number_input(
                        "Keyword Weight (Fusion)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(conf_result.get("keyword_weight", 0.5)),
                        step=0.1,
                        help="Weight for keyword matching in fusion mode"
                    )
                    st.caption(f"Current: {conf_result.get('keyword_weight', 0.5):.1f}")

                st.markdown("""
                <div style="background: #FEF9C3; padding: 8px 12px; border-radius: 6px; margin-top: 8px;">
                    <b>Classification Logic:</b><br>
                    • If LLM confidence ≥ threshold → use LLM result<br>
                    • Else if keyword score ≥ threshold → use keyword result<br>
                    • Else → weighted fusion (LLM × weight + Keyword × weight)
                </div>
                """, unsafe_allow_html=True)

                submitted = st.form_submit_button("💾 Save Settings", type="primary")

                if submitted:
                    save_result, save_err = api_request(
                        "PUT",
                        "/api/intents/settings/confidence",
                        data={
                            "confidence_threshold": threshold,
                            "llm_weight": llm_weight,
                            "keyword_weight": keyword_weight
                        }
                    )
                    if save_err:
                        st.error(f"Failed to save: {save_err}")
                    else:
                        st.success("Confidence settings saved!")
                        st.rerun()

        st.markdown("---")

        # Document Processing Settings
        st.markdown("""
        <div style="background: #DBEAFE; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #2563EB; margin: 0 0 8px 0;">📄 Document Processing Settings</h3>
            <p style="color: #1E40AF; margin: 0;">Configure text chunking for vectorization</p>
        </div>
        """, unsafe_allow_html=True)

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
                        help="Size of each text chunk in characters"
                    )
                    st.caption(f"Current: {doc_result.get('chunk_size', 256)} chars")

                with col2:
                    chunk_overlap = st.number_input(
                        "Chunk Overlap",
                        min_value=0,
                        max_value=500,
                        value=int(doc_result.get("chunk_overlap", 50)),
                        step=10,
                        help="Overlap between adjacent chunks"
                    )
                    st.caption(f"Current: {doc_result.get('chunk_overlap', 50)} chars")

                st.warning("⚠️ Changing chunk settings will only affect new documents. Existing documents need to be re-indexed.")

                submitted_doc = st.form_submit_button("💾 Save Settings", type="primary")

                if submitted_doc:
                    save_doc_result, save_doc_err = api_request(
                        "PUT",
                        "/api/intents/settings/document",
                        data={
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap
                        }
                    )
                    if save_doc_err:
                        st.error(f"Failed to save: {save_doc_err}")
                    else:
                        st.success("Document settings saved!")
                        st.rerun()

        st.markdown("---")

        # Add New Intent
        st.markdown("""
        <div style="background: #FAF5FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #8B5CF6; margin: 0 0 8px 0;">➕ Create Intent Space</h3>
            <p style="color: #64748B; margin: 0;">Add a new intent space to classify queries</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("add_intent_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Intent Name", key="new_name")
                new_description = st.text_input("Description", key="new_desc")
            with col2:
                new_keywords = st.text_input(
                    "Keywords (comma-separated)",
                    help="Enter keywords to improve classification accuracy",
                    key="new_keywords"
                )

            submitted = st.form_submit_button("➕ Create Intent", type="primary")

            if submitted:
                if not new_name:
                    st.error("Intent name is required")
                else:
                    keywords_list = [k.strip() for k in new_keywords.split(",") if k.strip()]
                    result, err = api_request(
                        "POST",
                        "/api/intents",
                        json={
                            "name": new_name,
                            "description": new_description,
                            "keywords": keywords_list
                        }
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Intent '{result['name']}' created!")
                        st.rerun()


# ============== Query Page ==============
elif page == "Query":
    st.markdown("""
    <div class="knowledge-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0;">🔍 Query Knowledge Base</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Ask questions and get AI-powered answers from your knowledge base</p>
    </div>
    """, unsafe_allow_html=True)

    # Query input
    query_text = st.text_area(
        "Your Question",
        height=100,
        placeholder="e.g., How do I apply for annual leave?"
    )

    # Frontend selector
    frontend = st.selectbox(
        "Query Source",
        ["web", "whatsapp", "teams"]
    )

    if st.button("🚀 Submit Query", type="primary"):
        if not query_text.strip():
            st.error("Please enter a question")
        else:
            with st.spinner("Processing query..."):
                payload = {
                    "query": query_text,
                    "frontend": frontend
                }
                result, error = api_request("POST", "/api/query", data=payload)

                if error:
                    st.error(error)
                else:
                    st.markdown("---")
                    
                    st.markdown("""
                    <div style="background: #ECFDF5; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;">
                        <h3 style="color: #10B981; margin: 0;">💬 Response</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display intent classification
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Detected Intent", result.get("intent"))
                    with col2:
                        st.metric("Confidence", f"{result.get('confidence', 0):.1%}")
                    with col3:
                        source = result.get("confidence_source", "unknown")
                        source_display = {
                            "llm": "🤖 LLM",
                            "keyword": "🔑 Keyword",
                            "fusion": "⚖️ Fusion",
                            "hint": "💡 Hint",
                            "error": "❌ Error",
                            "none": "➖ None"
                        }.get(source, source)
                        st.metric("Source", source_display)
                    with col4:
                        response_time = result.get("response_time", 0)
                        st.metric("Response Time", f"{response_time:.0f}ms")

                    # Display response
                    st.markdown(result.get("response", ""))

                    # Display sources if available
                    sources = result.get("sources", [])
                    if sources:
                        st.markdown("""
                        <div style="background: #F0FDF4; padding: 12px 16px; border-radius: 8px; margin-top: 16px;">
                            <h4 style="color: #10B981; margin: 0;">📚 Sources</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        for source in sources:
                            st.info(f"**{source['document_name']}** (Score: {source['score']:.2f})")
                            st.markdown(f"_{source['content'][:200]}..._")

                    st.markdown("---")
                    st.caption(f"Response time: {result.get('response_time', 0):.0f}ms")


# ============== Frontend Integration Page ==============
elif page == "Frontend Integration":
    st.markdown("""
    <div class="frontend-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #3B82F6; margin-bottom: 20px;">
        <h2 style="color: #3B82F6; margin: 0;">📱 Frontend Integration</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Configure WhatsApp and Teams bot integrations</p>
    </div>
    """, unsafe_allow_html=True)

    status, error = api_request("GET", "/api/status/frontend")

    if error:
        st.error(error)
    else:
        # WhatsApp Section
        st.markdown("""
        <div style="background: #EFF6FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #3B82F6; margin: 0;">WhatsApp Business API</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            wa_status = status.get("whatsapp", {})
            if wa_status.get("configured"):
                st.success("✅ WhatsApp Configured")
            else:
                st.warning("⚠️ WhatsApp Not Configured")

        with col2:
            if wa_status.get("configured"):
                if st.button("🔄 Test WhatsApp", type="primary"):
                    st.info("WhatsApp test functionality available")
            else:
                st.info("Configure credentials to enable testing")

        with st.expander("⚙️ Configure WhatsApp Credentials"):
            wa_phone = st.text_input("Phone Number ID", key="wa_phone")
            wa_token = st.text_input("Access Token", type="password", key="wa_token")

            if st.button("💾 Save WhatsApp Credentials"):
                if wa_phone and wa_token:
                    result, err = api_request(
                        "PUT",
                        "/api/credentials/whatsapp",
                        json={"credentials": {"phone_number_id": wa_phone, "access_token": wa_token}}
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success("WhatsApp credentials saved successfully")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")

        st.markdown("---")

        # Teams Section
        st.markdown("""
        <div style="background: #F0F9FF; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <h3 style="color: #3B82F6; margin: 0;">Microsoft Teams Bot</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            teams_status = status.get("teams", {})
            if teams_status.get("configured"):
                st.success("✅ Teams Configured")
            else:
                st.warning("⚠️ Teams Not Configured")

        with col2:
            if teams_status.get("configured"):
                conv_id_input = st.text_input(
                    "Conversation ID (optional) 💡 Enter to send test message",
                    key="teams_conv_id",
                    placeholder="19:xxx@thread.tacv2"
                )
                st.caption("Format: 19:xxx@thread.tacv2 or UUID")
                
                if st.button("🔄 Test Teams", type="primary"):
                    conv_id = st.session_state.get("teams_conv_id", "").strip()
                    
                    if conv_id:
                        if not (conv_id.startswith("19:") and "@thread" in conv_id) and \
                           not (len(conv_id) == 36 and conv_id.count("-") == 4):
                            st.error("Invalid Conversation ID format")
                        else:
                            payload = {"message": "Hello from IntelliKnow!", "conversation_id": conv_id}
                            result, err = api_request("POST", "/api/test/teams", json=payload)
                            if err:
                                st.error(f"API error: {err}")
                            elif result and result.get("success"):
                                st.success(f"✅ {result.get('message', 'Test successful')}")
                            else:
                                st.error(f"❌ {result.get('error', 'Test failed') if result else 'Test failed'}")
                    else:
                        result, err = api_request("POST", "/api/test/teams", json={"message": "test"})
                        if err:
                            st.error(f"API error: {err}")
                        elif result and result.get("success"):
                            st.success("✅ Credentials validated")
                        else:
                            st.error(f"❌ Validation failed: {result.get('error', 'Unknown') if result else 'Unknown'}")
            else:
                st.info("Please configure Teams credentials first")

        with st.expander("⚙️ Configure Teams Credentials"):
            teams_app_id = st.text_input("App ID", key="teams_app_id")
            teams_app_pwd = st.text_input("App Password", type="password", key="teams_app_pwd")
            teams_tenant = st.text_input("Tenant ID", key="teams_tenant")

            if st.button("💾 Save Teams Credentials"):
                if teams_app_id and teams_app_pwd and teams_tenant:
                    result, err = api_request(
                        "PUT",
                        "/api/credentials/teams",
                        json={"credentials": {
                            "app_id": teams_app_id,
                            "app_password": teams_app_pwd,
                            "tenant_id": teams_tenant
                        }}
                    )
                    if err:
                        st.error(err)
                    else:
                        st.success("Teams credentials saved successfully")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")

        st.markdown("---")

        # Webhook URLs
        st.markdown("""
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px; margin-top: 16px;">
            <h4 style="color: #64748B; margin: 0 0 12px 0;">Webhook URLs</h4>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.code(f"{API_BASE_URL}/api/webhook/whatsapp", language="text")
            st.caption("WhatsApp Webhook URL - Configure in Facebook Developer Console")
        with col2:
            st.code(f"{API_BASE_URL}/api/webhook/teams", language="text")
            st.caption("Teams Bot Webhook URL - Configure in Azure Portal")


# ============== Analytics Page ==============
elif page == "Analytics":
    st.markdown("""
    <div class="analytics-card" style="padding: 16px; border-radius: 12px; border-left: 4px solid #F59E0B; margin-bottom: 20px;">
        <h2 style="color: #F59E0B; margin: 0;">📈 Analytics & Reports</h2>
        <p style="color: #64748B; margin: 8px 0 0 0;">Track system usage and performance metrics</p>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown("""
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📊 Intent Usage</h3>
    </div>
    """, unsafe_allow_html=True)

    intent_stats, error = api_request("GET", "/api/analytics/intents")

    if not error and intent_stats:
        df_intents = pd.DataFrame(intent_stats)
        if not df_intents.empty:
            st.dataframe(
                df_intents.rename(columns={
                    "intent_name": "Intent",
                    "query_count": "Queries",
                    "accuracy": "Accuracy %"
                }),
                use_container_width=True
            )
        else:
            st.info("No intent statistics yet")
    else:
        st.info("No intent statistics yet")

    # Popular documents
    st.markdown("""
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📄 Popular Documents</h3>
    </div>
    """, unsafe_allow_html=True)

    popular, error = api_request("GET", "/api/analytics/popular-documents")

    if not error and popular:
        df_popular = pd.DataFrame(popular)
        if not df_popular.empty:
            st.dataframe(
                df_popular.rename(columns={
                    "document_id": "ID",
                    "document_name": "Document",
                    "access_count": "Access Count"
                }),
                use_container_width=True
            )
        else:
            st.info("No document access data yet")
    else:
        st.info("No popular documents yet")

    # Query logs
    st.markdown("""
    <div style="background: #FFFBEB; padding: 12px 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color: #F59E0B; margin: 0;">📝 Query Classification Log</h3>
    </div>
    """, unsafe_allow_html=True)

    # Fetch intents for filter
    all_intents, _ = api_request("GET", "/api/intents")

    # Filters for query logs
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_intent = st.selectbox("Filter by Intent", ["All Intents"] + [i.get("name") for i in (all_intents or [])])
    with col_f2:
        filter_status = st.selectbox("Filter by Status", ["All Status", "success", "failed"])

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

        df_logs = pd.DataFrame([
            {
                "Time": l["created_at"][:19],
                "Query Content": l.get("query", ""),
                "Detected Intent": l.get("intent_name", "-") or "General",
                "Confidence Score": f"{l.get('confidence', 0):.1%}",
                "Response Status": fmt_status(l.get("status", "failed"))
            }
            for l in logs["items"]
        ])
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No query logs found")

    # Export
    st.markdown("---")
    st.subheader("Export")

    if st.button("📥 Download Query Logs (CSV)"):
        try:
            response = requests.get(f"{API_BASE_URL}/api/analytics/export-logs")
            if response.status_code == 200:
                st.download_button(
                    label="📥 Click to Download",
                    data=response.content,
                    file_name="query_logs.csv",
                    mime="text/csv"
                )
            else:
                st.error("Failed to export")
        except Exception as e:
            st.error(f"Error: {e}")