#!/usr/bin/env python3
"""
FMS Data Transformation Test
Spark을 사용한 데이터 변환 테스트
"""

# Mock 데이터를 사용한 변환 로직 테스트
import json
from datetime import datetime
import random

class MockFMSDataTransformer:
    def __init__(self):
        self.quality_rules = {
            "sensor1": {"min": 0, "max": 100},
            "sensor2": {"min": 0, "max": 100}, 
            "sensor3": {"min": 0, "max": 150},
            "motor1": {"min": 0, "max": 2000},
            "motor2": {"min": 0, "max": 1500},
            "motor3": {"min": 0, "max": 1800},
        }

    def basic_data_cleaning(self, data):
        """기본 데이터 정제"""
        cleaned = {}
        
        # 필수 필드 체크
        if not all(k in data for k in ["DeviceId", "time"]):
            return None
        
        cleaned["DeviceId"] = data["DeviceId"]
        cleaned["time"] = data["time"]
        cleaned["isFail"] = data.get("isFail", False)
        
        # 센서 범위 검증 및 정제
        for sensor in ["sensor1", "sensor2", "sensor3"]:
            value = data.get(sensor)
            if value is not None:
                rules = self.quality_rules[sensor]
                if rules["min"] <= value <= rules["max"]:
                    cleaned[f"{sensor}_clean"] = value
                else:
                    cleaned[f"{sensor}_clean"] = None
                    cleaned[f"{sensor}_outlier"] = True
        
        # 모터 RPM 검증 및 정제
        for motor in ["motor1", "motor2", "motor3"]:
            value = data.get(motor)
            if value is not None:
                rules = self.quality_rules[motor]
                if rules["min"] <= value <= rules["max"]:
                    cleaned[f"{motor}_clean"] = value
                else:
                    cleaned[f"{motor}_clean"] = None
                    cleaned[f"{motor}_outlier"] = True
        
        return cleaned

    def classify_sensor_status(self, sensor1, sensor2, sensor3):
        """센서 상태 분류 UDF"""
        if any(v is None for v in [sensor1, sensor2, sensor3]):
            return "DATA_MISSING"
        
        # 임계값 정의
        temp_critical = 90.0
        humidity_critical = 85.0  
        pressure_critical = 130.0
        
        critical_count = 0
        warning_count = 0
        
        if sensor1 > temp_critical:
            critical_count += 1
        elif sensor1 > temp_critical * 0.9:
            warning_count += 1
            
        if sensor2 > humidity_critical:
            critical_count += 1
        elif sensor2 > humidity_critical * 0.9:
            warning_count += 1
            
        if sensor3 > pressure_critical:
            critical_count += 1
        elif sensor3 > pressure_critical * 0.9:
            warning_count += 1
        
        if critical_count >= 2:
            return "CRITICAL"
        elif critical_count >= 1:
            return "HIGH_WARNING"
        elif warning_count >= 2:
            return "WARNING"
        else:
            return "NORMAL"

    def calculate_motor_efficiency(self, motor1, motor2, motor3, sensor1, sensor2):
        """모터 효율성 계산 UDF"""
        if any(v is None for v in [motor1, motor2, motor3, sensor1, sensor2]):
            return 0.0
        
        try:
            # 기준 RPM 대비 효율성
            motor1_eff = motor1 / 2000.0 if motor1 <= 2000 else 2000.0 / motor1
            motor2_eff = motor2 / 1500.0 if motor2 <= 1500 else 1500.0 / motor2  
            motor3_eff = motor3 / 1800.0 if motor3 <= 1800 else 1800.0 / motor3
            
            # 환경 보정
            temp_factor = max(0.5, 1.0 - (sensor1 - 70) / 100) if sensor1 > 70 else 1.0
            humidity_factor = max(0.7, 1.0 - (sensor2 - 60) / 100) if sensor2 > 60 else 1.0
            
            base_efficiency = (motor1_eff + motor2_eff + motor3_eff) / 3.0
            adjusted_efficiency = base_efficiency * temp_factor * humidity_factor
            
            return min(1.0, max(0.0, adjusted_efficiency))
            
        except (ZeroDivisionError, TypeError):
            return 0.0

    def validate_data_quality(self, data):
        """데이터 품질 검증"""
        quality_score = 0.0
        total_checks = 0
        issues = []
        
        # 완전성 검증
        required_fields = ["DeviceId", "time", "sensor1", "sensor2", "sensor3", "motor1", "motor2", "motor3", "isFail"]
        for field in required_fields:
            total_checks += 1
            if field in data and data[field] is not None:
                quality_score += 1
            else:
                issues.append(f"missing_{field}")
        
        # 유효성 검증
        for field, rules in self.quality_rules.items():
            if field in data and data[field] is not None:
                total_checks += 1
                value = data[field]
                if rules["min"] <= value <= rules["max"]:
                    quality_score += 1
                else:
                    issues.append(f"invalid_{field}_range")
        
        final_score = quality_score / total_checks if total_checks > 0 else 0
        
        return {
            "quality_score": final_score,
            "total_checks": total_checks,
            "passed_checks": quality_score,
            "issues": issues,
            "grade": "EXCELLENT" if final_score >= 0.95 else 
                    "GOOD" if final_score >= 0.85 else 
                    "FAIR" if final_score >= 0.7 else "POOR"
        }

    def transform_record(self, raw_data):
        """전체 변환 파이프라인"""
        # 1. 기본 정제
        cleaned = self.basic_data_cleaning(raw_data)
        if not cleaned:
            return None
        
        # 2. UDF 적용
        sensor_status = self.classify_sensor_status(
            cleaned.get("sensor1_clean"),
            cleaned.get("sensor2_clean"), 
            cleaned.get("sensor3_clean")
        )
        
        motor_efficiency = self.calculate_motor_efficiency(
            cleaned.get("motor1_clean"),
            cleaned.get("motor2_clean"),
            cleaned.get("motor3_clean"),
            cleaned.get("sensor1_clean"),
            cleaned.get("sensor2_clean")
        )
        
        # 3. 품질 검증
        quality_result = self.validate_data_quality(raw_data)
        
        # 4. 결과 조합
        result = {
            **cleaned,
            "sensor_status": sensor_status,
            "motor_efficiency": round(motor_efficiency, 4),
            "quality_score": round(quality_result["quality_score"], 4),
            "quality_grade": quality_result["grade"],
            "quality_issues": quality_result["issues"],
            "processed_at": datetime.now().isoformat()
        }
        
        return result

