import streamlit as st 
import tempfile
import uuid
from datetime import datetime
import asyncio as _asyncio
import json
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
import zipfile
import requests
from auth.password import hash_password, verify_password
from core.config import EVENT_HUB_BLOB_STORAGE_CONN_STR, EVENT_HUB_BLOB_CONTAINER_NAME, EVENTHUB_CONN_STR, EVENTHUB_NAME
from pathlib import Path
import os
from auth.users import get_user,create_user,clear_user_memory,add_project_to_user,clear_single_project
from core.state_types import UploadAppState, AppStateProject
from graphs.web_project_creation import APP_PROJECT
from graphs.web_project_upload import UPLOAD_PROJECT
from include import utils as ut

# -------------------------
# Setup Streamlit session state
# -------------------------

# -------------------------
# Page setup
# -------------------------
st.set_page_config(page_title="Web App Creator", layout="wide")
st.title("Web App Creator — Projects + Feedback")

# -------------------------
# Sidebar authentication
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.header("Account")
if st.session_state.user:
    st.sidebar.write(f"Signed in as: **{st.session_state.user['username']}**")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()
else:
    with st.sidebar.expander("Sign up"):
        new_user = st.text_input("Choose username", key="su_user")
        new_pass = st.text_input("Choose password", key="su_pass", type="password")
        if st.button("Create account", key="create_acc"):
            if get_user(new_user):
                st.sidebar.error("Username already exists")
            else:
                create_user(new_user, hash_password(new_pass))
                st.sidebar.success("Account created — please login")

    with st.sidebar.expander("Log in"):
        login_user = st.text_input("Username", key="li_user")
        login_pass = st.text_input("Password", key="li_pass", type="password")
        if st.button("Log in", key="login_btn"):
            user_doc = get_user(login_user)
            if not user_doc:
                st.sidebar.error("No such user")
            elif verify_password(login_pass, user_doc["password_hash"]):
                st.session_state.user = {"id": user_doc["id"], "username": login_user}
                st.sidebar.success("Logged in")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

if not st.session_state.user:
    st.info("Please sign up or log in (use the sidebar).")
    st.stop()

current_username = st.session_state.user["username"]
current_user_id = st.session_state.user["id"]

# Sidebar memory controls
st.sidebar.markdown("---")
if st.sidebar.button("Clear User Data"):
    clear_user_memory(current_username, current_user_id, clear_blobs=True)
    st.sidebar.success("Cleared memory and blobs.")
    st.rerun()

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs(
    ["Generate Project", "Your Projects (Tree View)", "Project Status" ]
)

# ----------------------------
# Tab 1: Generate Project (unchanged)
# ----------------------------
with tab1:
    st.header("Create a new project")
    project_name = st.text_input("Project Name")
    requirements_text = st.text_area("Project requirements", height=200)

    if st.button("Run full creation pipeline"):
        if not project_name.strip():
            st.error("Please provide a project name.")
        elif not requirements_text.strip():
            st.error("Please provide requirements.")
        else:
            # Check for duplicate project name
            user_doc = get_user(current_username)
            existing_projects = user_doc.get("projects", []) if user_doc else []
            if any(p["project_name"].lower() == project_name.lower() for p in existing_projects):
                st.error("This project name has already been used. Please select a new name.")
                st.stop()

            project_id = str(uuid.uuid4())
            project_obj = {
                "project_id": project_id,
                "project_name": project_name,
                "created_by": current_username,
                "created_at": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),
                "chat_history": [],
                "pipeline_details": {}
            }
            add_project_to_user(current_username, current_user_id, project_obj)

            with tempfile.TemporaryDirectory() as tmpdir:
                init_state: AppStateProject = {
                    "project_id": project_id,
                    "project_name": project_name,
                    "username": current_username,
                    "requirements": requirements_text,
                    "work_dir": tmpdir,
                    "chat_history": [],
                    "pipeline_details": {},
                }

                st.info("Running pipeline...")
                try:
                    final_state = APP_PROJECT.ainvoke(init_state)
                    import asyncio as _asyncio
                    if _asyncio.iscoroutine(final_state):
                        final_state = _asyncio.run(final_state)
                except Exception as e:
                    st.exception(e)
                    st.stop()

# ----------------------------
# Tab 4: Project Status
# ----------------------------

