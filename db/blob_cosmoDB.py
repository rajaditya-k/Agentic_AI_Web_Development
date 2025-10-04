from core.config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE, COSMOS_CONTAINER, BLOB_CONN_STR, BLOB_CONTAINER
import streamlit as st
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.cosmos import CosmosClient, PartitionKey, exceptions

@st.cache_resource
def get_blob_container_client():
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
    try:
        container_client.create_container()
    except Exception:
        pass
    return container_client


@st.cache_resource
def get_cosmos_container():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    try:
        db = client.create_database_if_not_exists(id=COSMOS_DATABASE)
        container = db.create_container_if_not_exists(
            id=COSMOS_CONTAINER,
            partition_key=PartitionKey(path="/username"),
            offer_throughput=400,
        )
    except exceptions.CosmosHttpResponseError:
        db = client.get_database_client(COSMOS_DATABASE)
        container = db.get_container_client(COSMOS_CONTAINER)
    return container


container = get_cosmos_container()
blob_container_client = get_blob_container_client()