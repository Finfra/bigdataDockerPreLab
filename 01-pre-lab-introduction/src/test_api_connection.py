#!/usr/bin/env python3
"""
BigData Docker Pre-Lab API 연결 테스트 스크립트

작성일: 2025-06-14
목적: FMS API 서버 연결 상태 및 데이터 형식 검증
"""

import json
import requests
import time
import sys
from datetime import datetime

class APITester:
    """API 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:9872"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
    
    def log_test(self, test_name, status, message, data=None):
        """테스트 결과 로깅"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        # 콘솔 출력
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status} - {message}")
        
        if data and status == "PASS":
            print(f"   📄 데이터 샘플: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
    
    def test_server_status(self):
        """서버 상태 테스트"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "서버 상태", 
                    "PASS", 
                    f"서버가 정상적으로 응답함 (응답시간: {response.elapsed.total_seconds():.2f}초)",
                    data
                )
                return True
            else:
                self.log_test(
                    "서버 상태", 
                    "FAIL", 
                    f"서버 응답 오류 (HTTP {response.status_code})"
                )
                return False
        except requests.exceptions.ConnectionError:
            self.log_test(
                "서버 상태", 
                "FAIL", 
                "서버에 연결할 수 없음 (Connection Error)"
            )
            return False
        except requests.exceptions.Timeout:
            self.log_test(
                "서버 상태", 
                "FAIL", 
                "서버 응답 시간 초과 (Timeout)"
            )
            return False
        except Exception as e:
            self.log_test(
                "서버 상태", 
                "FAIL", 
                f"예상치 못한 오류: {str(e)}"
            )
            return False
    
    def test_device_endpoint(self, device_id):
        """개별 장비 엔드포인트 테스트"""
        try:
            response = requests.get(f"{self.base_url}/{device_id}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # 데이터 형식 검증
                required_fields = ["time", "DeviceId", "sensor1", "sensor2", "sensor3", 
                                 "motor1", "motor2", "motor3", "isFail"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        f"장비 {device_id} 데이터", 
                        "FAIL", 
                        f"필수 필드 누락: {missing_fields}"
                    )
                    return False
                
                # 데이터 타입 검증
                type_errors = []
                if not isinstance(data["DeviceId"], int):
                    type_errors.append("DeviceId는 정수여야 함")
                if not isinstance(data["isFail"], bool):
                    type_errors.append("isFail은 불린값이어야 함")
                
                for sensor in ["sensor1", "sensor2", "sensor3"]:
                    if not isinstance(data[sensor], (int, float)):
                        type_errors.append(f"{sensor}는 숫자여야 함")
                
                for motor in ["motor1", "motor2", "motor3"]:
                    if not isinstance(data[motor], int):
                        type_errors.append(f"{motor}는 정수여야 함")
                
                if type_errors:
                    self.log_test(
                        f"장비 {device_id} 데이터", 
                        "FAIL", 
                        f"데이터 타입 오류: {'; '.join(type_errors)}"
                    )
                    return False
                
                self.log_test(
                    f"장비 {device_id} 데이터", 
                    "PASS", 
                    f"정상적인 데이터 수신 (DeviceId: {data['DeviceId']}, isFail: {data['isFail']})",
                    data
                )
                return True
            else:
                self.log_test(
                    f"장비 {device_id} 데이터", 
                    "FAIL", 
                    f"HTTP {response.status_code} 오류"
                )
                return False
        except Exception as e:
            self.log_test(
                f"장비 {device_id} 데이터", 
                "FAIL", 
                f"오류: {str(e)}"
            )
            return False
    
    def test_data_consistency(self):
        """데이터 일관성 테스트 (연속 2회 요청)"""
        device_id = 1
        try:
            # 첫 번째 요청
            response1 = requests.get(f"{self.base_url}/{device_id}/", timeout=5)
            time.sleep(1)  # 1초 대기
            # 두 번째 요청
            response2 = requests.get(f"{self.base_url}/{device_id}/", timeout=5)
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                # 시간이 다른지 확인 (실시간 데이터인지)
                if data1["time"] != data2["time"]:
                    self.log_test(
                        "데이터 일관성", 
                        "PASS", 
                        "실시간 데이터 생성 확인 (시간 값이 서로 다름)"
                    )
                else:
                    self.log_test(
                        "데이터 일관성", 
                        "WARN", 
                        "동일한 시간 값 (캐시된 데이터일 가능성)"
                    )
                
                # DeviceId가 일치하는지 확인
                if data1["DeviceId"] == data2["DeviceId"] == device_id:
                    self.log_test(
                        "DeviceId 일관성", 
                        "PASS", 
                        f"DeviceId가 요청값과 일치 ({device_id})"
                    )
                else:
                    self.log_test(
                        "DeviceId 일관성", 
                        "FAIL", 
                        f"DeviceId 불일치 (요청: {device_id}, 응답1: {data1['DeviceId']}, 응답2: {data2['DeviceId']})"
                    )
                
                return True
            else:
                self.log_test(
                    "데이터 일관성", 
                    "FAIL", 
                    "HTTP 응답 오류"
                )
                return False
        except Exception as e:
            self.log_test(
                "데이터 일관성", 
                "FAIL", 
                f"오류: {str(e)}"
            )
            return False
    
    def test_invalid_endpoints(self):
        """잘못된 엔드포인트 테스트"""
        invalid_cases = [
            ("/0/", "장비 ID 0 (범위 밖)"),
            ("/6/", "장비 ID 6 (범위 밖)"),
            ("/abc/", "잘못된 형식"),
            ("/999/", "존재하지 않는 장비")
        ]
        
        for endpoint, description in invalid_cases:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 404:
                    self.log_test(
                        f"잘못된 요청 처리 ({description})", 
                        "PASS", 
                        "404 오류 정상 반환"
                    )
                else:
                    self.log_test(
                        f"잘못된 요청 처리 ({description})", 
                        "FAIL", 
                        f"예상과 다른 응답 코드: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"잘못된 요청 처리 ({description})", 
                    "FAIL", 
                    f"오류: {str(e)}"
                )
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 FMS API 연결 테스트 시작")
        print("=" * 60)
        
        # 1. 서버 상태 테스트
        if not self.test_server_status():
            print("\n❌ 서버에 연결할 수 없어 테스트를 중단합니다.")
            print("💡 해결 방법:")
            print("   1. Mock 서버가 실행 중인지 확인: python3 simple_mock_server.py")
            print("   2. 포트 9872가 사용 중인지 확인: lsof -i :9872")
            print("   3. 방화벽 설정 확인")
            return False
        
        print()
        
        # 2. 개별 장비 엔드포인트 테스트
        device_tests_passed = 0
        for device_id in range(1, 6):
            if self.test_device_endpoint(device_id):
                device_tests_passed += 1
        
        print()
        
        # 3. 데이터 일관성 테스트
        self.test_data_consistency()
        
        print()
        
        # 4. 잘못된 엔드포인트 테스트
        self.test_invalid_endpoints()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"전체 테스트: {total_tests}개")
        print(f"✅ 통과: {passed_tests}개")
        print(f"❌ 실패: {failed_tests}개")
        print(f"⚠️ 경고: {warned_tests}개")
        
        if failed_tests == 0:
            print("\n🎉 모든 테스트가 성공했습니다! API 서버가 정상적으로 작동합니다.")
            return True
        else:
            print(f"\n⚠️ {failed_tests}개의 테스트가 실패했습니다. 문제를 확인해주세요.")
            return False
    
    def save_results(self, filename="api_test_results.json"):
        """테스트 결과를 JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_summary": {
                        "timestamp": datetime.now().isoformat(),
                        "base_url": self.base_url,
                        "total_tests": len(self.test_results),
                        "passed": len([r for r in self.test_results if r["status"] == "PASS"]),
                        "failed": len([r for r in self.test_results if r["status"] == "FAIL"]),
                        "warned": len([r for r in self.test_results if r["status"] == "WARN"])
                    },
                    "test_details": self.test_results
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"\n❌ 테스트 결과 저장 실패: {str(e)}")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FMS API 연결 테스트')
    parser.add_argument('--url', default='http://localhost:9872', 
                       help='API 서버 URL (기본값: http://localhost:9872)')
    parser.add_argument('--save', action='store_true', 
                       help='테스트 결과를 JSON 파일로 저장')
    
    args = parser.parse_args()
    
    # 테스트 실행
    tester = APITester(args.url)
    success = tester.run_all_tests()
    
    # 결과 저장
    if args.save:
        tester.save_results()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