with tab2:
    st.header("Your saved projects")

    user_doc = get_user(current_username)
    projects = user_doc.get("projects", []) if user_doc else []

    if not projects:
        st.info("You have no projects yet — create one from the 'Generate Project' tab.")
    else:
        st.subheader("📋 Your Projects")
        ignored_keywords = ["wireframe", "mockup", "api_contract", "generate_project.sh", "_text", "feedback"]

        # Helper to insert file path into nested tree dict
        def add_file_to_tree(tree: dict, relpath: str):
            parts = [p for p in relpath.split("/") if p != ""]
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            # mark file with None value
            node[parts[-1]] = None

        # Helper to ensure a directory exists in tree (for empty dirs)
        def ensure_dir_in_tree(tree: dict, reldir: str):
            parts = [p for p in reldir.split("/") if p != ""]
            node = tree
            for part in parts:
                node = node.setdefault(part, {})

        # Render the nested tree recursively into expanders/buttons
        def render_tree(node: dict, pid: str, prefix: str = ""):
            for name in sorted(node.keys(), key=lambda x: (0 if isinstance(node[x], dict) else 1, x.lower())):
                val = node[name]
                if isinstance(val, dict):
                    # directory
                    with st.expander(f"📁 {name}", expanded=False):
                        render_tree(val, pid, prefix + name + "/")
                else:
                    # file
                    btn_key = f"btn__{pid}__{(prefix + name).replace('/', '__')}"
                    if st.button(f"📄 {name}", key=btn_key):
                        st.session_state[f"selected_file_{pid}"] = prefix + name

        for proj in reversed(projects):
            pname = proj.get("project_name")
            pid = proj.get("project_id")
            chat_history = proj.get("chat_history", [])
            pipeline_details = proj.get("pipeline_details", {})
            col1, col2 , col3 = st.columns([7, 2, 2])
            exp=''
            with col1:
                exp = st.expander(f"{pname} (Project ID: {pid})", expanded=False)
            with col2:
                uploaded_file = st.file_uploader(
                    "Upload project.zip",
                    type=["zip"],
                    key=f"upload_{pid}"
                )
                if uploaded_file is not None:
                    if uploaded_file.name != "project.zip":
                        st.error("⚠️ Only 'project.zip' is allowed.")
                    else:
                        with tempfile.TemporaryDirectory() as tmpdir:
                            zip_path = Path(tmpdir) / "project.zip"
                            zip_path.write_bytes(uploaded_file.read())
                            st.success("✅ Uploaded 'project.zip' successfully.")
                            
                            init_upload_state: UploadAppState = {
                                "project_id": pid,
                                "project_name": pname,
                                "username": current_username,
                                "work_dir": tmpdir,
                                "chat_history": chat_history,
                                "pipeline_details": pipeline_details,
                            }
                            try:
                                final_upload_state = UPLOAD_PROJECT.ainvoke(init_upload_state)
                                import asyncio as _asyncio
                                if _asyncio.iscoroutine(final_upload_state):
                                    final_upload_state = _asyncio.run(final_upload_state)
                            except Exception as e:
                                st.exception(e)
                                st.stop()
                            #chat_history: List[Dict[str, Any]] = final_upload_state.get("chat_history", [])
                            #new_upload_chat_history=chat_history.copy()
                            #update_chat_history(current_username, current_user_id, project_id, new_upload_chat_history)
                            #st.success(f"Project successfully uploaded and documentation updated.")
                            # >>> call your agent with tmpdir and project_id/project_name <<<

            with col3:
                if st.button(f"🗑️ Clear", key=f"clear_{pid}"):
                    clear_single_project(current_username, pname, pid)
                    st.success(f"Project '{pname}' cleared successfully.")
                    st.rerun()

            with exp:
                st.write(f"👤 Created by: {proj.get('created_by', current_username)}")

                history = proj.get("chat_history", [])
                zip_entries = [s for s in history if s.get("step") == "project_zip_blob"]
                doc_entries = [s for s in history if s.get("step") == "documentation_blob"]
                if not zip_entries:
                    st.warning("No project ZIP found for this project.")
                    continue

                zip_url = zip_entries[-1]["url"]
                doc_url = doc_entries[-1]["url"]
                st.markdown(f"**📥 Download Project ZIP:** [Download]({zip_url})")
                st.markdown(f"**📥 Download Project Documentation:** [Download]({doc_url})")
                cache_key = f"project_cache_{pid}"

                # If not cached, download and build file tree + contents
                if cache_key not in st.session_state:
                    try:
                        resp = requests.get(zip_url, timeout=20)
                        resp.raise_for_status()
                        files_map = {}   # relpath -> content (None for binary/unreadable)
                        tree = {}        # nested dict for directory tree

                        with tempfile.TemporaryDirectory() as tmpdir:
                            zip_path = Path(tmpdir) / "project.zip"
                            zip_path.write_bytes(resp.content)

                            with zipfile.ZipFile(zip_path, "r") as zf:
                                zf.extractall(tmpdir)

                            # walk extracted files and build structures
                            for root, dirs, files in os.walk(tmpdir):
                                rel_root = os.path.relpath(root, tmpdir)
                                if rel_root == ".":
                                    rel_root = ""
                                # register directories (so empty dirs are kept)
                                for d in dirs:
                                    reldir = (os.path.join(rel_root, d)).lstrip("./")
                                    reldir_posix = Path(reldir).as_posix()
                                    if any(kw in d.lower() for kw in ignored_keywords):
                                        continue
                                    ensure_dir_in_tree(tree, reldir_posix)

                                for fname in files:
                                    # skip internal/ignored files
                                    if any(kw in fname.lower() for kw in ignored_keywords):
                                        continue
                                    full = os.path.join(root, fname)
                                    relpath = os.path.join(rel_root, fname).lstrip("./")
                                    relpath_posix = Path(relpath).as_posix()
                                    # try reading as text; fallback to None for binary
                                    try:
                                        content = Path(full).read_text(encoding="utf-8", errors="ignore")
                                    except Exception:
                                        content = None
                                    files_map[relpath_posix] = content
                                    add_file_to_tree(tree, relpath_posix)

                        st.session_state[cache_key] = {"files": files_map, "tree": tree}
                    except Exception as e:
                        st.error(f"⚠️ Error downloading/extracting ZIP: {e}")
                        continue

                # show explorer + preview side-by-side
                cache = st.session_state[cache_key]
                tree = cache["tree"]

                # ensure per-project selected file key
                selected_key = f"selected_file_{pid}"
                if selected_key not in st.session_state:
                    st.session_state[selected_key] = None

                explorer_col, preview_col = st.columns([1.2, 2])

                with explorer_col:
                    st.subheader("📂 Project Explorer")
                    if not tree:
                        st.info("Project folder is empty.")
                    else:
                        render_tree(tree, pid, prefix="")

                with preview_col:
                    st.subheader("📝 File Preview")
                    sel = st.session_state.get(selected_key)
                    if sel:
                        # get content from cache
                        content = cache["files"].get(sel)
                        if content is None:
                            st.warning("Binary file or cannot preview this file.")
                        else:
                            # determine language by suffix
                            suffix = Path(sel).suffix.lower()
                            if suffix == ".py":
                                st.code(content, language="python")
                            elif suffix in [".sh"]:
                                st.code(content, language="bash")
                            elif suffix in [".json"]:
                                st.code(content, language="json")
                            elif suffix in [".yaml", ".yml"]:
                                st.code(content, language="yaml")
                            elif suffix == ".md":
                                st.markdown(content)
                            else:
                                st.code(content)
                    else:
                        st.info("👆 Click a file on the left to preview it here.")
    

