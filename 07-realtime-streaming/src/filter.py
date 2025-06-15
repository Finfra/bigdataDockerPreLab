#!/usr/bin/env python3
"""
Kafka Message Filter
특정 키워드가 포함된 메시지만 필터링하여 다른 토픽으로 전송
"""
from confluent_kafka import Consumer, Producer, KafkaError

BROKER = "s1:9092,s2:9092,s3:9092"
INPUT_TOPIC = "input-topic"
FILTERED_TOPIC = "filtered-topic"

def filter_messages():
    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": "filter-group",
        "auto.offset.reset": "earliest"
    })
    producer = Producer({"bootstrap.servers": BROKER})

    consumer.subscribe([INPUT_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)  # 1초 동안 메시지 기다림
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            value = msg.value().decode("utf-8")
            print(f"Received: {value}")

            # 필터 조건: "filter" 포함 여부
            if "filter" in value:
                producer.produce(FILTERED_TOPIC, value)
                print(f"Filtered and sent to {FILTERED_TOPIC}: {value}")
                producer.flush()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()

if __name__ == "__main__":
    filter_messages()
