# 3. 데이터 품질 요건 정의

## 원본 데이터 구조 분석
### 3.1 FMS 센서 데이터 구조
* FMS(Factory Management System) 센서 데이터는 JSON 형태로 수집됨
* 장비별 센서값(온도, 습도, 압력), 모터 RPM, 장애상태 포함
* **샘플 데이터**: [`src/sample_sensor_data.json`](src/sample_sensor_data.json) 참조

### 3.2 데이터 타입 정의 및 검증 규칙
| 필드명   | 데이터 타입       | 필수 여부 | 유효 범위      | 비고             |
| -------- | ----------------- | --------- | -------------- | ---------------- |
| time     | String (ISO 8601) | 필수      | 현재 시간 ±1분 | 타임스탬프 검증  |
| DeviceId | Integer           | 필수      | 1-5            | 장비 ID 범위     |
| sensor1  | Float             | 필수      | 0-100          | 온도 센서 (°C)   |
| sensor2  | Float             | 필수      | 0-100          | 습도 센서 (%)    |
| sensor3  | Float             | 필수      | 0-150          | 압력 센서 (PSI)  |
| motor1   | Integer           | 필수      | 0-2000         | 메인 모터 RPM    |
| motor2   | Integer           | 필수      | 0-1500         | 보조 모터 RPM    |
| motor3   | Integer           | 필수      | 0-1800         | 냉각 모터 RPM    |
| isFail   | Boolean           | 필수      | true/false     | 장애 상태 플래그 |

## 데이터 품질 이슈 식별
### 3.3 주요 품질 이슈 유형
* **완전성 문제**
  - NULL/빈 값 존재
  - 필수 필드 누락
  - API 응답 실패

* **정확성 문제**
  - 센서 값 범위 초과
  - 타임스탬프 오류
  - 데이터 타입 불일치

* **일관성 문제**
  - 중복 데이터 수신
  - 시간 순서 역전
  - 장비 ID 불일치

## 전처리 규칙 및 변환 로직 정의
### 3.4 NULL 값 처리 전략
* **REJECT**: 타임스탬프, 장비 ID 같은 핵심 필드
* **INTERPOLATE**: 센서값의 경우 이전 정상값으로 보간
* **DEFAULT**: 모터 RPM은 0, 장애상태는 false로 기본값 설정
* **상세 규칙**: [`src/null_handling_rules.py`](src/null_handling_rules.py) 참조

### 3.5 이상치(Outlier) 탐지 및 처리
* **탐지 방법**: IQR(Interquartile Range) 기반
* **윈도우 크기**: 최근 100개 데이터 기준
* **센서별 Z-Score 임계값**: 센서(3.0), 모터(2.5)
* **처리 방법**: CLIP, INTERPOLATE, FLAG, REJECT
* **상세 규칙**: [`src/outlier_detection_rules.py`](src/outlier_detection_rules.py) 참조

### 3.6 데이터 타입 검증 및 변환
* **타임스탬프**: ISO8601 형식 강제, 오류 시 거부
* **장비 ID**: 1-5 범위 정수값, 범위 외 거부
* **센서/모터값**: 자동 형변환 시도, 실패 시 거부
* **상세 규칙**: [`src/type_validation_rules.py`](src/type_validation_rules.py) 참조

### 3.7 장애 데이터 분류 및 저장 정책
* **정상 데이터**: HDFS_MAIN (1년 보관)
* **장애 데이터**: HDFS_ALERT (3년 보관, 알림 발송)
* **비정상 데이터**: HDFS_QUARANTINE (30일 보관, 검토 필요)
* **상세 정책**: [`src/fail_data_policy.py`](src/fail_data_policy.py) 참조

## 데이터 검증 기준 수립
### 3.8 품질 메트릭 KPI
* **완전성**: 99% (NULL 값 비율 1% 이하)
* **정확성**: 95% (유효 범위 내 데이터 비율)
* **적시성**: 30초 이내 처리 완료
* **일관성**: 98% (중복 데이터 비율 2% 이하)
* **상세 메트릭**: [`src/quality_metrics.py`](src/quality_metrics.py) 참조

### 3.9 데이터 품질 모니터링 체계
* **실시간 품질 체크**
  - 매 배치마다 품질 메트릭 계산
  - 임계값 위반 시 즉시 알림 발송
  - 품질 리포트 자동 생성

* **품질 대시보드 구성**
  - 장비별 데이터 품질 현황 시각화
  - 시간대별 품질 트렌드 분석
  - 이상치 발생 패턴 및 예측

## 주요 산출물
* 데이터 품질 규칙 정의서
* 전처리 로직 구현 스크립트
* 품질 모니터링 대시보드 설계서

## 4. 예제 코드 실행

### 데이터 품질 검증 테스트 실행 방법

```bash
# (필요시) 의존성 설치
pip install requests

# 테스트 코드 실행
python3 src/test_quality_validation.py
```

- 외부 FMS API(`http://finfra.iptime.org:9872/{device_id}/`)에 연결되어야 하며, 네트워크 환경에 따라 실행이 제한될 수 있습니다.

#### 예시 출력

```
=== FMS API 데이터 품질 검증 테스트 ===

Device 1:
  Data: {
    "time": "2025-06-15T15:30:00",
    "DeviceId": 1,
    "sensor1": 23.5,
    "sensor2": 45.2,
    "sensor3": 101.3,
    "motor1": 1500,
    "motor2": 1200,
    "motor3": 1300,
    "isFail": false
  }
  ✅ Data quality OK

Device 2:
  Data: {
    ...
  }
  Quality Issues:
    ❌ sensor1 out of range: 150.0 (expected 0-100)
    ❌ motor2 out of range: 2000 (expected 0-1500)
```
