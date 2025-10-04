from typing import Dict, Any, TypedDict, List

class AppStateProject(TypedDict, total=False):
    project_id: str
    project_name: str
    username: str
    userid: str
    requirements: str
    wireframe: str
    high_fidelity_design: str
    api_contract_str: str
    initial_script_file: str
    final_script_file: str
    documentation: str
    chat_history: List[Dict[str, Any]]
    pipeline_details : Dict
    pipeline_start_time : str
    pipeline_end_time : str
    duration : float
    work_dir: str


class UploadAppState(TypedDict, total=False):
    project_id: str
    project_name: str
    username: str
    final_script_file: str
    documentation: str
    chat_history: List[Dict[str, Any]]
    pipeline_details : Dict
    pipeline_start_time : str
    pipeline_end_time : str
    duration : float
    work_dir: str