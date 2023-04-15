from google.cloud import pubsub_v1
import time

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    "knightwash-webui-angular", "calvin-test-dryer-location"
)
payloadMessage = "Off"
data = payloadMessage.encode("utf-8")

while True:
    future = publisher.publish(topic_path, data)
    print(future.result())
    time.sleep(15)
