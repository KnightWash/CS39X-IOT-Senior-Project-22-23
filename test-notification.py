from google.cloud import pubsub_v1
import time

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    "knightwash-webui-angular", "machines_pubsub"
)
payloadMessage = "calvin/test/dryer/location"
data = payloadMessage.encode("utf-8")

while True:
    future = publisher.publish(topic_path, data)
    print(future.result())
    time.sleep(15)
