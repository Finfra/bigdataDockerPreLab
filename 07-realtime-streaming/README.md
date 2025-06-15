# 7. 실시간 데이터 스트리밍 환경 구축
**Kafka 클러스터 설치부터 Spark Streaming 통합까지 완전한 실시간 데이터 파이프라인 구현**

## Kafka 클러스터 설치 및 구성
### 7.1 Kafka 설치 방법 선택
* **Ansible 자동 설치** (권장 방법)
* **수동 설치 방법** (개별 컨테이너 설정)

### 7.2 Ansible 자동 설치 (권장)
```bash
# i1 컨테이너에서 실행
docker exec -it i1 bash
ansible-playbook -i /df/ansible-kafka/hosts /df/ansible-kafka/kafka_install.yml -e ansible_python_interpreter=/usr/bin/python3.12
source /etc/bashrc
```

### 7.3 수동 설치 (선택사항)
각 컨테이너별 개별 설치가 필요한 경우 `src/install_kafka.sh` 참조

#### 설치 확인
```bash
# i1에서 확인
kafka-topics.sh --help
python3 -c "from confluent_kafka import Producer"  # 에러 안나면 성공

# s1에서 확인
which kafka-server-start.sh
ls /tmp/kafka-logs  # 로그 디렉터리 확인
```

## Kafka 클러스터 관리
### 7.4 클러스터 시작/중지
```bash
# 클러스터 시작
bash src/manage_kafka.sh start

# 클러스터 중지
bash src/manage_kafka.sh stop

# 상태 확인
bash src/manage_kafka.sh status
```

### 7.5 토픽 관리
```bash
# 기본 토픽 생성
bash src/manage_topics.sh create

# 토픽 목록 확인
bash src/manage_topics.sh list

# 특정 토픽 상세 정보
bash src/manage_topics.sh describe sensor-data
```

## 실제 FMS 데이터 수집 및 처리
### 7.6 실제 API 데이터 Producer
**실제 FMS 시스템**에서 센서 데이터를 수집하여 Kafka로 전송:

```bash
# 필요한 패키지 설치
cd src
pip3 install -r requirements.txt

# 테스트 실행 (한 번만)
python3 fms_producer.py test

# 연속 실행 (10초 간격으로 계속)
python3 fms_producer.py
```

**API 정보**:
- **엔드포인트**: `http://finfra.iptime.org:9872/{DeviceId}/`
- **장비 범위**: DeviceId 1~5 (총 5개 장비)
- **갱신 주기**: 10초마다 자동 수집
- **데이터 구조**: 센서값(sensor1~3), 모터값(motor1~3), 장애상태(isFail)

### 7.7 실제 데이터 분석 Consumer
```bash
# 실제 FMS 데이터 분석 (터미널 2에서)
python3 fms_consumer.py
```

**분석 기능**:
- 센서 평균값 계산
- 임계값 초과 알림 (센서 >90, 모터 >1500)
- 장비 실패 상태 모니터링
- 실시간 상태 분류 (NORMAL/CRITICAL)

## 기본 Producer/Consumer 테스트
### 7.8 콘솔 기반 테스트
```bash
# Producer (터미널 1)
kafka-console-producer.sh --topic test-topic --bootstrap-server s1:9092

# Consumer (터미널 2)
kafka-console-consumer.sh --topic test-topic --from-beginning --bootstrap-server s1:9092
```

### 7.9 Python 클라이언트 테스트
기본 메시지 생성:
```bash
cd src
python3 producer.py
```

**상세 구현**: `src/producer.py`, `src/filter.py`, `src/filtered_consumer.py` 참조

## 고급 메시지 처리
### 7.10 메시지 필터링 파이프라인
1. **Input Topic**: 원시 메시지 수신
2. **Filter Process**: 특정 키워드 포함 메시지만 추출
3. **Filtered Topic**: 필터링된 메시지 저장

```bash
# 필터링 프로세스 시작
cd src
python3 filter.py &
python3 filtered_consumer.py &
python3 producer.py
```

### 7.11 고가용성 테스트
```bash
# 복제본 포함 토픽으로 장애 복구 테스트
kafka-console-producer.sh --topic replicated-topic --bootstrap-server s1:9092,s2:9092,s3:9092

# s3 노드 중지 후에도 메시지 처리 확인
# docker stop s3
kafka-console-consumer.sh --topic replicated-topic --bootstrap-server s1:9092,s2:9092
```

## Spark Streaming 통합
### 7.12 실시간 스트림 분석
Spark에서 Kafka 데이터를 실시간으로 처리:

