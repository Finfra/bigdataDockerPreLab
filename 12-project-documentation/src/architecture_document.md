# FMS BigData Pipeline Architecture

## 전체 구조
- **Data Collection**: Python Collector → Kafka
- **Stream Processing**: Spark Streaming → HDFS
- **Visualization**: Grafana Dashboard
- **Monitoring**: Prometheus + AlertManager

## 주요 컴포넌트
| 컴포넌트 | 기술 스택 | 역할 |
|----------|-----------|------|
| 데이터 수집 | Python + Kafka Producer | API 호출 및 데이터 발행 |
| 메시지 큐 | Kafka Cluster | 스트리밍 데이터 버퍼링 |
| 스트림 처리 | Spark Streaming | 실시간 데이터 처리 |
| 데이터 저장 | HDFS | 분산 파일 시스템 |
| 시각화 | Grafana | 실시간 모니터링 |

## 데이터 플로우
```
FMS API → Python Collector → Kafka → Spark Streaming → HDFS
    ↓         ↓              ↓         ↓              ↓
[10초 간격] [검증/변환]    [버퍼링]   [실시간처리]    [분산저장]
    ↓         ↓              ↓         ↓              ↓
[5개 장비]  [에러처리]     [2개 브로커] [품질검증]     [파티셔닝]
```

## 네트워크 및 포트 구성
| 서비스 | 컨테이너명 | 포트 | 프로토콜 |
|--------|------------|------|----------|
| Kafka | fms-kafka-1 | 9092 | TCP |
| HDFS NameNode | fms-namenode | 9870 | HTTP |
| Spark Master | fms-spark-master | 8080 | HTTP |
| Grafana | fms-grafana | 3000 | HTTP |
| FMS Collector | fms-collector | 8090 | HTTP |

## 데이터 스키마
### FMS 센서 데이터
```json
{
  "time": "2024-01-15T14:30:00Z",
  "DeviceId": 1,
  "sensor1": 85.2,
  "sensor2": 92.7, 
  "sensor3": 78.5,
  "motor1": 1200,
  "motor2": 850,
  "motor3": 1100,
  "isFail": false
}
```