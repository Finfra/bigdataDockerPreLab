#!/bin/bash
# tmux 세션 rs 종료
SESSION="rs"
LOGDIR="log/admin"
DATE=$(date +"%Y%m%d_%H%M%S")
mkdir -p $LOGDIR

if tmux has-session -t $SESSION 2>/dev/null; then
  tmux kill-session -t $SESSION
  echo "[$(date +"%Y-%m-%d %H:%M:%S")] stop.sh 실행" >> $LOGDIR/${DATE}_stop.log
else
  echo "[$(date +"%Y-%m-%d %H:%M:%S")] stop.sh 실행(세션 없음)" >> $LOGDIR/${DATE}_stop.log
fi
