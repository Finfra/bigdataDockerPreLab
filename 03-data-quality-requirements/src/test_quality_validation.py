#!/usr/bin/env python3
# 데이터 품질 검증 테스트

import json
import requests
from datetime import datetime

# 품질 검증 규칙
VALIDATION_RULES = {
    "sensor1": {"min": 0, "max": 100},
    "sensor2": {"min": 0, "max": 100}, 
    "sensor3": {"min": 0, "max": 150},
    "motor1": {"min": 0, "max": 2000},
    "motor2": {"min": 0, "max": 1500},
    "motor3": {"min": 0, "max": 1800},
    "DeviceId": {"min": 1, "max": 5}
}

def validate_data(data):
    """데이터 품질 검증"""
    issues = []
    
    # 필수 필드 체크
    required_fields = ["time", "DeviceId", "sensor1", "sensor2", "sensor3", 
                      "motor1", "motor2", "motor3", "isFail"]
    for field in required_fields:
        if field not in data or data[field] is None:
            issues.append(f"Missing field: {field}")
    
    # 범위 검증
    for field, rules in VALIDATION_RULES.items():
        if field in data and data[field] is not None:
            value = data[field]
            if value < rules["min"] or value > rules["max"]:
                issues.append(f"{field} out of range: {value} (expected {rules['min']}-{rules['max']})")
    
    return issues

def test_live_api():
    """실제 API 데이터 품질 테스트"""
    print("=== FMS API 데이터 품질 검증 테스트 ===\n")
    
    for device_id in range(1, 6):
        try:
            response = requests.get(f"http://finfra.iptime.org:9872/{device_id}/", timeout=5)
            data = response.json()
            
            print(f"Device {device_id}:")
            print(f"  Data: {json.dumps(data, indent=2)}")
            
            issues = validate_data(data)
            if issues:
                print("  Quality Issues:")
                for issue in issues:
                    print(f"    ❌ {issue}")
            else:
                print("  ✅ Data quality OK")
                
        except Exception as e:
            print(f"  ❌ API Error: {e}")
        
        print()

if __name__ == "__main__":
    test_live_api()
