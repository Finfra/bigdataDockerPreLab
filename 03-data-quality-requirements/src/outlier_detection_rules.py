# 이상치 탐지 규칙 설정
OUTLIER_DETECTION_RULES = {
    "method": "IQR",  # Interquartile Range 방법
    "window_size": 100,  # 최근 100개 데이터 기준
    "threshold": 1.5,    # IQR * 1.5 임계값
    "sensor_specific": {
        "sensor1": {"min": 0, "max": 100, "z_score": 3},
        "sensor2": {"min": 0, "max": 100, "z_score": 3},
        "sensor3": {"min": 0, "max": 150, "z_score": 3},
        "motor1": {"min": 0, "max": 2000, "z_score": 2.5},
        "motor2": {"min": 0, "max": 1500, "z_score": 2.5},
        "motor3": {"min": 0, "max": 1800, "z_score": 2.5}
    }
}

# 이상치 처리 방법
OUTLIER_ACTIONS = {
    "CLIP": "최대/최소값으로 제한",
    "INTERPOLATE": "이전 정상값으로 보간",
    "FLAG": "이상치 플래그 추가 후 저장",
    "REJECT": "데이터 거부"
}
