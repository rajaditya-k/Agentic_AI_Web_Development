import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sys
from pathlib import Path


load_dotenv()
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")
BLOB_CONN_STR = os.getenv("BLOB_CONN_STR")
BLOB_CONTAINER = os.getenv("BLOB_CONTAINER")
EVENTHUB_CONN_STR = os.getenv("EVENTHUB_CONN_STR")
EVENTHUB_NAME = os.getenv("EVENTHUB_NAME")
EVENT_HUB_BLOB_STORAGE_CONN_STR = os.getenv("EVENT_HUB_BLOB_STORAGE_CONN_STR")
EVENT_HUB_BLOB_CONTAINER_NAME = os.getenv("EVENT_HUB_BLOB_CONTAINER_NAME")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

llm_openai = ChatOpenAI(model="gpt-5-mini")

def ensure_env_set(var_name: str):
    if not os.getenv(var_name):
        raise RuntimeError(f"Environment variable {var_name} is required but not set.")

ensure_env_set("COSMOS_ENDPOINT")
ensure_env_set("COSMOS_KEY")
ensure_env_set("COSMOS_DATABASE")
ensure_env_set("COSMOS_CONTAINER")
ensure_env_set("BLOB_CONN_STR")
ensure_env_set("BLOB_CONTAINER")
ensure_env_set("OPENAI_API_KEY")