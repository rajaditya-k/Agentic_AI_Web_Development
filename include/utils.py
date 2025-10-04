import tempfile
from poml.integration.langchain import LangchainPomlTemplate
import re
import os
from pathlib import Path
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
from auth.users import upload_to_blob, update_chat_history_pipeline
import zipfile
import time
from azure.eventhub import EventHubProducerClient, EventData
from core.config import EVENTHUB_CONN_STR, EVENTHUB_NAME

producer = EventHubProducerClient.from_connection_string(
    conn_str=EVENTHUB_CONN_STR,
    eventhub_name=EVENTHUB_NAME
)

def sanitize_script(input_file: str, output_file: str):
    """Reads a script file, removes invisible/control characters,
    normalizes line endings, and writes a clean version."""
    with open(input_file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    content = re.sub(r"[^\x20-\x7E\n\t]", "", content)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = re.sub(r"```[a-zA-Z]*\n?", "", content)
    content = content.replace("```", "")

    with open(output_file, "w", encoding="utf-8", errors="replace", newline="\n") as f:
        f.write(content)

    print(f"Sanitized script written to: {output_file}")


def safe_load_poml(path: str, speaker_mode: bool = False) -> LangchainPomlTemplate:
    """Load POML safely regardless of encoding issues, always using from_file."""
    try:
        # First try with utf-8-sig (handles BOM if present)
        with open(path, "r", encoding="utf-8-sig", errors="strict") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 which can decode any byte
        with open(path, "r", encoding="latin-1", errors="replace") as f:
            content = f.read()
        # Normalize into UTF-8 safe text
        content = content.encode("latin-1").decode("utf-8", errors="replace")

    # Remove stray control chars except whitespace/newlines
    import re
    content = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", content)

    # Write sanitized content to a temporary .poml file
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".poml", mode="w", encoding="utf-8", newline="\n"
    )
    tmp.write(content)
    tmp.close()

    # Load with LangchainPomlTemplate.from_file
    return LangchainPomlTemplate.from_file(tmp.name, speaker_mode=speaker_mode)

