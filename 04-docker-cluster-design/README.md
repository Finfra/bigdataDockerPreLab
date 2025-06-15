# 4. Docker 기반 클러스터 환경 설계
FMS 시스템에 특화된 Docker 클러스터 환경을 설계

## Hadoop/Spark 클러스터 구성도 작성
### 4.1 전체 아키텍처
```
┌─────────────────────────────┐
│                  Docker Network (fms-network)            │
├─────────────────────────────┤
│                                                          │
│ ┌──────────────────────────┐ │
│ │                    i1 Container                    │ │
│ │   (Ansible,Management & Monitoring Services)       │ │
│ │ ┌────┐ ┌────┐ ┌─────┐ ┌───┐│ │
│ │ │  Kafka │ │Grafana │ │Prometheus│ │  n8n ││ │
│ │ │Producer│ │  :3000 │ │  :9090   │ │ :5678││ │
│ │ │  :9092 │ │        │ │          │ │      ││ │
│ │ └────┘ └────┘ └─────┘ └───┘│ │
│ └──────────────────────────┘ │
│                          │                              │
│                      Kafka Stream                        │
│                          ▼                              │
│ ┌──────────────────────────┐ │
│ │                 Hadoop/Spark Cluster               │ │
│ │                                                    │ │
│ │  ┌─────┐   ┌─────┐   ┌─────┐  │ │
│ │  │    s1    │   │    s2    │   │    s3    │  │ │
│ │  │(Master)  │   │(Worker)  │   │(Worker)  │  │ │
│ │  │          │   │          │   │          │  │ │
│ │  │Consumer  │   │          │   │          │  │ │
│ │  │NameNode  │   │DataNode  │   │DataNode  │  │ │
│ │  │ :9870    │   │ :9864    │   │ :9864    │  │ │
│ │  │          │   │          │   │          │  │ │
│ │  │ResrcMgr  │   │NodeMgr   │   │NodeMgr   │  │ │
│ │  │ :8088    │   │ :8042    │   │ :8042    │  │ │
│ │  │          │   │          │   │          │  │ │
│ │  │SprkMstr  │   │SprkWrkr  │   │SprkWrkr  │  │ │
│ │  │ :8080    │   │ :8081    │   │ :8081    │  │ │
│ │  └─────┘   └─────┘   └─────┘  │ │
│ └──────────────────────────┘ │
│                                                          │
└─────────────────────────────┘
```

### 컨테이너 역할 분담
* **i1 (Management & Monitoring Services)**
  - Kafka Producer: 센서 데이터 수집 및 Kafka로 전송
  - Grafana: 모니터링 대시보드 및 시각화
  - Prometheus: 메트릭 수집 및 저장
  - n8n: 워크플로우 자동화 및 ETL 처리

* **s1 (Hadoop/Spark Master + Kafka Consumer)**
  - Kafka Consumer: Kafka에서 데이터 수신 및 처리
  - NameNode: HDFS 메타데이터 관리
  - ResourceManager: YARN 리소스 관리
  - Spark Master: Spark 클러스터 마스터

* **s2, s3 (Hadoop/Spark Workers)**
  - DataNode: HDFS 데이터 저장
  - NodeManager: YARN 워커 노드
  - Spark Worker: Spark 작업 실행

## Docker Compose 구성
### 4.2 메인 클러스터 구성
* **네트워크**: 172.25.0.0/16 대역의 브리지 네트워크
* **서비스 구성**:
  - Zookeeper + Kafka 클러스터 (2노드)
  - Hadoop HDFS (NameNode + DataNode 3개)
  - YARN ResourceManager + NodeManager
  - Spark Master + Worker
  - MySQL, Grafana 모니터링
* **메인 구성파일**: [`src/docker-compose.yml`](src/docker-compose.yml)

## Kafka 토픽 및 파티션 설계
### 4.3 토픽 구성 전략
| 토픽명              | 파티션 | 복제인수 | 보관기간 | 용도             |
| ------------------- | ------ | -------- | -------- | ---------------- |
| fms-raw-data        | 5      | 2        | 7일      | 원시 센서 데이터 |
| fms-processed-data  | 3      | 2        | 30일     | 전처리된 데이터  |
| fms-alerts          | 1      | 2        | 1일      | 실시간 알림      |
| fms-quality-metrics | 2      | 2        | 7일      | 품질 메트릭      |

* **토픽 초기화**: [`src/init-kafka-topics.sh`](src/init-kafka-topics.sh)

## 환경 설정 파일들
### 4.4 Hadoop 클러스터 설정
* **Core 설정**: [`src/core-site.xml`](src/core-site.xml)
  - HDFS 기본 경로: hdfs://namenode:8020
  - Proxy 사용자 설정
* **HDFS 설정**: [`src/hdfs-site.xml`](src/hdfs-site.xml)
  - 복제인수: 2
  - WebHDFS 활성화
  - 권한 비활성화 (개발환경)

## 클러스터 관리 도구
### 4.5 운영 스크립트
* **클러스터 시작**: [`src/fms-cluster-start.sh`](src/fms-cluster-start.sh)
  - 서비스 순차 시작 (Zookeeper → Kafka → Hadoop → Spark)
  - 의존성 대기 시간 관리
  - 웹 UI 접속 정보 제공

* **상태 점검**: [`src/fms-cluster-health.sh`](src/fms-cluster-health.sh)
  - Kafka 토픽 목록 확인
  - HDFS 클러스터 상태 점검
  - Spark 애플리케이션 상태
  - 데이터 수집기 헬스체크

## 리소스 할당 및 확장성 고려사항
### 4.6 리소스 제한 관리
* **메모리/CPU 제한**: [`src/docker-compose.override.yml`](src/docker-compose.override.yml)
  - NameNode: 2G 메모리, 1 CPU
  - Spark Master: 4G 메모리, 2 CPU
  - Kafka: 2G 메모리, 1 CPU

### 4.7 동적 확장 지원
* **확장 스크립트**: [`src/scale-cluster.sh`](src/scale-cluster.sh)
  - DataNode 노드 추가
  - Spark Worker 확장
  - Kafka 브로커 추가

## 주요 포트 및 웹 UI
| 서비스               | 포트 | 웹 UI | 용도              |
| -------------------- | ---- | ----- | ----------------- |
| Hadoop NameNode      | 9870 | ✓    | HDFS 관리         |
| YARN ResourceManager | 8088 | ✓    | 리소스 관리       |
| Spark Master         | 8080 | ✓    | Spark 클러스터    |
| Grafana              | 3000 | ✓    | 모니터링 대시보드 |
| FMS Collector        | 8090 | ✓    | 데이터 수집 상태  |

## 핵심 설계 원칙
* **고가용성**: 2노드 복제를 통한 장애 대응
* **확장성**: 수평 확장 가능한 마이크로서비스 구조
* **모니터링**: 실시간 상태 점검 및 로그 관리
* **운영 편의성**: 스크립트 기반 자동화된 관리

## 주요 산출물
* Docker Compose 클러스터 구성
* Kafka 토픽 설계 및 초기화
* Hadoop/Spark 설정 파일
* 클러스터 운영 관리 스크립트

