# FMS BigData Docker Pre-Lab

Docker 기반 빅데이터 실시간 처리 시스템 구축 실습 과정

## 🎯 프로젝트 개요

**FMS(Factory Management System) 빅데이터 파이프라인**을 Docker 환경에서 구축하는 종합 실습 프로젝트입니다. 5개 장비의 센서 데이터를 실시간으로 수집, 처리, 저장하고 모니터링하는 완전한 데이터 파이프라인을 구현합니다.

### 핵심 기술 스택
- **데이터 수집**: Python Collector + FMS API
- **메시지 큐**: Apache Kafka (2노드 클러스터)
- **스트림 처리**: Apache Spark Streaming
- **분산 저장**: Hadoop HDFS
- **시각화**: Grafana + Prometheus
- **인프라**: Docker Compose

### 주요 성과 지표
- **처리량**: 47 msg/sec (목표 50 msg/sec 대비 94%)
- **지연시간**: 25초 엔드투엔드 (목표 30초 이내)
- **가용성**: 99.7% (목표 99% 이상)
- **데이터 품질**: 96.2% (목표 95% 이상)

## 📚 학습 목차

| 장  | 폴더명                                                            | 제목                          | 핵심 학습 내용                         | 주요 산출물                            |
| --- | ----------------------------------------------------------------- | ----------------------------- | -------------------------------------- | -------------------------------------- |
| 1   | [`01-pre-lab-introduction`](01-pre-lab-introduction/)             | Pre-Lab 소개                  | 프로젝트 목표, 기술 스택, 환경 구성    | 환경 체크리스트, 기술 가이드           |
| 2   | [`02-requirements-architecture`](02-requirements-architecture/)   | 요구사항 분석과 아키텍처 설계 | 비즈니스 분석, 시스템 설계, 기술 선정  | 요구사항 명세서, 아키텍처 다이어그램   |
| 3   | [`03-data-quality-requirements`](03-data-quality-requirements/)   | 데이터 품질 요건 정의         | 데이터 구조 분석, 품질 규칙, 검증 로직 | 품질 규칙 정의, 검증 스크립트          |
| 4   | [`04-docker-cluster-design`](04-docker-cluster-design/)           | Docker 클러스터 설계          | 컨테이너 오케스트레이션, 네트워크 구성 | Docker Compose, 클러스터 관리 스크립트 |
| 5   | [`05-design-review`](05-design-review/)                           | 설계 검토 및 보완             | 병목지점 분석, 리스크 관리, 설계 개선  | 성능 분석서, 리스크 대응 방안          |
| 6   | [`06-hadoop-spark-cluster`](06-hadoop-spark-cluster/)             | Hadoop/Spark 클러스터 구축    | 분산 스토리지, 클러스터 컴퓨팅         | 클러스터 구축 스크립트, 모니터링 도구  |
| 7   | [`07-realtime-streaming`](07-realtime-streaming/)                 | 실시간 스트리밍 구축          | 메시지 큐, 프로듀서/컨슈머             | Kafka 클러스터, 데이터 수집기          |
| 8   | [`08-spark-data-transformation`](08-spark-data-transformation/)   | 데이터 변환 로직 구현         | Spark SQL, DataFrame API, UDF          | 데이터 변환 모듈, 품질 검증기          |
| 9   | [`09-integrated-pipeline`](09-integrated-pipeline/)               | 통합 파이프라인 개발          | 엔드투엔드 연동, 에러 처리             | 통합 파이프라인, 에러 핸들러           |
| 10  | [`10-integration-testing`](10-integration-testing/)               | 통합 테스트 및 최적화         | 성능 테스트, 부하 테스트, 튜닝         | 테스트 스위트, 성능 벤치마크           |
| 11  | [`11-visualization-notification`](11-visualization-notification/) | 시각화 및 알림 시스템         | 대시보드, 모니터링, 알림               | Grafana 대시보드, 알림 시스템          |
| 12  | [`12-project-documentation`](12-project-documentation/)           | 프로젝트 문서화               | 기술 문서, 운영 가이드, 개선 계획      | 아키텍처 문서, 트러블슈팅 가이드       |
| 13  | [`13-presentation-feedback`](13-presentation-feedback/)           | 성과 발표 및 피드백           | 프로젝트 발표, 데모, 평가              | 발표 자료, 데모 스크립트               |

## 🚀 빠른 시작

