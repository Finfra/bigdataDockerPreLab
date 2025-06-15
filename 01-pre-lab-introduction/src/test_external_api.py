#!/usr/bin/env python3
"""
BigData Docker Pre-Lab 외부 API 테스트 스크립트

작성일: 2025-06-14
목적: 외부 FMS API 서버 연결 상태 및 데이터 형식 검증
"""

import json
import requests
import time
from datetime import datetime

def test_external_api():
    """외부 API 테스트"""
    base_url = "http://finfra.iptime.org:9872"
    
    print("🧪 외부 FMS API 연결 테스트 시작")
    print("=" * 60)
    print(f"📍 테스트 대상: {base_url}")
    print()
    
    # 각 장비별 테스트
    device_results = {}
    
    for device_id in range(1, 6):
        print(f"🔍 장비 {device_id} 테스트 중...")
        
        try:
            response = requests.get(f"{base_url}/{device_id}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 필수 필드 확인
                required_fields = ["time", "DeviceId", "sensor1", "sensor2", "sensor3", 
                                 "motor1", "motor2", "motor3", "isFail"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ 장비 {device_id}: 필수 필드 누락 - {missing_fields}")
                    device_results[device_id] = "FAIL"
                else:
                    print(f"✅ 장비 {device_id}: 정상 (isFail: {data['isFail']}, 온도: {data['sensor1']:.1f}°C)")
                    device_results[device_id] = "PASS"
                    
                    # 첫 번째 장비 데이터 샘플 출력
                    if device_id == 1:
                        print(f"   📄 데이터 샘플:")
                        for key, value in data.items():
                            print(f"      {key}: {value}")
                        print()
            else:
                print(f"❌ 장비 {device_id}: HTTP {response.status_code} 오류")
                device_results[device_id] = "FAIL"
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 장비 {device_id}: 연결 오류")
            device_results[device_id] = "FAIL"
        except requests.exceptions.Timeout:
            print(f"❌ 장비 {device_id}: 응답 시간 초과")
            device_results[device_id] = "FAIL"
        except Exception as e:
            print(f"❌ 장비 {device_id}: 오류 - {str(e)}")
            device_results[device_id] = "FAIL"
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    
    passed_count = len([r for r in device_results.values() if r == "PASS"])
    failed_count = len([r for r in device_results.values() if r == "FAIL"])
    
    print(f"✅ 성공: {passed_count}/5 장비")
    print(f"❌ 실패: {failed_count}/5 장비")
    
    if failed_count == 0:
        print("\n🎉 모든 외부 API 테스트가 성공했습니다!")
        print("💡 이제 다음 단계로 진행할 수 있습니다.")
        return True
    else:
        print(f"\n⚠️ {failed_count}개 장비에서 문제가 발생했습니다.")
        return False

if __name__ == "__main__":
    success = test_external_api()
    exit(0 if success else 1)
