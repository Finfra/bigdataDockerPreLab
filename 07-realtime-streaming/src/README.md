# Kafka 스트리밍 소스 코드

이 폴더에는 Kafka 클러스터 관리 및 메시지 처리를 위한 소스 코드들이 포함되어 있음.

## Python 클라이언트
* **producer.py**: 기본 메시지 생성 및 Kafka 전송
* **filter.py**: 메시지 필터링 (특정 키워드 포함 메시지만 추출)
* **filtered_consumer.py**: 필터링된 메시지 수신 및 처리
* **spark_streaming.py**: Spark Streaming과 Kafka 통합 처리

## 관리 스크립트
* **install_kafka.sh**: Kafka 수동 설치 스크립트
* **manage_kafka.sh**: Kafka 클러스터 시작/중지/상태확인
* **manage_topics.sh**: Kafka 토픽 생성/관리/삭제

## 사용법

### Python 클라이언트 실행
```bash
# 메시지 필터링 파이프라인
python3 filter.py &
python3 filtered_consumer.py &
python3 producer.py

# Spark Streaming 실행
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 spark_streaming.py
```

### 관리 스크립트 실행
```bash
# Kafka 클러스터 관리
bash manage_kafka.sh start|stop|status

# 토픽 관리
bash manage_topics.sh create|list|describe|delete [topic-name]

# 수동 설치 (필요시)
bash install_kafka.sh install
bash install_kafka.sh configure [broker-id]
```

## 주의사항
* 모든 스크립트는 적절한 Kafka 클러스터 환경에서 실행되어야 함
* Python 스크립트 실행 전에 confluent-kafka 패키지 설치 필요
* Spark Streaming은 Spark 클러스터가 실행 중이어야 함
