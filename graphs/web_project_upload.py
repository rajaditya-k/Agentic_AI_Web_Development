from include import utils as ut
from core.state_types import UploadAppState
from auth.users import upload_to_blob, update_chat_history_pipeline
from langgraph.graph import StateGraph, END
import shutil
from db.eventHub import send_update
from core.config import llm_openai
from datetime import datetime
from pathlib import Path

async def script_file_generator(state: UploadAppState) -> UploadAppState:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    username = state.get("username", "")
    project_name = state.get("project_name","")
    history = state.get("chat_history", [])
    pipeline_details = state.get("pipeline_details", {})
    pipeline_details["UPLOAD"]={"username":username, "project_name":project_name,"CURRENT_STATUS":[{"overall_status":"IN-PROGRESS", "step":"SCRIPT_GENERATOR", "step_status": "IN-PROGRESS", "step_url": "", "start_time": start_time, "end_time":""}] }
    send_update(pipeline_details["UPLOAD"], partition_key=pipeline_details["UPLOAD"]["username"] + " ||| " + pipeline_details["UPLOAD"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    ut.unzip_zip_file(state)
    ut.delete_zip(state)
    project_folder = Path(state["work_dir"]) / "project"
    zip_path = Path(state["work_dir"]) / "project.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), 'zip', root_dir=project_folder.parent, base_dir=project_folder.name)
    ut.generate_sh_from_project(Path(state["work_dir"])/"project", Path(state["work_dir"]) / "generate_project_clean.sh", prefix="project")
    ut.sanitize_script(Path(state["work_dir"]) / "generate_project_clean.sh",Path(state["work_dir"]) / "generate_project_clean_sanitized.sh")
    final_sh_path=Path(state["work_dir"]) / "generate_project_clean_sanitized.sh"
    final_code_sanitized_script_blob_url = upload_to_blob(state["username"], state["project_id"], final_sh_path)
    for hist in history:
        if "url" in hist and (hist['step']=="final_code_sanitized_blob"):
            hist['url']=final_code_sanitized_script_blob_url
    final_code_blob_url = upload_to_blob(state["username"], state["project_id"], zip_path)
    for hist in history:
        if "url" in hist and (hist['step']=="project_zip_blob"):
            hist['url']=final_code_blob_url
    end_time=datetime.now().strftime(fmt)
    pipeline_details["UPLOAD"]={"username":username, "project_name":project_name,"CURRENT_STATUS":[{"overall_status":"IN-PROGRESS", "step":"SCRIPT_GENERATOR", "step_status": "DONE", "step_url": final_code_sanitized_script_blob_url, "start_time": start_time, "end_time":end_time}] }
    send_update(pipeline_details["UPLOAD"], partition_key=pipeline_details["UPLOAD"]["username"] + " ||| " + pipeline_details["UPLOAD"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"final_script_file": final_sh_path, "chat_history": history, "pipeline_details": pipeline_details, "pipeline_start_time": start_time}


async def code_document_generator_post_upload(state: UploadAppState) -> UploadAppState:
    return ut.generate_code_documentation(state,llm_openai,'UPLOAD')


async def all_steps_done(state: UploadAppState) -> UploadAppState:
    history = state.get("chat_history", [])
    zip_entries = [s for s in history if s.get("step") == "project_zip_blob"]
    zip_url = zip_entries[-1]["url"]
    fmt="%Y-%m-%d:%H:%M:%S"
    end_time=datetime.now().strftime(fmt)
    pipeline_details = state.get("pipeline_details", {})
    tmp_dict={}
    tmp_dict=pipeline_details["UPLOAD"]["CURRENT_STATUS"][len(pipeline_details["UPLOAD"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "DONE"
    tmp_dict["step"] = "ALL_STEPS_COMPLETED"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = zip_url
    tmp_dict["start_time"]=end_time
    tmp_dict["end_time"]=end_time
    pipeline_details["UPLOAD"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["UPLOAD"], partition_key=pipeline_details["UPLOAD"]["username"] + " ||| " + pipeline_details["UPLOAD"]["project_name"])
    pipeline_start_time = state.get("pipeline_start_time", "1900-01-01:00:00:00")
    st = datetime.strptime(pipeline_start_time, fmt)
    en = datetime.strptime(end_time, fmt)
    elapsed_minutes = (en - st).total_seconds() / 60
    duration = f"{elapsed_minutes:.2f}"
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"chat_history": history,"pipeline_details": pipeline_details, "pipeline_end_time": end_time, "duration": duration}

def build_project_upload_graph():
    graph = StateGraph(UploadAppState)
    graph.add_node("script_file_generator", script_file_generator)
    graph.add_node("code_document_generator_post_upload", code_document_generator_post_upload)
    graph.add_node("all_steps_done", all_steps_done)
    graph.set_entry_point("script_file_generator")
    graph.add_edge("script_file_generator", "code_document_generator_post_upload")
    graph.add_edge("code_document_generator_post_upload", "all_steps_done")
    graph.add_edge("all_steps_done", END)
    return graph.compile()


UPLOAD_PROJECT = build_project_upload_graph()

