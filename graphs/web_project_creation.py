from include import utils as ut
from langchain_core.output_parsers import StrOutputParser
from core.state_types import AppStateProject
from auth.users import upload_to_blob, update_chat_history_pipeline
import subprocess
import zipfile
from langgraph.graph import StateGraph, END
from datetime import datetime
import os
from db.eventHub import send_update
from core.config import llm_openai


async def wireframe_generator(state: AppStateProject) -> AppStateProject:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    username = state.get("username", "")
    project_name = state.get("project_name","")
    pipeline_details = state.get("pipeline_details", {})
    pipeline_details["CREATE"]={"username":username, "project_name":project_name,"CURRENT_STATUS":[{"overall_status":"IN-PROGRESS", "step":"WIREFRAME_GENERATION", "step_status": "IN-PROGRESS", "step_url": "", "start_time": start_time, "end_time":""}] }
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    poml = ut.safe_load_poml("web_app_creator_pomls/wireframe_prompt.poml")
    chain = poml | llm_openai | StrOutputParser()
    history = state.get("chat_history", [])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    wireframe_text = chain.invoke({"requirements": state.get("requirements", "")})
    input_txt = os.path.join(state["work_dir"], "input.txt")
    with open(input_txt, "w", encoding="utf-8") as f:
        f.write(state.get("requirements", ""))
    print("Wireframe done")
    input_url = upload_to_blob(state["username"], state["project_id"], input_txt)
    history.append(
        {
            "project_id": state["project_id"],
            "step": "input_blob",
            "url": input_url,
            "status" : "DONE",
        }
    )
    wireframe_path = os.path.join(state["work_dir"], "wireframe.md")
    with open(wireframe_path, "w", encoding="utf-8") as f:
        f.write(wireframe_text)
    wireframe_url = upload_to_blob(state["username"], state["project_id"], wireframe_path)

    history.append(
        {
            "project_id": state["project_id"],
            "step": "wireframe_blob",
            "url": wireframe_url,
            "status" : "DONE",
        }
    )
    end_time=datetime.now().strftime(fmt)
    pipeline_details["CREATE"]={"username":username, "project_name":project_name,"CURRENT_STATUS":[{"overall_status":"IN-PROGRESS", "step":"WIREFRAME_GENERATION", "step_status": "DONE", "step_url": wireframe_url, "start_time": start_time, "end_time":end_time}] }
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    return {"wireframe": wireframe_text, "chat_history": history, "pipeline_details": pipeline_details, "pipeline_start_time": start_time}

async def high_fidelity_mockup_generator(state: AppStateProject) -> AppStateProject:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    poml = ut.safe_load_poml("web_app_creator_pomls/high_fidelity_mockup.poml")
    chain = poml | llm_openai | StrOutputParser()
    history = state.get("chat_history", [])
    pipeline_details = state.get("pipeline_details", {})
    tmp_dict={}
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "HIGH_FIDELITY_MOCKUP_GENERATOR"
    tmp_dict["step_status"] = "IN-PROGRESS"
    tmp_dict["step_url"] = ""
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=""
    pipeline_details["CREATE"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    mockup_text = chain.invoke({"wireframe": state.get("wireframe", "")})
    print("High Fidelity Mockup done")
    High_Fidelity_Path = os.path.join(state["work_dir"], "mockup.md")
    with open(High_Fidelity_Path, "w", encoding="utf-8") as f:
        f.write(mockup_text)
    High_Fidelity_url = upload_to_blob(state["username"], state["project_id"], High_Fidelity_Path)
    history.append(
        {
            "project_id": state["project_id"],
            "step": "mockup_blob",
            "url": High_Fidelity_url,
            "status" : "DONE",
        }
    )
    end_time=datetime.now().strftime(fmt)
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "HIGH_FIDELITY_MOCKUP_GENERATOR"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = High_Fidelity_url
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=end_time
    pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"high_fidelity_design": mockup_text, "chat_history": history, "pipeline_details": pipeline_details}

