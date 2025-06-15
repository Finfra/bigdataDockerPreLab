# 데이터 타입 검증 및 변환 규칙
TYPE_VALIDATION_RULES = {
    "time": {
        "target_type": "timestamp",
        "format": "ISO8601",
        "error_action": "REJECT"
    },
    "DeviceId": {
        "target_type": "int",
        "range": [1, 5],
        "error_action": "REJECT"
    },
    "sensor1-3": {
        "target_type": "float",
        "precision": 2,
        "error_action": "CONVERT_OR_REJECT"
    },
    "motor1-3": {
        "target_type": "int",
        "error_action": "CONVERT_OR_REJECT"
    },
    "isFail": {
        "target_type": "boolean",
        "error_action": "CONVERT_OR_DEFAULT"
    }
}
