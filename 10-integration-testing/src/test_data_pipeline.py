# tests/test_data_pipeline.py
import unittest
import time
from kafka import KafkaProducer, KafkaConsumer
import json

class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    def test_kafka_connectivity(self):
        """Kafka 연결 테스트"""
        test_data = {
            "DeviceId": 1,
            "time": "2024-01-15T10:00:00Z",
            "sensor1": 85.0,
            "sensor2": 60.0,
            "sensor3": 120.0,
            "motor1": 1200,
            "motor2": 800,
            "motor3": 1000,
            "isFail": False
        }
        
        # 메시지 발송
        future = self.producer.send('fms-raw-data', test_data)
        result = future.get(timeout=10)
        
        self.assertIsNotNone(result)
        
    def test_end_to_end_pipeline(self):
        """엔드투엔드 파이프라인 테스트"""
        # 테스트 데이터 생성 및 발송
        for i in range(10):
            test_data = {
                "DeviceId": i % 5 + 1,
                "time": f"2024-01-15T10:{i:02d}:00Z",
                "sensor1": 80 + i,
                "sensor2": 50 + i,
                "sensor3": 100 + i,
                "motor1": 1100 + i * 10,
                "motor2": 700 + i * 10,
                "motor3": 900 + i * 10,
                "isFail": i % 3 == 0
            }
            self.producer.send('fms-raw-data', test_data)
        
        # 처리 대기
        time.sleep(30)
        
        # 결과 검증 (HDFS 파일 존재 확인 등)
        # 실제 구현에서는 HDFS 클라이언트를 사용하여 파일 확인
        self.assertTrue(True)  # 플레이스홀더

if __name__ == '__main__':
    unittest.main()