async def api_generator(state: AppStateProject) -> AppStateProject:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    poml = ut.safe_load_poml("web_app_creator_pomls/api_contract_agent.poml")
    chain = poml | llm_openai | StrOutputParser()
    pipeline_details = state.get("pipeline_details", {})
    history = state.get("chat_history", [])
    tmp_dict={}
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "API_LIST_GENERATOR"
    tmp_dict["step_status"] = "IN-PROGRESS"
    tmp_dict["step_url"] = ""
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=""
    #pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    pipeline_details["CREATE"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    api_text = chain.invoke({"wireframe": state.get("wireframe", "")})
    print("API done")
    API_Path = os.path.join(state["work_dir"], "api_contract.txt")
    with open(API_Path, "w", encoding="utf-8") as f:
        f.write(api_text)
    API_url = upload_to_blob(state["username"], state["project_id"], API_Path)
    history.append(
        {
            "project_id": state["project_id"],
            "step": "api_blob",
            "url": API_url,
            "status" : "DONE",
        }
    )
    end_time=datetime.now().strftime(fmt)
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "API_LIST_GENERATOR"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = API_url
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=end_time
    pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"api_contract_str": api_text, "chat_history": history, "pipeline_details": pipeline_details}

async def full_stack_script_draft_generator(state: AppStateProject) -> AppStateProject:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    poml = ut.safe_load_poml("web_app_creator_pomls/full_stack_code_script_generator.poml")
    chain = poml | llm_openai | StrOutputParser()
    pipeline_details = state.get("pipeline_details", {})
    history = state.get("chat_history", [])
    tmp_dict={}
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "INITIAL_DRAFT_GENERATOR"
    tmp_dict["step_status"] = "IN-PROGRESS"
    tmp_dict["step_url"] = ""
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=""
    #pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    pipeline_details["CREATE"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    draft_code = chain.invoke({"mockup": state.get("high_fidelity_design", ""), "api_contract": state.get("api_contract_str", "")})
    local_path = os.path.join(state["work_dir"], "generate_project.sh")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(draft_code)
    initial_draft_url = upload_to_blob(state["username"], state["project_id"], local_path)
    history.append(
        {
            "project_id": state["project_id"],
            "step": "draft_code_text",
            "url": initial_draft_url,
            "status" : "DONE",
        }
    )
    print("Initial Draft done")
    end_time=datetime.now().strftime(fmt)
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "INITIAL_DRAFT_GENERATOR"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = initial_draft_url
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=end_time
    pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"initial_script_file": local_path, "chat_history": history, "pipeline_details": pipeline_details}

