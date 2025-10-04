from db.blob_cosmoDB import container, blob_container_client
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from pathlib import Path



def upload_to_blob(user_id: str, project_id: str, file_path: str, blob_name: str = None) -> str:
    """
    Upload a local file to Blob storage and return a secure SAS URL for downloading.
    """
    if blob_name is None:
        blob_name = f"{user_id}/{project_id}/{Path(file_path).name}"

    blob_client = blob_container_client.get_blob_client(blob_name)

    with open(file_path, "rb") as fd:
        blob_client.upload_blob(fd, overwrite=True)

    # Generate a SAS token valid for 1 day
    sas_token = generate_blob_sas(
        account_name=blob_client.account_name,
        container_name=blob_client.container_name,
        blob_name=blob_client.blob_name,
        account_key=blob_container_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(days=365*100),
    )

    sas_url = f"{blob_client.url}?{sas_token}"
    return sas_url


def delete_user_blobs_prefix(username: str, project_name: str, project_id : str, ind: int):
    prefix=""
    if ind==0:
        prefix = f"{username}/"
    elif ind==1:
        prefix = f"{username}/{project_id}"
    else:
        raise RuntimeError("Invalid Argument")
    blobs = list(blob_container_client.list_blobs(name_starts_with=prefix))
    if not blobs:
        print(f"No blobs found for prefix {prefix}")
        return
    for blob in blobs:
        try:
            blob_container_client.delete_blob(blob.name)
            print(f"Deleted blob: {blob.name}")
        except Exception as e:
            print(f"Failed to delete {blob.name}: {e}")
    for blob in blob_container_client.list_blobs(name_starts_with=prefix):
        blob_container_client.delete_blob(blob.name)


def get_user(username: str) -> Dict[str, Any]:
    query = f'SELECT * FROM c WHERE c.username = "{username}"'
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items[0] if items else None


def create_user(username: str, password_hash: str) -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
        "projects": [],
    }
    container.create_item(body=doc)
    return doc


def upsert_user_doc(user_doc: Dict[str, Any]):
    container.upsert_item(user_doc)


def update_chat_history(username: str, user_id: str, project_id: str, new_chat_history: list):
    user_doc = get_user(username)
    flag=0
    if not user_doc:
        raise RuntimeError("User not found")
    projects = user_doc.get("projects", []) if user_doc else []
    for proj in projects:
        if proj.get("project_id") == project_id:
            proj["chat_history"] = new_chat_history
            flag=1
            break
    if flag==0:
        raise RuntimeError("Project not found")
    upsert_user_doc(user_doc)

def update_pipeline_details(username: str, user_id: str, project_id: str, pipeline_details: dict):
    user_doc = get_user(username)
    flag=0
    if not user_doc:
        raise RuntimeError("User not found")
    projects = user_doc.get("projects", []) if user_doc else []
    for proj in projects:
        if proj.get("project_id") == project_id:
            proj["pipeline_details"] = pipeline_details
            flag=1
            break
    if flag==0:
        raise RuntimeError("Project not found")
    upsert_user_doc(user_doc)

def update_chat_history_pipeline(username: str, user_id: str, project_id: str, new_chat_history: list,pipeline_details: dict):
    user_doc = get_user(username)
    flag=0
    if not user_doc:
        raise RuntimeError("User not found")
    projects = user_doc.get("projects", []) if user_doc else []
    for proj in projects:
        if proj.get("project_id") == project_id:
            proj["pipeline_details"] = pipeline_details
            proj["chat_history"] = new_chat_history
            flag=1
            break
    if flag==0:
        raise RuntimeError("Project not found")
    upsert_user_doc(user_doc)


def add_project_to_user(username: str, user_id: str, project_obj: dict):
    user_doc = get_user(username)
    if not user_doc:
        raise RuntimeError("User not found")
    user_doc.setdefault("projects", []).append(project_obj)
    upsert_user_doc(user_doc)


def clear_user_projects(username: str, user_id: str):
    user_doc = get_user(username)
    if not user_doc:
        return
    user_doc["projects"] = []
    upsert_user_doc(user_doc)


def clear_user_memory(username: str, user_id: str, clear_blobs: bool = False):
    clear_user_projects(username, user_id)
    if clear_blobs:
        delete_user_blobs_prefix(username,'','',0)


def clear_single_project(username: str, project_name: str, project_id : str):
    """Remove a single project from user's projects and optionally delete its blobs."""
    user_doc = get_user(username)
    if not user_doc:
        return

    # Keep all projects except the one being cleared
    user_doc["projects"] = [
        proj for proj in user_doc.get("projects", []) if proj["project_id"] != project_id
    ]

    upsert_user_doc(user_doc)
    delete_user_blobs_prefix(username, project_name, project_id, 1)


