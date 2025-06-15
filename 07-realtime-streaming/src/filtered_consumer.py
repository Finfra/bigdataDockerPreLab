#!/usr/bin/env python3
"""
Filtered Message Consumer
필터링된 메시지를 수신하여 처리
"""
from confluent_kafka import Consumer, KafkaError

BROKER = "s1:9092,s2:9092,s3:9092"
FILTERED_TOPIC = "filtered-topic"

def consume_filtered():
    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": "filtered-group",
        "auto.offset.reset": "earliest"
    })

    consumer.subscribe([FILTERED_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            print(f"Filtered message: {msg.value().decode('utf-8')}")
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_filtered()
