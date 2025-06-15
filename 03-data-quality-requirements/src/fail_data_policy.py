# 실패 데이터 처리 정책
FAIL_DATA_POLICY = {
    "normal_data": {
        "storage": "HDFS_MAIN",
        "retention": "365_DAYS",
        "partition": "device_id/year/month/day"
    },
    "fail_data": {
        "storage": "HDFS_ALERT",
        "retention": "1095_DAYS",  # 3년 보관
        "partition": "device_id/year/month/day",
        "alert_trigger": True,
        "priority": "HIGH"
    },
    "invalid_data": {
        "storage": "HDFS_QUARANTINE",
        "retention": "30_DAYS",
        "review_required": True
    }
}