def generate_sh_from_project(project_root: Path, sh_path: Path, prefix: str = "project"):
    """
    Generate a .sh script that recreates the folder tree under `project_root`.
    - Uses POSIX paths (as_posix) so the produced .sh is valid for bash.
    - Writes everything to memory and writes the .sh file once (utf-8).
    - prefix: the top-level folder name to use inside the script (e.g. "project" or "project").
    """
    project_root = Path(project_root)
    if not project_root.exists():
        raise FileNotFoundError(f"project_root does not exist: {project_root}")

    lines = []
    lines.append("#!/usr/bin/env bash")
    lines.append("set -e")
    lines.append("")  # blank

    lines.append(f"# Auto-generated script to recreate {project_root.name}")
    lines.append("")  # blank

    # Collect directories (preserve structure). Use relative POSIX paths.
    dir_set = set()
    for p in project_root.rglob('*'):
        if p.is_dir():
            rel = p.relative_to(project_root)
            # represent root-dir children with their posix path ('' -> skip)
            if str(rel) == ".":
                continue
            dir_set.add(rel.as_posix())

    # Write mkdir lines (sorted for determinism)
    lines.append("# Create project directories")
    for d in sorted(dir_set):
        lines.append(f"mkdir -p {prefix}/{d}")
    lines.append("")  # blank

    # Write files (sorted for determinism)
    # We iterate files and put content inside heredoc blocks.
    for p in sorted(project_root.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(project_root).as_posix()
        target = f"{prefix}/{rel}"
        # Read file content robustly (utf-8 preferred, fallback to latin-1)
        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            try:
                content = p.read_text(encoding="latin-1")
            except Exception:
                # skip unreadable/binary files
                continue

        # Use a quoted heredoc delimiter to avoid variable expansion in the content
        lines.append(f"cat > {target} << 'EOF'")
        lines.append(content)
        lines.append("EOF")
        lines.append("")  # blank between files

    # Final message
    lines.append(f"echo 'Project scaffolding complete: {prefix}/'")

    # Join and write once
    script_content = "\n".join(lines)
    sh_path.write_text(script_content, encoding="utf-8")
    try:
        sh_path.chmod(0o755)
    except Exception:
        pass

    return sh_path


import json
def send_update(update_dict,partition_key=None):
    event_data = EventData(json.dumps(update_dict))
    with producer:
        event_batch = producer.create_batch(partition_key=partition_key)
        event_batch.add(event_data)
        producer.send_batch(event_batch)
    print("Sent:", update_dict)


def generate_code_documentation(state,llm_model,pipeline_name):
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    poml = safe_load_poml("web_app_creator_pomls/Code_Document_Generator.poml")
    chain = poml | llm_model | StrOutputParser()
    final_path = state.get("final_script_file")
    if not final_path or not os.path.exists(final_path):
        return {"documentation": "", "chat_history": state.get("chat_history", [])}
    with open(final_path, "r", encoding="utf-8", errors="replace") as f:
        code_content = f.read()
    pipeline_details = state.get("pipeline_details", {})
    history = state.get("chat_history", [])
    tmp_dict={}
    tmp_dict=pipeline_details[pipeline_name]["CURRENT_STATUS"][len(pipeline_details[pipeline_name]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "DOCUMENTATION_GENERATOR"
    tmp_dict["step_status"] = "IN-PROGRESS"
    tmp_dict["step_url"] = ""
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=""
    pipeline_details[pipeline_name]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details[pipeline_name], partition_key=pipeline_details[pipeline_name]["username"] + " ||| " + pipeline_details[pipeline_name]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    documentation = chain.invoke({"code_designer_refined": code_content})
    pipeline_details = state.get("pipeline_details", [])
    doc_path = os.path.join(state["work_dir"], "code_documentation.html")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(documentation)
    doc_blob_url = upload_to_blob(state["username"], state["project_id"], doc_path)
    history.append({"project_id": state["project_id"], "step": "documentation_blob", "url": doc_blob_url,"status" : "DONE",})
    print("Code Documentation Done")
    end_time=datetime.now().strftime(fmt)
    tmp_dict=pipeline_details[pipeline_name]["CURRENT_STATUS"][len(pipeline_details[pipeline_name]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "DOCUMENTATION_GENERATOR"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = doc_blob_url
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=end_time
    pipeline_details[pipeline_name]["CURRENT_STATUS"][len(pipeline_details[pipeline_name]["CURRENT_STATUS"])-1].update(tmp_dict)
    send_update(pipeline_details[pipeline_name], partition_key=pipeline_details[pipeline_name]["username"] + " ||| " + pipeline_details[pipeline_name]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"documentation": documentation, "chat_history": history, "pipeline_details": pipeline_details}

def unzip_zip_file(state):
    project = Path(state["work_dir"]) / "project"
    project.mkdir(parents=True, exist_ok=True)
    zip_path = os.path.join(state["work_dir"], "project.zip")
    with zipfile.ZipFile(zip_path, "r") as zf:
        top_level_names = set()
        for info in zf.infolist():
            name = info.filename
            if not name:
                continue
            parts = Path(name).parts
            if not parts:
                continue
            top_level_names.add(parts[0])

        allowed_top = {"backend", "frontend", "tests"}
        strip_root = False
        if len(top_level_names) == 1:
            only = next(iter(top_level_names)).lower()
            if only not in allowed_top and not only.startswith("README"):
                strip_root = True
                strip_root_name = only
            else:
                strip_root = False

        for info in zf.infolist():
            name = info.filename
            if not name:
                continue
            is_dir = name.endswith("/")
            parts = Path(name).parts
            if strip_root:
                if len(parts) > 1:
                    parts = parts[1:]
                else:
                    continue

            if not parts:
                continue

            rel_path = Path(*parts)
            top = rel_path.parts[0].lower()
            if top not in allowed_top and not (rel_path.name.lower().startswith("readme") and len(rel_path.parts) == 1):
                continue
            if top == "frontend":
                if any(p.lower() == "node_modules" for p in rel_path.parts):
                    continue
            elif top in ("backend", "tests"):
                if any(p.lower() == "__pycache__" for p in rel_path.parts):
                    continue
                if is_dir:
                # create dir entry
                    target_dir = project / rel_path
                    target_dir.mkdir(parents=True, exist_ok=True)
                    continue
                name_lower = rel_path.name.lower()
                if not (name_lower.endswith(".py") or name_lower.endswith(".sh") or name_lower == "requirements.txt"):
                    continue
            target_path = project / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if is_dir:
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())

def delete_zip(state):
    for zip_file in Path(state["work_dir"]).glob("*.zip"):
        try:
            zip_file.unlink()
        except Exception as e:
            raise RuntimeError(f"Could not delete {zip_file}: {e}")

def getStatusDictionary():
    pass


