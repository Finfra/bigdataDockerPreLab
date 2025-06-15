# 1. Pre-Lab 소개, 주제 소개 Tech Check
## Pre-Lab intro
### 1.1 과정 목표
* **BigData 실시간 처리 파이프라인 구축**
  - Docker 기반 분산 처리 환경 구성
  - 실시간 데이터 수집, 처리, 저장 시스템 개발
  - FMS(Facility Management System) 모니터링 시스템 구현

### 1.2 학습 성과물
* Kafka-Spark-HDFS 기반 실시간 데이터 파이프라인
* Docker Compose 기반 클러스터 환경
* 실시간 모니터링 대시보드 및 알림 시스템
* 팀용 git hub repository(소스 및 보고서 )  
  - 비공개 계정 가능가능(강사 초대: nowage)

## Lab 주제 설명
### 2.1 FMS 시스템 개요
* **시설 관리 시스템(Facility Management System)**
  - 제조업체 설비 모니터링 시스템
  - 실시간 센서 데이터 수집 및 분석
  - 설비 장애 예측 및 알림 기능

### 2.2 데이터 소스 정보
* **API 엔드포인트**: `http://finfra.iptime.org:9872/{DeviceId}/`
* **장비 범위**: DeviceId 1~5 (총 5개 장비)
* **데이터 갱신 주기**: 10초마다 업데이트
* **응답 데이터 구조**:
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

### 2.3 구현 목표
* **실시간 데이터 수집**: 5개 장비로부터 10초 간격 데이터 수집
* **데이터 전처리**: 센서 값 검증, 이상치 탐지
* **실시간 분석**: 설비 상태 모니터링, 장애 예측
* **알림 시스템**: 임계값 초과 시 SMS/이메일 알림
* **데이터 저장**: 히스토리 데이터 HDFS 저장

## 테크 체크 및 부족 부분에 대한 설명이나 자료 제공
### 3.1 필수 기술 스택
* **Docker & Docker Compose**
  - 컨테이너 기반 환경 구성
  - 멀티 컨테이너 오케스트레이션
* **Apache Kafka**
  - 실시간 메시지 스트리밍
  - Producer/Consumer 패턴
* **Apache Spark**
  - 분산 데이터 처리
  - Spark Streaming, Spark SQL
* **Apache Hadoop (HDFS)**
  - 분산 파일 시스템
  - 대용량 데이터 저장

### 3.2 개발 환경 요구사항
* **하드웨어 최소 사양**
  - RAM: 8GB 이상 (권장 16GB)
  - Storage: 50GB 이상 여유 공간
  - CPU: 4코어 이상
* **소프트웨어 요구사항**
  - Docker Desktop 설치
  - Python 3.8+ 환경
  - Git 버전 관리 도구

### 3.3 사전 학습 자료
* **Docker 기초**: [Docker Official Tutorial](https://docs.docker.com/get-started/)
* **Kafka 개념**: [Apache Kafka Quickstart](https://kafka.apache.org/quickstart)
* **Spark 기초**: [Spark Programming Guide](https://spark.apache.org/docs/latest/programming-guide.html)

## 4. 실습 환경 테스트 및 검증 완료

### 4.1 환경 체크 결과 예✅
* windows환경에서는 수동으로 확인.
```bash
# 환경 체크 실행
./check_environment.sh

# 결과:
✅ Docker: 정상 작동 (v27.5.1)
✅ Docker Compose: 정상 설치 (v2.32.4)
✅ Python: 정상 설치 (v3.9.6)
✅ Git: 정상 설치
✅ 메모리: 64GB (충분)
✅ 디스크: 460GB 여유 공간
⚠️ 포트 사용: 일부 포트 사용 중 (정상 범위)
```

### 4.2 외부 API 서버 테스트 예✅
* windows환경에서는 수동으로 확인.
```bash
# 외부 API 테스트
python3 test_external_api.py

# 결과: 모든 5개 장비 정상 작동
✅ 장비 1-5: 정상 응답
✅ 데이터 형식: JSON 구조 검증 통과
✅ 센서 데이터: 실시간 업데이트 확인
```


### 4.4 테스트 요약
* **환경 준비도**: 100% (환경 설정 완료)
* **API 연결성**: 100% (외부 서버 정상)
* **Mock 시스템**: 100% (로컬 테스트 환경 완비)
* **다음 단계 준비**: ✅ 2장 진행 가능