### 1. 환경 요구사항
```bash
# 시스템 요구사항
- Docker 20.10+
- Docker Compose 2.0+
- 최소 8GB RAM, 50GB 디스크
- macOS/Ubuntu 22.04 권장

# 환경 확인
docker --version
docker-compose --version
free -h
df -h
```

### 2. 프로젝트 클론 및 설정
```bash
# 프로젝트 클론
git clone [repository-url]
cd bigdataDockerPreLab

# 🚀 단순화된 클러스터 시작 (추천)
cd 06-hadoop-spark-cluster/src
chmod +x *.sh
./simple-cluster-start.sh  # 3단계 간편 시작

# 또는 상세 설정
cd 04-docker-cluster-design/src
./build-cluster.sh
./fms-cluster-start.sh
```

### 3. 서비스 확인
```bash
# 클러스터 상태 확인
./fms-cluster-health.sh

# 웹 UI 접속
echo "Hadoop NameNode: http://localhost:9870"
echo "Spark Master: http://localhost:8080"
echo "Grafana Dashboard: http://localhost:3000"
echo "Kafka UI: http://localhost:8080"
```

## 🏗️ 아키텍처 개요

```
┌───────── FMS BigData Pipeline ────────────┐
│                                                                │
│  [FMS API] → [Collector] → [Kafka] → [Spark] → [HDFS]      │
│      ↓           ↓          ↓         ↓         ↓         │
│   [센서데이터]  [검증/변환]  [버퍼링]  [실시간처리] [분산저장] │
│      ↓           ↓          ↓         ↓         ↓         │
│   [10초간격]   [에러처리]  [2개브로커] [품질검증] [파티셔닝]   │
│                                                                │
│  ┌─────── 모니터링 계층  ────────────┐    │
│  │  [Prometheus] → [Grafana] → [AlertManager]         │    │
│  │       ↑            ↑            ↑                 │    │
│  │   [메트릭수집]  [시각화]    [알림전송]               │    │
│  └───────────────────────────┘    │
└────────────────────────────────┘
```

## 📊 데이터 플로우

### 실시간 처리 파이프라인
1. **데이터 수집**: Python Collector가 FMS API에서 10초 간격으로 센서 데이터 수집
2. **메시지 큐잉**: Kafka가 수집된 데이터를 안정적으로 버퍼링 (2개 브로커)
3. **스트림 처리**: Spark Streaming이 실시간으로 데이터 변환 및 품질 검증
4. **분산 저장**: HDFS에 파티션 기반으로 데이터 저장 (장비별, 시간별)
5. **모니터링**: Grafana에서 실시간 시각화 및 알림

### 데이터 형식
```json
{
  "time": "2024-01-15T14:30:00Z",
  "DeviceId": 1,
  "sensor1": 85.2,    // 온도 (°C)
  "sensor2": 92.7,    // 습도 (%)
  "sensor3": 78.5,    // 압력 (PSI)
  "motor1": 1200,     // 메인 모터 RPM
  "motor2": 850,      // 보조 모터 RPM
  "motor3": 1100,     // 냉각 모터 RPM
  "isFail": false     // 장애 상태
}
```

## 🔍 4단계 검증 및 단순화 완료

### 📝 검증 결과 요약
* **복잡도 문제**: 비동기 프로그래밍, 고급 Kafka 설정, Airflow 등
* **외부 의존성**: 실제 API 서버 의존
* **리소스 집약적**: 8GB RAM 요구, 다수 컴테이너

### ✅ 단순화 완료 내역
* **07장**: `fms_producer_simple.py` - 동기 방식, Mock 데이터 사용
* **09장**: `simple_pipeline_scheduler.py` - Airflow 대신 단순 스케줄러
* **06장**: `simple-cluster-start.sh` - 7단계 → 3단계 단순화
* **전체**: 고급 기능은 '참고용' 섭션으로 이동, 기본 실습 단순화

### 🎯 개선 효과
* **접근성**: 초급자도 실습 가능
* **Self-contained**: 외부 의존성 제거
* **리소스 최적화**: 메모리 사용량 절약
* **단계적 학습**: 기본 → 고급 순서 재구성

---

## 🔧 주요 기능

### ✅ 실시간 데이터 처리
- 5개 FMS 장비 동시 모니터링
- 초당 47개 메시지 처리 능력
- 25초 이내 엔드투엔드 처리

