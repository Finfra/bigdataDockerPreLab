#!/usr/bin/env python3
"""
FMS Consumer for Real Data Processing
실제 FMS 센서 데이터를 수신하여 처리
"""
import json
from confluent_kafka import Consumer, KafkaError
import logging
from datetime import datetime

# Kafka 설정
BROKER = "s1:9092,s2:9092,s3:9092"
TOPIC = "fms-sensor-data"
GROUP_ID = "fms-data-processor"

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FMSDataConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': BROKER,
            'group.id': GROUP_ID,
            'auto.offset.reset': 'earliest'
        })
        
    def analyze_sensor_data(self, data):
        """센서 데이터 분석"""
        device_id = data['DeviceId']
        
        # 센서 값 분석
        sensor_avg = (data['sensor1'] + data['sensor2'] + data['sensor3']) / 3
        motor_total = data['motor1'] + data['motor2'] + data['motor3']
        
        # 이상 상태 탐지
        alerts = []
        
        # 센서 임계값 검사
        if data['sensor1'] > 90 or data['sensor2'] > 90 or data['sensor3'] > 90:
            alerts.append("HIGH_SENSOR_VALUE")
            
        # 모터 이상 검사
        if data['motor1'] > 1500 or data['motor2'] > 1500 or data['motor3'] > 1500:
            alerts.append("HIGH_MOTOR_VALUE")
            
        # 장비 실패 상태
        if data['isFail']:
            alerts.append("DEVICE_FAILURE")
        
        analysis_result = {
            'device_id': device_id,
            'timestamp': data['time'],
            'processed_at': datetime.now().isoformat(),
            'sensor_average': round(sensor_avg, 2),
            'motor_total': motor_total,
            'alerts': alerts,
            'status': 'CRITICAL' if alerts else 'NORMAL'
        }
        
        return analysis_result
    
    def process_message(self, msg):
        """메시지 처리"""
        try:
            # JSON 파싱
            data = json.loads(msg.value().decode('utf-8'))
            
            # 데이터 분석
            result = self.analyze_sensor_data(data)
            
            # 결과 출력
            device_id = result['device_id']
            status = result['status']
            
            if status == 'CRITICAL':
                logger.warning(f"🚨 Device {device_id}: {status} - Alerts: {result['alerts']}")
            else:
                logger.info(f"✅ Device {device_id}: {status} - Avg: {result['sensor_average']}")
            
            # 상세 정보 출력 (선택적)
            if result['alerts']:
                print(f"  └─ 센서 평균: {result['sensor_average']}")
                print(f"  └─ 모터 합계: {result['motor_total']}")
                print(f"  └─ 알림: {', '.join(result['alerts'])}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            return None
    
    def run(self):
        """Consumer 실행"""
        logger.info("FMS Data Consumer 시작...")
        logger.info(f"구독 토픽: {TOPIC}")
        
        self.consumer.subscribe([TOPIC])
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        break
                
                # 메시지 처리
                self.process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        finally:
            self.consumer.close()
            logger.info("Consumer 종료")

if __name__ == "__main__":
    consumer = FMSDataConsumer()
    consumer.run()
