# bigdataDockerPreLab_restServer

## 프로젝트 개요
실제 서버 접속이 불가한 상황에서 가상의 REST 서버를 구축하여 데이터를 제공하는 프로젝트입니다.

## 개발 환경
- Python 3.10.12 (권장)
- 가상환경(venv) 사용 권장

---

> **⚠️ 중요: 모든 python 스크립트는 반드시 tmux 세션(rs)에서 실행해야 하며, venv가 활성화된 상태여야 합니다.**
> 
> - tmux 세션이 없으면 `tmux new-session -d -s rs`로 생성 후 사용하세요.
> - tmux 세션 내에서 `source venv/bin/activate`로 가상환경을 활성화한 뒤 python 스크립트를 실행하세요.
> - 이 규칙은 서버 실행, 테스트, 기타 모든 python 스크립트에 공통 적용됩니다.

---

## 설치 및 실행 방법

1. 가상환경 생성 및 활성화
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

2. 필수 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```

3. tmux 세션에서 서버 실행 및 REST 테스트

   1) tmux 세션(rs) 생성 및 진입
   ```bash
   tmux new -s rs
   ```

   2) 가상환경 활성화
   ```bash
   source venv/bin/activate
   ```

   3) 서버 실행
   ```bash
   python server.py
   ```

   4) 별도 터미널에서 REST API 테스트 (DeviceId 1~5)
   ```bash
   curl http://finfra.iptime.org:9872/1/
   curl http://finfra.iptime.org:9872/2/
   curl http://finfra.iptime.org:9872/3/
   curl http://finfra.iptime.org:9872/4/
   curl http://finfra.iptime.org:9872/5/
   ```

   5) 정상 응답 예시
   ```json
   {
     "time": "2025-06-14T07:40:27Z",
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

## 3단계: 가변값 및 config.yaml 반영 테스트

1. 여러 번 GET 요청 시 센서/모터 값이 주기적으로 변하는지 확인
   ```bash
   curl http://finfra.iptime.org:9872/1/
   curl http://finfra.iptime.org:9872/1/
   curl http://finfra.iptime.org:9872/1/
   # 여러 번 실행 시 sensor/motor 값이 매번 달라짐을 확인
   ```

2. config.yaml의 설정(평균, 표준편차, 이상치, -1 출력 확률 등)이 반영되는지 확인
   - config.yaml에서 예를 들어 sensor1의 mean 값을 100.0으로 변경 후 서버 재시작
   - 다시 GET 요청 시 sensor1 값이 평균적으로 100 부근에서 생성되는지 확인

3. 테스트 예시
   ```json
   {
     "time": "2025-06-14T07:50:00Z",
     "DeviceId": 1,
     "sensor1": 78.3,
     "sensor2": 91.1,
     "sensor3": 80.2,
     "motor1": 1250,
     "motor2": 900,
     "motor3": 1080,
     "isFail": false
   }
   {
     "time": "2025-06-14T07:50:10Z",
     "DeviceId": 1,
     "sensor1": 82.7,
     "sensor2": 88.9,
     "sensor3": 75.6,
     "motor1": 1190,
     "motor2": 870,
     "motor3": 1120,
     "isFail": false
   }
   # 값이 매번 달라짐을 확인
   ```

4. config.yaml 변경 후 테스트 예시
   - sensor1의 mean을 100.0으로 변경 후
   ```json
   {
     "time": "2025-06-14T07:55:00Z",
     "DeviceId": 1,
     "sensor1": 101.2,
     "sensor2": 92.7,
     "sensor3": 78.5,
     "motor1": 1200,
     "motor2": 850,
     "motor3": 1100,
     "isFail": false
   }
   # sensor1 값이 평균적으로 100 부근에서 생성됨을 확인
   ```

5. 테스트 방법 및 결과를 통해 config.yaml의 설정이 정상적으로 반영되고, 값이 주기적으로 갱신됨을 확인할 수 있음.

## requirements.txt
필수 패키지 목록은 requirements.txt에 명시되어 있습니다.
- web.py
- PyYAML

## 로그 생성 테스트

아래 명령어로 1~5번 DeviceId에 대해 일괄로 GET 요청을 보내고,  
각 DeviceId별 로그 파일이 정상적으로 생성되는지(log/client/1.log 등) 확인할 수 있습니다.

```bash
for i in 1 2 3 4 5; do curl -s http://localhost:9872/$i/; done
```

- 클라이언트 접속 로그: log/client/{DeviceId}.log
- 데이터 로그: log/{DeviceId}/YYYYMMDD.log

## 참고
- 개발 및 실행 관련 세부 내용은 PRD.md를 참고하세요.

---

## 최종 테스트 및 TDD

본 프로젝트는 PRD.md의 모든 요구사항을 충족하며, 아래의 자동화 테스트 스크립트로 최종 검증을 완료하였습니다.

### 자동화 테스트(tdd.sh) 사용법

1. 실행 권한 부여
   ```bash
   chmod +x tdd.sh
   ```

2. 테스트 실행
   ```bash
   ./tdd.sh
   ```

- 주요 테스트 항목:
  - 서버 실행 및 tmux 세션 관리
  - REST API 1~5번 응답 및 구조 확인
  - config.yaml 설정 반영 테스트
  - 로그 파일 생성 확인

테스트가 모두 통과하면 "✅ 모든 테스트 통과" 메시지가 출력됩니다.

---

**최종 테스트 완료(2025-06-14)**
