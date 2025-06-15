#!/usr/bin/env python3
"""
FMS 통합 데이터 파이프라인 테스트
Kafka → Transformation → Storage 전체 플로우
"""

import json
import time
import os
from datetime import datetime
from kafka import KafkaConsumer
import logging

class FMSIntegratedPipeline:
    def __init__(self):
        self.setup_logging()
        self.data_dir = "/tmp/fms_data"
        self.setup_directories()
        
        # 처리 통계
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": time.time()
        }

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('FMS-Pipeline')

    def setup_directories(self):
        """저장 디렉터리 설정"""
        os.makedirs(f"{self.data_dir}/raw", exist_ok=True)
        os.makedirs(f"{self.data_dir}/processed", exist_ok=True)
        os.makedirs(f"{self.data_dir}/alerts", exist_ok=True)
        os.makedirs(f"{self.data_dir}/quality", exist_ok=True)

    def classify_sensor_status(self, sensor1, sensor2, sensor3):
        """센서 상태 분류"""
        if any(v is None for v in [sensor1, sensor2, sensor3]):
            return "DATA_MISSING"
        
        critical_count = 0
        warning_count = 0
        
        # 임계값 체크
        if sensor1 > 90: critical_count += 1
        elif sensor1 > 81: warning_count += 1
            
        if sensor2 > 85: critical_count += 1
        elif sensor2 > 76: warning_count += 1
            
        if sensor3 > 130: critical_count += 1
        elif sensor3 > 117: warning_count += 1
        
        if critical_count >= 2:
            return "CRITICAL"
        elif critical_count >= 1:
            return "HIGH_WARNING"
        elif warning_count >= 2:
            return "WARNING"
        else:
            return "NORMAL"

    def calculate_motor_efficiency(self, motor1, motor2, motor3, sensor1, sensor2):
        """모터 효율성 계산"""
        if any(v is None for v in [motor1, motor2, motor3, sensor1, sensor2]):
            return 0.0
        
        try:
            motor1_eff = motor1 / 2000.0 if motor1 <= 2000 else 2000.0 / motor1
            motor2_eff = motor2 / 1500.0 if motor2 <= 1500 else 1500.0 / motor2  
            motor3_eff = motor3 / 1800.0 if motor3 <= 1800 else 1800.0 / motor3
            
            temp_factor = max(0.5, 1.0 - (sensor1 - 70) / 100) if sensor1 > 70 else 1.0
            humidity_factor = max(0.7, 1.0 - (sensor2 - 60) / 100) if sensor2 > 60 else 1.0
            
            base_efficiency = (motor1_eff + motor2_eff + motor3_eff) / 3.0
            adjusted_efficiency = base_efficiency * temp_factor * humidity_factor
            
            return min(1.0, max(0.0, adjusted_efficiency))
        except:
            return 0.0

    def transform_data(self, raw_data):
        """데이터 변환"""
        try:
            # 기본 검증
            if not all(k in raw_data for k in ["DeviceId", "time"]):
                return None
            
            # 변환 실행
            transformed = {
                "DeviceId": raw_data["DeviceId"],
                "timestamp": raw_data["time"],
                "sensor1": raw_data.get("sensor1"),
                "sensor2": raw_data.get("sensor2"),
                "sensor3": raw_data.get("sensor3"),
                "motor1": raw_data.get("motor1"),
                "motor2": raw_data.get("motor2"),
                "motor3": raw_data.get("motor3"),
                "isFail": raw_data.get("isFail", False),
                "processed_at": datetime.now().isoformat()
            }
            
            # UDF 적용
            transformed["sensor_status"] = self.classify_sensor_status(
                transformed["sensor1"], transformed["sensor2"], transformed["sensor3"]
            )
            
            transformed["motor_efficiency"] = self.calculate_motor_efficiency(
                transformed["motor1"], transformed["motor2"], transformed["motor3"],
                transformed["sensor1"], transformed["sensor2"]
            )
            
            # 품질 점수 계산
            valid_fields = sum(1 for v in [transformed["sensor1"], transformed["sensor2"], 
                                         transformed["sensor3"], transformed["motor1"],
                                         transformed["motor2"], transformed["motor3"]] if v is not None)
            transformed["quality_score"] = valid_fields / 6.0
            
            return transformed
            
        except Exception as e:
            self.logger.error(f"Transformation error: {str(e)}")
            return None

    def save_data(self, data, data_type="processed"):
        """데이터 저장"""
        try:
            device_id = data["DeviceId"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 파일 경로 생성
            filename = f"{self.data_dir}/{data_type}/device_{device_id}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Storage error: {str(e)}")
            return False

    def handle_alert(self, data):
        """알림 처리"""
        if data["sensor_status"] in ["CRITICAL", "HIGH_WARNING"] or data["isFail"]:
            alert = {
                "alert_time": datetime.now().isoformat(),
                "device_id": data["DeviceId"],
                "severity": data["sensor_status"],
                "sensor_status": data["sensor_status"],
                "motor_efficiency": data["motor_efficiency"],
                "is_fail": data["isFail"],
                "sensors": {
                    "sensor1": data["sensor1"],
                    "sensor2": data["sensor2"],
                    "sensor3": data["sensor3"]
                }
            }
            
            self.save_data(alert, "alerts")
            self.logger.warning(f"ALERT: Device {data['DeviceId']} - {data['sensor_status']}")
            return True
        return False

    def process_message(self, raw_data):
        """메시지 처리 파이프라인"""
        try:
            self.stats["total_processed"] += 1
            
            # 1. 원시 데이터 저장
            self.save_data(raw_data, "raw")
            
            # 2. 데이터 변환
            transformed = self.transform_data(raw_data)
            if not transformed:
                self.stats["failed"] += 1
                return False
            
            # 3. 변환된 데이터 저장
            self.save_data(transformed, "processed")
            
            # 4. 알림 처리
            self.handle_alert(transformed)
            
            # 5. 품질 메트릭 저장
            quality_metric = {
                "timestamp": datetime.now().isoformat(),
                "device_id": transformed["DeviceId"],
                "quality_score": transformed["quality_score"],
                "sensor_status": transformed["sensor_status"],
                "motor_efficiency": transformed["motor_efficiency"]
            }
            self.save_data(quality_metric, "quality")
            
            self.stats["successful"] += 1
            
            self.logger.info(f"Processed Device {transformed['DeviceId']}: "
                           f"{transformed['sensor_status']}, "
                           f"Efficiency: {transformed['motor_efficiency']:.3f}, "
                           f"Quality: {transformed['quality_score']:.3f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {str(e)}")
            self.stats["failed"] += 1
            return False

    def run_kafka_pipeline(self, max_messages=20):
        """Kafka 기반 실시간 파이프라인 실행"""
        self.logger.info("Starting FMS Integrated Pipeline...")
        self.logger.info(f"Data will be saved to: {self.data_dir}")
        
        try:
            consumer = KafkaConsumer(
                'fms-raw-data',
                bootstrap_servers=['localhost:9092'],
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='integrated-pipeline-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            self.logger.info("Connected to Kafka. Processing messages...")
            
            message_count = 0
            for message in consumer:
                raw_data = message.value
                
                # 메시지 처리
                success = self.process_message(raw_data)
                message_count += 1
                
                if message_count >= max_messages:
                    break
                    
                time.sleep(0.1)  # 간격 조절
                
        except Exception as e:
            self.logger.error(f"Kafka pipeline error: {str(e)}")
        finally:
            self.print_summary()

    def print_summary(self):
        """처리 결과 요약"""
        elapsed = time.time() - self.stats["start_time"]
        success_rate = (self.stats["successful"] / self.stats["total_processed"] * 100) if self.stats["total_processed"] > 0 else 0
        
        self.logger.info("=" * 50)
        self.logger.info("PIPELINE SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total Processed: {self.stats['total_processed']}")
        self.logger.info(f"Successful: {self.stats['successful']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Processing Time: {elapsed:.1f} seconds")
        self.logger.info(f"Throughput: {self.stats['total_processed']/elapsed:.1f} msg/sec")
        self.logger.info(f"Data Location: {self.data_dir}")

    def run_mock_pipeline(self):
        """Mock 데이터 기반 파이프라인 테스트"""
        self.logger.info("Running Mock Data Pipeline Test...")
        
        # Mock 데이터 생성
        mock_data = [
            {
                "time": "2025-06-14T20:00:00Z",
                "DeviceId": 1,
                "sensor1": 45.5, "sensor2": 62.3, "sensor3": 78.9,
                "motor1": 1200, "motor2": 850, "motor3": 1100,
                "isFail": False
            },
            {
                "time": "2025-06-14T20:00:10Z", 
                "DeviceId": 2,
                "sensor1": 95.8, "sensor2": 92.1, "sensor3": 140.2,  # 임계치 초과
                "motor1": 1950, "motor2": 1200, "motor3": 1650,
                "isFail": True
            }
        ]
        
        for data in mock_data:
            self.process_message(data)
            time.sleep(1)
        
        self.print_summary()

if __name__ == "__main__":
    import sys
    
    pipeline = FMSIntegratedPipeline()
    
    if len(sys.argv) > 1 and sys.argv[1] == "mock":
        pipeline.run_mock_pipeline()
    else:
        pipeline.run_kafka_pipeline(max_messages=10)
