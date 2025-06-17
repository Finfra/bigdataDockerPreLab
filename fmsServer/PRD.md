# 프로젝트 개요
bigdataDockerPreLab_restServer는 실제 서버 접속이 불가한 상황에서 가상의 REST 서버를 구축하여 데이터를 제공하는 프로젝트입니다.

# 주요 기능
- 5개 장비(DeviceId 1~5)의 센서 및 모터 데이터를 10초 주기로 생성 및 갱신
- config.yaml 기반 평균, 표준편차, 이상치 및 -1 출력 확률을 반영한 데이터 생성
- 클라이언트 접속 로그 및 데이터 로그 저장
- tmux를 활용한 서비스 시작, 중지, 재시작 스크립트 제공

# 개발 환경 구성
- Python 3.10.12 (권장)
- Web.py, PyYAML 라이브러리 사용
- tmux 설치 권장
- 로그 및 데이터 저장용 디렉토리 생성 및 권한 설정 필요

# 설치 및 실행 방법
1. 가상환경 생성 및 활성화 (권장)
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```


# API 사용법
- GET 요청: `http://{서버주소}:9872/{DeviceId}/`
- 응답 예시:
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

# 로그 및 데이터 저장 위치
- 클라이언트 접속 로그: `log/client/{ip}_{시각}.log` (예: log/client/192.168.0.1_20250614_095300.log)
- 데이터 로그: `log/{DeviceId}/`

# 서비스 관리
- start.sh: tmux 세션 rs 생성 및 서버 실행
- stop.sh: tmux 세션 rs 종료
- restart.sh: stop.sh와 start.sh 연속 실행
- 서비스 시작/중지/재시작 로그: `log/admin/{날짜}_{stop|start|restart}.log`

# 개발 단계
## 1단계. 환경구성
- [v] 1.1 Python 3.10.12 환경 준비
- [v] 1.2 venv 가상환경 생성 및 활성화
- [v] 1.3 requirements.txt 파일 생성 및 필수 패키지(Web.py, PyYAML) 명시
- [v] 1.4 pip install -r requirements.txt로 패키지 설치
- [v] 1.5 tmux 설치(권장)
- [v] 1.6 로그/데이터 디렉토리 생성 및 권한 설정

## 2단계. Rest 테스트
- [v] 2.1 서버 실행 후, 각 DeviceId(1~5)에 대해 GET 요청 시 고정된 값의 JSON이 정상적으로 반환되는지 확인
- [v] 2.2 예시: `curl http://localhost:9872/1/` 등으로 테스트
- [v] 2.3 반환 JSON 구조는 "API 사용법"의 예시와 동일해야 함
- [v] 2.4 tmux session세션 rs만들어서 venv활성화 시키고 py파일 테스트
- [v] 2.5 테스트 결과 및 확인 방법을 README.md에 기록

## 3단계. 가변값 테스트
- [v] 3.1 config.yaml의 설정(평균, 표준편차, 이상치, -1 출력 확률 등)에 따라 각 센서/모터 값이 주기적으로 갱신되어 반환되는지 확인
- [v] 3.2 여러 번 GET 요청 시 값이 변하는지, config.yaml의 설정이 반영되는지 테스트
- [v] 3.3 테스트 방법 및 예시를 README.md에 기록

## 4단계. 로그값 생성
- [v] 4.1 클라이언트 접속 로그(`log/client/{ip}_{시각}.log`)와 데이터 로그(`log/{DeviceId}/`)가 정상적으로 생성되는지 확인
- [v] 4.2 start.sh, stop.sh, restart.sh 실행 시 관리 로그(`log/admin/{날짜}_{stop|start|restart}.log`)가 생성되는지 확인
- [v] 4.3 각 로그 파일의 예시와 확인 방법을 README.md에 기록

## 5단계. 최종 테스트
- [v] 5.1 README.md의 설치 및 실행 방법, 테스트 방법, 예시가 실제 동작과 일치하는지 검증
- [v] 5.2 PRD.md의 모든 요건이 충족되었는지 체크리스트 형태로 점검

  ### 최종 체크리스트
  - [v] 1단계: 환경구성
  - [v] 2단계: Rest 테스트
  - [v] 3단계: 가변값 테스트
  - [v] 4단계: 로그값 생성 (클라이언트 로그 파일명: log/client/{ip}_{시각}.log)
  - [v] 5.1 README.md 실제 동작 일치 검증
  - [v] 5.2 PRD.md 요건 체크리스트 점검
  - [v] 5.3 모든 기능 정상 동작 및 README.md에 완료 명시
  - [v] 5.4 TDD 코드(tdd.sh) 작성 및 사용법 추가

- [v] 5.3 최종적으로 모든 기능이 정상 동작함을 확인한 후, 완료 여부를 README.md에 명시
