#!/usr/bin/env python3
"""
Kafka에서 실제 FMS 데이터를 읽어와서 변환 테스트
"""

import json
from kafka import KafkaConsumer
import sys
import signal

# 앞서 만든 변환기 import
sys.path.append('.')
from test_transformations import MockFMSDataTransformer

def signal_handler(sig, frame):
    print('\nStopping consumer...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('=== Real-time FMS Data Transformation Test ===')
print('Reading from Kafka topic: fms-raw-data')

transformer = MockFMSDataTransformer()

try:
    consumer = KafkaConsumer(
        'fms-raw-data',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='transformation-test-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    print('Connected to Kafka. Processing messages...\n')
    
    message_count = 0
    for message in consumer:
        raw_data = message.value
        message_count += 1
        
        print(f"Message {message_count} (Device {raw_data['DeviceId']}):")
        print(f"  Raw: sensor1={raw_data['sensor1']:.1f}, motor1={raw_data['motor1']}, isFail={raw_data['isFail']}")
        
        # 변환 실행
        transformed = transformer.transform_record(raw_data)
        
        if transformed:
            print(f"  Transformed:")
            print(f"    Sensor Status: {transformed['sensor_status']}")
            print(f"    Motor Efficiency: {transformed['motor_efficiency']:.3f}")
            print(f"    Quality Grade: {transformed['quality_grade']} ({transformed['quality_score']:.3f})")
            if transformed['quality_issues']:
                print(f"    Issues: {', '.join(transformed['quality_issues'])}")
        else:
            print("  Transformation failed!")
        
        print("---")
        
        if message_count >= 10:  # 10개 메시지만 처리
            break

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    print(f"\nProcessed {message_count} messages from real-time stream")