```python
# 기본 구조 예시
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "s1:9092,s2:9092,s3:9092") \
    .option("subscribe", "sensor-data") \
    .load()
```

**완전한 구현**: `src/spark_streaming.py` 참조

### 7.13 HDFS 저장
```python
# 스트리밍 데이터를 HDFS에 저장
query = processed_df.writeStream \
    .format("parquet") \
    .option("path", "hdfs://s1:8020/streaming/") \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()
```

## 실시간 모니터링
### 7.14 상태 확인 명령어
```bash
# Consumer 그룹 상태
kafka-consumer-groups.sh --describe --all-groups --bootstrap-server s1:9092,s2:9092,s3:9092

# 토픽 상세 정보
kafka-topics.sh --describe --topic sensor-data --bootstrap-server s1:9092,s2:9092,s3:9092

# Spark 스트리밍 상태
# http://localhost:8080 웹 UI 접속
```

### 7.15 문제 해결
```bash
# 로그 확인
tail -f /opt/kafka/logs/server.log

# 서비스 재시작
bash src/manage_kafka.sh stop
bash src/manage_kafka.sh start
```

## 성능 최적화
### 7.16 주요 설정 파라미터
* **배치 크기**: 16KB (처리량 최적화)
* **압축**: gzip (저장 공간 절약)
* **파티션 수**: CPU 코어 수 × 2
* **복제 인수**: 2 (고가용성)

### 7.17 확장성 고려사항
* **수평 확장**: Worker 노드 추가
* **파티션 증가**: 높은 처리량 요구 시
* **체크포인트**: 장애 복구용 상태 저장

---

## 실습 가이드

### 실습 1: Kafka 클러스터 구축
```bash
# 1. 자동 설치
docker exec -it i1 bash
ansible-playbook -i /df/ansible-kafka/hosts /df/ansible-kafka/kafka_install.yml -e ansible_python_interpreter=/usr/bin/python3.12

# 2. 클러스터 시작
bash src/manage_kafka.sh start

# 3. 토픽 생성
bash src/manage_topics.sh create
```

### 실습 2: 실제 FMS 데이터 수집 및 분석
```bash
# 1. 필요한 패키지 설치
cd src
pip3 install -r requirements.txt

# 2. 실제 API 테스트
python3 fms_producer.py test

# 3. 실제 데이터 연속 수집 (터미널 1)
python3 fms_producer.py

# 4. 실시간 데이터 분석 (터미널 2)
python3 fms_consumer.py

# 5. 결과 확인
# 센서 임계값 초과, 장비 장애 등 실시간 알림 확인
```

### 실습 3: 기본 메시지 흐름 테스트
```bash
# Producer/Consumer 기본 테스트
kafka-console-producer.sh --topic test-topic --bootstrap-server s1:9092
kafka-console-consumer.sh --topic test-topic --from-beginning --bootstrap-server s1:9092
```

### 실습 4: Python 메시지 필터링
```bash
cd src
# 백그라운드에서 필터링 프로세스 시작
python3 filter.py &
python3 filtered_consumer.py &

# 메시지 생성
python3 producer.py
```

### 실습 5: Spark Streaming 통합
```bash
# Spark에서 Kafka 스트림 처리
cd src
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 spark_streaming.py
```

### 실습 6: 고가용성 테스트
```bash
# 복제본 토픽 테스트
kafka-console-producer.sh --topic replicated-topic --bootstrap-server s1:9092,s2:9092,s3:9092

# 노드 장애 시뮬레이션
# docker stop s3
kafka-console-consumer.sh --topic replicated-topic --bootstrap-server s1:9092,s2:9092
```

## 핵심 성과 지표
* **실시간성**: 메시지 처리 지연 < 5초
* **안정성**: 99.9% 메시지 전달 보장
* **확장성**: 초당 10,000+ 메시지 처리 가능
* **고가용성**: 단일 노드 장애 시에도 서비스 지속

## 주요 산출물
* **Kafka 클러스터**: 3노드 분산 메시지 브로커
* **Python 클라이언트**: 고급 메시지 필터링 및 처리
* **Spark Streaming**: 실시간 데이터 분석 엔진
* **HDFS 통합**: 스트리밍 데이터 영구 저장
* **확장 가능한 아키텍처**: 마이크로서비스 기반 분산 시스템

---

**다음 챕터**: [8. Spark 데이터 변환](../08-spark-data-transformation/) - 수집된 스트리밍 데이터의 고급 분석 및 변환