async def full_stack_script_final_generator(state: AppStateProject) -> AppStateProject:
    fmt="%Y-%m-%d:%H:%M:%S"
    start_time=datetime.now().strftime(fmt)
    pipeline_details = state.get("pipeline_details", {})
    history = state.get("chat_history", [])
    tmp_dict={}
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "PROJECT_ZIP_GENERATOR"
    tmp_dict["step_status"] = "IN-PROGRESS"
    tmp_dict["step_url"] = ""
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=""
    #pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    pipeline_details["CREATE"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    poml = ut.safe_load_poml("web_app_creator_pomls/full_stack_scipt_verifier.poml")
    chain = poml | llm_openai | StrOutputParser()
    draft_path = state.get("initial_script_file")
    if not draft_path or not os.path.exists(draft_path):
        raise RuntimeError("Draft script not found in state for final generator")
    draft_code=""
    with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
        draft_code = f.read()
    llm_input = {"code_designer": draft_code}
    refined_code = chain.invoke(llm_input)
    final_path = os.path.join(state["work_dir"], "generate_project_clean.sh")
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(refined_code)
    generate_project_clean_url = upload_to_blob(state["username"], state["project_id"], final_path)
    history.append(
        {
            "project_id": state["project_id"],
            "step": "generate_project_clean_text",
            "url": generate_project_clean_url,
            "status" : "DONE",
        }
    )
    print("generate project clean done")
    try:
        clean_path = os.path.join(state["work_dir"], "generate_project_clean_sanitized.sh")
        ut.sanitize_script(final_path, clean_path)
        final_blob_sanitized_url = upload_to_blob(state["username"], state["project_id"], clean_path)
        history.append({"project_id": state["project_id"], "step": "final_code_sanitized_blob", "url": final_blob_sanitized_url,"status" : "DONE",})
        print("generate project clean sanitized done")
    except Exception as e:
        raise RuntimeError(f"Issue with sanitized process: {e}")
    try:
        script_name = "generate_project_clean_sanitized.sh"
        subprocess.run(["bash", script_name], cwd=state["work_dir"],capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Project generation script failed: {e}")
    generated_folder = os.path.join(state["work_dir"], "project")
    if not os.path.exists(generated_folder):
        raise RuntimeError("Subprocess did not generate expected project folder")
    zip_path = os.path.join(state["work_dir"], "project.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(generated_folder):
            for file in files:
                full_fp = os.path.join(root, file)
                rel_fp = os.path.relpath(full_fp, state["work_dir"])  # preserve folder structure
                zf.write(full_fp, arcname=rel_fp)
    print("reached upload blob")
    zip_blob_url = upload_to_blob(state["username"], state["project_id"], zip_path)
    print("finished upload blob")
    history.append({"project_id": state["project_id"], "step": "project_zip_blob", "url": zip_blob_url,"status" : "DONE",})
    print("Final Draft done")
    end_time=datetime.now().strftime(fmt)
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "IN-PROGRESS"
    tmp_dict["step"] = "PROJECT_ZIP_GENERATOR"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = zip_blob_url
    tmp_dict["start_time"]=start_time
    tmp_dict["end_time"]=end_time
    pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"final_script_file": clean_path, "chat_history": history, "documentation": None, "pipeline_details": pipeline_details}

async def code_document_generator(state: AppStateProject) -> AppStateProject:
    return ut.generate_code_documentation(state,llm_openai,'CREATE')

async def all_steps_done(state: AppStateProject) -> AppStateProject:
    history = state.get("chat_history", [])
    zip_entries = [s for s in history if s.get("step") == "project_zip_blob"]
    zip_url = zip_entries[-1]["url"]
    fmt="%Y-%m-%d:%H:%M:%S"
    end_time=datetime.now().strftime(fmt)
    pipeline_details = state.get("pipeline_details", {})
    tmp_dict={}
    tmp_dict=pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].copy()
    tmp_dict["overall_status"] = "DONE"
    tmp_dict["step"] = "ALL_STEPS_COMPLETED"
    tmp_dict["step_status"] = "DONE"
    tmp_dict["step_url"] = zip_url
    tmp_dict["start_time"]=end_time
    tmp_dict["end_time"]=end_time
    #pipeline_details["CREATE"]["CURRENT_STATUS"][len(pipeline_details["CREATE"]["CURRENT_STATUS"])-1].update(tmp_dict)
    pipeline_details["CREATE"]["CURRENT_STATUS"].append(tmp_dict)
    send_update(pipeline_details["CREATE"], partition_key=pipeline_details["CREATE"]["username"] + " ||| " + pipeline_details["CREATE"]["project_name"])
    pipeline_start_time = state.get("pipeline_start_time", "1900-01-01:00:00:00")
    st = datetime.strptime(pipeline_start_time, fmt)
    en = datetime.strptime(end_time, fmt)
    elapsed_minutes = (en - st).total_seconds() / 60
    duration = f"{elapsed_minutes:.2f}"
    update_chat_history_pipeline(state.get("username", ""), state.get("userid", ""), state.get("project_id", ""), history, pipeline_details)
    return {"chat_history": history,"pipeline_details": pipeline_details, "pipeline_end_time": end_time, "duration": duration}


def build_project_create_graph():
    graph = StateGraph(AppStateProject)
    graph.add_node("wireframe_generator", wireframe_generator)
    graph.add_node("high_fidelity_mockup_generator", high_fidelity_mockup_generator)
    graph.add_node("api_generator", api_generator)
    graph.add_node("full_stack_script_draft_generator", full_stack_script_draft_generator)
    graph.add_node("full_stack_script_final_generator", full_stack_script_final_generator)
    graph.add_node("code_document_generator", code_document_generator)
    graph.add_node("all_steps_done", all_steps_done)
    graph.set_entry_point("wireframe_generator")
    graph.add_edge("wireframe_generator", "high_fidelity_mockup_generator")
    graph.add_edge("high_fidelity_mockup_generator", "api_generator")
    graph.add_edge("api_generator", "full_stack_script_draft_generator")
    graph.add_edge("full_stack_script_draft_generator", "full_stack_script_final_generator")
    graph.add_edge("full_stack_script_final_generator", "code_document_generator")
    graph.add_edge("code_document_generator", "all_steps_done")
    graph.add_edge("all_steps_done", END)
    return graph.compile()




# Example dictionary (simulate changes)


APP_PROJECT = build_project_create_graph()

