# 9. 통합 데이터 파이프라인 모듈 개발

## Kafka-Spark Streaming 연동
### 9.1 실시간 스트리밍 처리 모듈
* **스트림 처리기**: Kafka → Spark Streaming 실시간 연동
* **데이터 파싱**: JSON 스키마 기반 검증 및 변환
* **품질 점수**: 센서 범위 기반 실시간 품질 계산
* **체크포인트**: 장애 복구를 위한 상태 저장
* **실시간 처리기**: [`src/fms-realtime-processor.py`](src/fms-realtime-processor.py)

### 9.2 데이터 파티셔닝 전략
| 저장 위치        | 파티션 기준                 | 보존 기간 | 압축 형식 |
| ---------------- | --------------------------- | --------- | --------- |
| `/fms/raw-data`  | device_id, year, month, day | 30일      | gzip      |
| `/fms/processed` | device_id, hour             | 365일     | snappy    |
| `/fms/alerts`    | severity, day               | 1095일    | lz4       |

## HDFS 저장 로직 구현
### 9.3 계층화 저장 시스템
* **원시 데이터**: Parquet 형태, 30초 간격 배치 저장
* **처리된 데이터**: Delta Lake 형태, 1분 간격 업데이트
* **알림 데이터**: JSON 형태, 10초 간격 실시간 저장
* **파티셔닝**: 장비별, 시간별 효율적 분할
* **저장 관리자**: [`src/storage_manager.py`](src/storage_manager.py)

## 배치 처리 스케줄링
### 9.4 단순 스케줄러 기반 워크플로우
* **데이터 수집**: Mock 데이터 생성 및 검증
* **스트림 처리**: Spark 애플리케이션 실행
* **품질 검사**: 데이터 품질 검증 및 리포트
* **작업 의존성**: 순차적 실행 및 에러 처리
* **재시도 정책**: 기본 로깅 및 에러 처리
* **단순 스케줄러**: [`src/simple_pipeline_scheduler.py`](src/simple_pipeline_scheduler.py)
* **Airflow DAG (참고용)**: [`src/fms_data_pipeline.py`](src/fms_data_pipeline.py)

## 에러 핸들링 및 로깅 구현
### 9.5 종합 에러 처리 시스템
* **에러 등급**: LOW/MEDIUM/HIGH/CRITICAL 4단계
* **로깅 전략**: 파일 + 콘솔 이중 로깅
* **알림 시스템**: 심각한 에러 시 즉시 알림
* **복구 메커니즘**: 자동 재시도 및 격리
* **에러 핸들러**: [`src/error_handler.py`](src/error_handler.py)

## 파이프라인 아키텍처
```
FMS API → Kafka → Spark Streaming → HDFS
    ↓        ↓         ↓           ↓
  수집기    버퍼링    실시간처리   계층저장
    ↓        ↓         ↓           ↓
  에러처리  재전송    품질검증    백업/복제
```

## 주요 기술 특징
* **실시간 처리**: 30초 이내 데이터 처리 완료
* **내결함성**: 체크포인트 기반 장애 복구
* **확장성**: 파티션 기반 수평 확장
* **모니터링**: 종합 로깅 및 알림 시스템

## 주요 산출물
* 실시간 스트리밍 처리 모듈
* HDFS 계층화 저장 시스템
* Airflow 기반 배치 스케줄러
* 종합 에러 처리 및 로깅 시스템
