#!/usr/bin/env python3
"""
Kafka Producer Example
간단한 메시지 생성 및 전송
"""
from confluent_kafka import Producer

BROKER = "s1:9092,s2:9092,s3:9092"
INPUT_TOPIC = "input-topic"

def produce_messages():
    producer = Producer({"bootstrap.servers": BROKER})

    messages = [
        "This is a filter test.",
        "Another message without the keyword.",
        "filter message example.",
        "Normal message here.",
        "This contains filter keyword."
    ]

    for msg in messages:
        producer.produce(INPUT_TOPIC, msg)
        print(f"Produced: {msg}")
    producer.flush()

if __name__ == "__main__":
    produce_messages()
