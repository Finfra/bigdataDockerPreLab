# NULL 값 처리 규칙 설정
NULL_HANDLING_RULES = {
    "time": "REJECT",           # 타임스탬프 NULL 시 데이터 거부
    "DeviceId": "REJECT",       # 장비 ID NULL 시 데이터 거부
    "sensor1": "INTERPOLATE",   # 이전 값으로 보간
    "sensor2": "INTERPOLATE",   # 이전 값으로 보간
    "sensor3": "INTERPOLATE",   # 이전 값으로 보간
    "motor1": "DEFAULT_0",      # 기본값 0으로 설정
    "motor2": "DEFAULT_0",      # 기본값 0으로 설정
    "motor3": "DEFAULT_0",      # 기본값 0으로 설정
    "isFail": "DEFAULT_FALSE"   # 기본값 false로 설정
}
