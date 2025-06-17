#!/bin/bash
# tmux 세션 rs에서 venv 활성화 후 서버 실행
SESSION="rs"
LOGDIR="log/admin"
DATE=$(date +"%Y%m%d_%H%M%S")
mkdir -p $LOGDIR

if ! tmux has-session -t $SESSION 2>/dev/null; then
  tmux new-session -d -s $SESSION
fi

tmux send-keys -t $SESSION "source venv/bin/activate && python server.py" C-m

echo "[$(date +"%Y-%m-%d %H:%M:%S")] start.sh 실행" >> $LOGDIR/${DATE}_start.log
