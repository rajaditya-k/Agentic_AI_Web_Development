from azure.eventhub import EventHubProducerClient, EventData
from core.config import EVENTHUB_CONN_STR, EVENTHUB_NAME

import json


producer = EventHubProducerClient.from_connection_string(
    conn_str=EVENTHUB_CONN_STR,
    eventhub_name=EVENTHUB_NAME
)
def send_update(update_dict,partition_key=None):

    event_data = EventData(json.dumps(update_dict))
    with producer:
        event_batch = producer.create_batch(partition_key=partition_key)
        event_batch.add(event_data)
        producer.send_batch(event_batch)
    print("Sent:", update_dict)

