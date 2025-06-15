#!/usr/bin/env python3
"""
BigData Docker Pre-Lab Mock API Server
FMS(Facility Management System) 시뮬레이션 서버

작성일: 2025-06-14
목적: 실제 API 서버가 없을 때 테스트용 Mock 데이터 제공
"""

import json
import time
import random
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading
import signal
import sys

class FMSDataGenerator:
    """FMS 센서 데이터 생성기"""
    
    def __init__(self):
        # 각 장비별 기본 설정값
        self.device_configs = {
            1: {"base_temp": 85, "base_motor": 1200, "fail_rate": 0.05},
            2: {"base_temp": 90, "base_motor": 850, "fail_rate": 0.03},
            3: {"base_temp": 78, "base_motor": 1100, "fail_rate": 0.04},
            4: {"base_temp": 82, "base_motor": 950, "fail_rate": 0.06},
            5: {"base_temp": 88, "base_motor": 1050, "fail_rate": 0.02}
        }
        
        # 장비별 상태 저장
        self.device_states = {}
        for device_id in self.device_configs:
            self.device_states[device_id] = {
                "last_update": time.time(),
                "trend": random.choice(["stable", "increasing", "decreasing"]),
                "trend_duration": 0,
                "is_failing": False
            }
    
    def generate_sensor_data(self, device_id):
        """특정 장비의 센서 데이터 생성"""
        if device_id not in self.device_configs:
            return None
        
        config = self.device_configs[device_id]
        state = self.device_states[device_id]
        
        # 시간 경과에 따른 트렌드 변화
        current_time = time.time()
        if current_time - state["last_update"] > 30:  # 30초마다 트렌드 변경 가능
            if random.random() < 0.3:  # 30% 확률로 트렌드 변경
                state["trend"] = random.choice(["stable", "increasing", "decreasing"])
                state["trend_duration"] = 0
            state["last_update"] = current_time
        
        state["trend_duration"] += 1
        
        # 기본 값에 트렌드와 노이즈 적용
        trend_factor = 0
        if state["trend"] == "increasing":
            trend_factor = state["trend_duration"] * 0.5
        elif state["trend"] == "decreasing":
            trend_factor = -state["trend_duration"] * 0.5
        
        # 센서 데이터 생성
        base_temp = config["base_temp"]
        sensor1 = max(0, base_temp + trend_factor + random.uniform(-5, 5))
        sensor2 = max(0, base_temp + 5 + trend_factor + random.uniform(-3, 3))
        sensor3 = max(0, base_temp - 7 + trend_factor + random.uniform(-4, 4))
        
        # 모터 RPM 데이터
        base_motor = config["base_motor"]
        motor_variation = random.uniform(-50, 50)
        motor1 = max(0, base_motor + motor_variation)
        motor2 = max(0, base_motor - 200 + motor_variation)
        motor3 = max(0, base_motor - 100 + motor_variation)
        
        # 장애 상태 결정
        fail_probability = config["fail_rate"]
        if any(temp > 100 for temp in [sensor1, sensor2, sensor3]):
            fail_probability *= 3  # 고온 시 장애 확률 증가
        
        is_fail = random.random() < fail_probability
        state["is_failing"] = is_fail
        
        # JSON 데이터 구성
        data = {
            "time": datetime.now(timezone.utc).isoformat(),
            "DeviceId": device_id,
            "sensor1": round(sensor1, 2),
            "sensor2": round(sensor2, 2),
            "sensor3": round(sensor3, 2),
            "motor1": int(motor1),
            "motor2": int(motor2),
            "motor3": int(motor3),
            "isFail": is_fail
        }
        
        return data

class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API 요청 처리기"""
    
    def __init__(self, *args, data_generator=None, **kwargs):
        self.data_generator = data_generator
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET 요청 처리"""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        # 로그 출력 억제
        # print(f"GET 요청: {self.path}")
        
        # /DeviceId/ 형태의 경로 처리
        if len(path_parts) >= 1 and path_parts[0].isdigit():
            device_id = int(path_parts[0])
            
            if 1 <= device_id <= 5:
                # 센서 데이터 생성
                sensor_data = self.data_generator.generate_sensor_data(device_id)
                
                if sensor_data:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = json.dumps(sensor_data, indent=2)
                    self.wfile.write(response.encode())
                    return
        
        # 루트 경로 - 상태 정보 제공
        elif parsed_path.path == '/' or parsed_path.path == '':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            status_info = {
                "status": "running",
                "message": "FMS Mock API Server",
                "available_devices": [1, 2, 3, 4, 5],
                "endpoints": [
                    "/1/ - Device 1 센서 데이터",
                    "/2/ - Device 2 센서 데이터", 
                    "/3/ - Device 3 센서 데이터",
                    "/4/ - Device 4 센서 데이터",
                    "/5/ - Device 5 센서 데이터"
                ],
                "data_format": {
                    "time": "ISO 8601 timestamp",
                    "DeviceId": "장비 ID (1-5)",
                    "sensor1": "온도 센서 1 (°C)",
                    "sensor2": "온도 센서 2 (°C)", 
                    "sensor3": "온도 센서 3 (°C)",
                    "motor1": "모터 1 RPM",
                    "motor2": "모터 2 RPM",
                    "motor3": "모터 3 RPM",
                    "isFail": "장애 상태 (true/false)"
                }
            }
            
            response = json.dumps(status_info, indent=2, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            return
        
        # 잘못된 경로
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        error_response = {
            "error": "Not Found",
            "message": f"장비 ID는 1-5 범위여야 합니다. 요청: {self.path}",
            "available_endpoints": ["/1/", "/2/", "/3/", "/4/", "/5/"]
        }
        
        response = json.dumps(error_response, indent=2, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """로그 메시지 출력 (필요 시에만)"""
        # 일반적인 GET 요청은 로그 출력하지 않음
        pass

def create_handler(data_generator):
    """핸들러 팩토리 함수"""
    def handler(*args, **kwargs):
        return MockAPIHandler(*args, data_generator=data_generator, **kwargs)
    return handler

def signal_handler(signum, frame):
    """종료 시그널 처리"""
    print("\n서버를 종료합니다...")
    sys.exit(0)

def main():
    """메인 함수"""
    HOST = 'localhost'
    PORT = 9873
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 데이터 생성기 초기화
    data_generator = FMSDataGenerator()
    
    # HTTP 서버 생성
    handler = create_handler(data_generator)
    server = HTTPServer((HOST, PORT), handler)
    
    print(f"🚀 FMS Mock API Server 시작됨")
    print(f"📍 주소: http://{HOST}:{PORT}")
    print(f"📊 사용 가능한 장비: 1, 2, 3, 4, 5")
    print(f"🔄 데이터 갱신: 실시간 (요청시마다)")
    print(f"⏹️  종료: Ctrl+C")
    print()
    print(f"테스트 명령어:")
    print(f"  curl http://{HOST}:{PORT}/1/")
    print(f"  curl http://{HOST}:{PORT}/")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버가 종료되었습니다.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