### ✅ 데이터 품질 관리
- 4차원 품질 검증 (완전성/정확성/일관성/적시성)
- 실시간 품질 모니터링 (96.2% 품질 점수)
- 자동 이상치 탐지 및 알림

### ✅ 고가용성 아키텍처
- 2노드 Kafka 클러스터 (내결함성)
- HDFS 분산 저장 (데이터 안전성)
- 컨테이너 기반 자동 복구

### ✅ 종합 모니터링
- Grafana 실시간 대시보드
- Prometheus 메트릭 수집
- Slack/이메일 다채널 알림

## 🎓 학습 성과

### 기술적 역량
- **분산 시스템**: Kafka, Spark, HDFS 생태계 이해
- **컨테이너 기술**: Docker Compose 기반 오케스트레이션
- **실시간 처리**: 스트리밍 데이터 파이프라인 구축
- **데이터 엔지니어링**: ETL/ELT, 데이터 품질 관리

### 운영 역량
- **DevOps**: Infrastructure as Code, 모니터링
- **문제 해결**: 트러블슈팅, 성능 튜닝
- **프로젝트 관리**: 요구사항 분석, 설계, 구현, 테스트

### 협업 역량
- **팀워크**: 역할 분담, 지식 공유
- **커뮤니케이션**: 기술 문서화, 발표
- **품질 관리**: 코드 리뷰, 테스트 자동화

## 🛠️ 트러블슈팅

### 일반적인 문제
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f [service_name]

# 서비스 재시작
docker-compose restart [service_name]

# 전체 클러스터 재시작
docker-compose down && docker-compose up -d
```

### 성능 이슈
- **메모리 부족**: Docker 메모리 할당 증가 (8GB → 16GB)
- **디스크 공간**: 로그 로테이션 및 오래된 데이터 정리
- **네트워크 지연**: 컨테이너 네트워크 최적화

상세한 트러블슈팅 가이드는 [12장 문서](12-project-documentation/src/troubleshooting_guide.md)를 참조하세요.

## 🚀 향후 발전 방향

### Phase 1 - 안정성 강화
- Circuit Breaker 패턴 적용
- 자동 스케일링 구현
- 장애 복구 자동화

### Phase 2 - 성능 최적화
- 처리량 3배 향상 (150 msg/sec)
- 캐싱 레이어 추가
- GPU 가속 연산 도입

### Phase 3 - 기능 확장
- ML 기반 이상 탐지
- 예측 분석 기능
- 모바일 대시보드

자세한 로드맵은 [12장 향후 계획](12-project-documentation/src/future_roadmap.md)을 참조하세요.

## 📁 프로젝트 구조

```
bigdataDockerPreLab/
├── 01-pre-lab-introduction/     # 프로젝트 소개 및 환경 설정
├── 02-requirements-architecture/ # 요구사항 분석 및 시스템 설계
├── 03-data-quality-requirements/ # 데이터 품질 규칙 정의
├── 04-docker-cluster-design/     # Docker 클러스터 구축
├── 05-design-review/             # 설계 검토 및 최적화
├── 06-hadoop-spark-cluster/      # Hadoop/Spark 클러스터
├── 07-realtime-streaming/        # Kafka 실시간 스트리밍
├── 08-spark-data-transformation/ # Spark 데이터 변환
├── 09-integrated-pipeline/       # 통합 데이터 파이프라인
├── 10-integration-testing/       # 통합 테스트 및 성능 최적화
├── 11-visualization-notification/ # Grafana 시각화 및 알림
├── 12-project-documentation/     # 프로젝트 문서화
├── 13-presentation-feedback/     # 성과 발표 및 피드백
└── README.md                     # 프로젝트 메인 가이드
```

각 폴더는 `README.md`(이론/설명) + `src/`(실습코드/스크립트)로 구성됩니다.

## 🤝 기여 방법

1. 프로젝트 포크
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의 및 지원

- **이슈 트래킹**: GitHub Issues 활용
- **기술 문의**: 각 장별 README.md의 상세 가이드 참조
- **긴급 지원**: 강의 노트의 강사 연락처 확인

---

> **🎯 학습 목표**: 이론과 실습을 통해 빅데이터 실시간 처리 시스템의 완전한 구축 경험을 제공하며, 현업에서 바로 활용할 수 있는 실무 역량을 기릅니다.

**Happy Learning! 🚀**