with tab3:
    st.header("💬 Project Status")
    user_doc = get_user(current_username)
    projects = user_doc.get("projects", []) if user_doc else []

    if not projects:
        st.info("You have no projects yet — create one from the 'Generate Project' tab.")
    else:
        st.subheader("📋 Your Projects")

        if "logs" not in st.session_state:
            st.session_state.logs = {}
        
        project_boxes = {}
        
        # This function is no longer needed, we'll format directly in the callback

        # Step 1: Build UI for each project
        for proj in reversed(projects):
            project_name = proj.get("project_name")
            project_id = proj.get("project_id")
            project_key = f"{current_username} ||| {project_name}"

            with st.expander(f"{project_name} (Project ID: {project_id})"):
                st.write("📡 Live logs for this project:")
                # Create a dedicated container for each project's logs
                log_box = st.container()
                project_boxes[project_key] = log_box

                # Initialize logs for this project in session state
                if project_key not in st.session_state.logs:
                    st.session_state.logs[project_key] = []
                    
        # Step 2: Define on_event callback
        async def on_event(partition_context, event):
            try:
                message = event.body_as_str()
                data = json.loads(message)
            except Exception as e:
                print(f"Error parsing event: {e}")
                return

            username = data.get("username")
            project_name = data.get("project_name")
            project_key = f"{username} ||| {project_name}"
            
            if username == current_username and project_key in project_boxes:
                # Add the new dictionary to the project's log list
                #st.session_state.logs[project_key].clear()
                st.session_state.logs[project_key].append(data)

                # Clear and re-render the log box for that project
                log_box = project_boxes[project_key]
                with log_box:
                    log_box.empty()  # Clear existing content
                    ent= [st.session_state.logs[project_key][len(st.session_state.logs[project_key])-1]]

                    #for entry in st.session_state.logs[project_key]:
                    for entry in ent:
                        # Use st.json for the full dictionary, as it handles nested structures well
                        #st.success("********************************************************************************************************")
                        with st.empty():
                            st.json(entry, expanded=False)
                            status_updates = entry.get("CURRENT_STATUS")
                            if status_updates:
                            #st.subheader("Current Status")
                                for step in status_updates:
                                    step_name = step.get("step", "N/A")
                                    step_status = step.get("step_status", "N/A")
                                    step_url = step.get("step_url")
                                
                                # Use markdown to properly display the URL
                                    log_line = f"**Step:** {step_name} | **Status:** {step_status}"
                                    if step_url:
                                        log_line += f" | **URL:** [{step_url}]({step_url})"
                                    st.markdown(log_line, unsafe_allow_html=False) # Important: set this to False
            
            #await partition_context.update_checkpoint(event)

        # Step 3: Single consumer client for all projects
        async def receive():
            checkpoint_store = BlobCheckpointStore.from_connection_string(
                EVENT_HUB_BLOB_STORAGE_CONN_STR, EVENT_HUB_BLOB_CONTAINER_NAME
            )
            client = EventHubConsumerClient.from_connection_string(
                conn_str=EVENTHUB_CONN_STR,
                consumer_group="freshgroup20250920185111",
                eventhub_name=EVENTHUB_NAME,
            )
            async with client:
                await client.receive(
                    on_event=on_event,
                    starting_position="@latest"
                )

        # Step 4: Run only once
        if "loop_started" not in st.session_state:
            st.session_state["loop_started"] = True
            _asyncio.run(receive())
