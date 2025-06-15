# 데이터 품질 메트릭 정의
QUALITY_METRICS = {
    "completeness": {
        "target": 0.99,  # 99% 완전성
        "measurement": "non_null_ratio"
    },
    "accuracy": {
        "target": 0.95,  # 95% 정확성
        "measurement": "valid_range_ratio"
    },
    "timeliness": {
        "target": 30,    # 30초 이내 처리
        "measurement": "processing_latency"
    },
    "consistency": {
        "target": 0.98,  # 98% 일관성
        "measurement": "duplicate_ratio"
    }
}
