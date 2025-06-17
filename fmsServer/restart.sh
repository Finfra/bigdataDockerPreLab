#!/bin/bash
# stop.sh와 start.sh를 연속 실행
LOGDIR="log/admin"
DATE=$(date +"%Y%m%d_%H%M%S")
mkdir -p $LOGDIR

./stop.sh
sleep 1
./start.sh

echo "[$(date +"%Y-%m-%d %H:%M:%S")] restart.sh 실행" >> $LOGDIR/${DATE}_restart.log