# 테스트 실행
if __name__ == "__main__":
    transformer = MockFMSDataTransformer()
    
    # 테스트 데이터 생성
    test_data = [
        # 정상 데이터
        {
            "time": "2025-06-14 19:45:00",
            "DeviceId": 1,
            "sensor1": 45.5,
            "sensor2": 62.3,
            "sensor3": 78.9,
            "motor1": 1200,
            "motor2": 850,
            "motor3": 1100,
            "isFail": False
        },
        # 경고 데이터
        {
            "time": "2025-06-14 19:45:10",
            "DeviceId": 2,
            "sensor1": 85.2,  # 높은 온도
            "sensor2": 82.7,  # 높은 습도
            "sensor3": 95.5,
            "motor1": 1850,   # 높은 RPM
            "motor2": 950,
            "motor3": 1200,
            "isFail": False
        },
        # 심각한 데이터
        {
            "time": "2025-06-14 19:45:20", 
            "DeviceId": 3,
            "sensor1": 95.8,  # 임계치 초과
            "sensor2": 92.1,  # 임계치 초과
            "sensor3": 140.2, # 높은 압력
            "motor1": 1950,
            "motor2": 1200,
            "motor3": 1650,
            "isFail": True
        }
    ]
    
    print("=== FMS Data Transformation Test ===\n")
    
    for i, data in enumerate(test_data, 1):
        print(f"Test Case {i}: Device {data['DeviceId']}")
        print(f"Input: sensor1={data['sensor1']}, sensor2={data['sensor2']}, sensor3={data['sensor3']}")
        
        result = transformer.transform_record(data)
        
        if result:
            print(f"Output:")
            print(f"  Sensor Status: {result['sensor_status']}")
            print(f"  Motor Efficiency: {result['motor_efficiency']}")
            print(f"  Quality Score: {result['quality_score']} ({result['quality_grade']})")
            if result['quality_issues']:
                print(f"  Issues: {', '.join(result['quality_issues'])}")
            print()
        else:
            print("  Failed to process (invalid data)")
            print()
    
    print("Transformation test completed!")
