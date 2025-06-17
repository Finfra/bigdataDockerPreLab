#!/bin/bash
# bigdataDockerPreLab_restServer TDD 자동화 스크립트
# 1. tmux 세션(rs)에서 서버 실행 확인 및 재시작
# 2. REST API 1~5번 GET 요청 및 응답 구조 확인
# 3. config.yaml 임시 변경 후 값 반영 테스트
# 4. 로그 파일 생성 여부 확인
# 5. 테스트 결과 요약

set -e

SERVER_PORT=9872
SERVER_HOST=localhost
TMUX_SESSION=rs
CONFIG_FILE="config.yaml"
TMP_CONFIG_FILE="config_test.yaml"
LOG_DIR="log"
PASS_COUNT=0
FAIL_COUNT=0

function print_result() {
  echo "=============================="
  echo "테스트 통과: $PASS_COUNT"
  echo "테스트 실패: $FAIL_COUNT"
  echo "=============================="
  if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ 모든 테스트 통과"
    exit 0
  else
    echo "❌ 일부 테스트 실패"
    exit 1
  fi
}

function check_server_running() {
  tmux has-session -t $TMUX_SESSION 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "[INFO] tmux 세션($TMUX_SESSION) 없음. 새로 생성 및 서버 실행."
    tmux new-session -d -s $TMUX_SESSION "source venv/bin/activate && python server.py"
    sleep 2
  else
    # 이미 세션이 있으면 서버가 실행 중인지 확인
    tmux capture-pane -p -t $TMUX_SESSION:0 | grep -q "Running on"
    if [ $? -ne 0 ]; then
      echo "[INFO] tmux 세션은 있으나 서버가 실행 중이 아님. 서버 재시작."
      tmux send-keys -t $TMUX_SESSION:0 C-c
      sleep 1
      tmux send-keys -t $TMUX_SESSION:0 "source venv/bin/activate && python server.py" Enter
      sleep 2
    else
      echo "[INFO] 서버가 이미 실행 중입니다."
    fi
  fi
}

function test_api_response() {
  for i in {1..5}; do
    resp=$(curl -s http://$SERVER_HOST:$SERVER_PORT/$i/)
    echo "$resp" | grep -q '"DeviceId": '$i
    if [ $? -eq 0 ]; then
      echo "[PASS] DeviceId $i 응답 확인"
      PASS_COUNT=$((PASS_COUNT+1))
    else
      echo "[FAIL] DeviceId $i 응답 오류"
      FAIL_COUNT=$((FAIL_COUNT+1))
    fi
  done
}

function test_config_reflect() {
  # 기존 config 백업
  cp $CONFIG_FILE $TMP_CONFIG_FILE
  # sensor1의 mean을 100.0으로 임시 변경
  sed -i 's/\(sensor1:\s*{\s*mean:\s*\)[0-9.]\+/\1100.0/' $CONFIG_FILE
  tmux send-keys -t $TMUX_SESSION:0 C-c
  sleep 1
  tmux send-keys -t $TMUX_SESSION:0 "source venv/bin/activate && python server.py" Enter
  sleep 2
  resp=$(curl -s http://$SERVER_HOST:$SERVER_PORT/1/)
  sensor1_val=$(echo "$resp" | grep -o '"sensor1":[0-9.]\+' | head -1 | cut -d: -f2)
  if (( $(echo "$sensor1_val > 90" | bc -l) )); then
    echo "[PASS] config.yaml 반영 테스트(sensor1 mean=100)"
    PASS_COUNT=$((PASS_COUNT+1))
  else
    echo "[FAIL] config.yaml 반영 테스트(sensor1 mean=100)"
    FAIL_COUNT=$((FAIL_COUNT+1))
  fi
  # config 원복
  mv $TMP_CONFIG_FILE $CONFIG_FILE
  tmux send-keys -t $TMUX_SESSION:0 C-c
  sleep 1
  tmux send-keys -t $TMUX_SESSION:0 "source venv/bin/activate && python server.py" Enter
  sleep 2
}

function test_log_files() {
  for i in {1..5}; do
    curl -s http://$SERVER_HOST:$SERVER_PORT/$i/ > /dev/null
    sleep 0.5
    if [ -f "$LOG_DIR/client/$i.log" ]; then
      echo "[PASS] log/client/$i.log 생성 확인"
      PASS_COUNT=$((PASS_COUNT+1))
    else
      echo "[FAIL] log/client/$i.log 생성 안됨"
      FAIL_COUNT=$((FAIL_COUNT+1))
    fi
  done
}

echo "===== bigdataDockerPreLab_restServer TDD 자동화 ====="
check_server_running
test_api_response
test_config_reflect
test_log_files
print_result
