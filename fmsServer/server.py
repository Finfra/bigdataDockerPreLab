import web
import json
from datetime import datetime
import yaml
import numpy as np
import random
import os

urls = (
    '/(\\d+)/', 'DeviceHandler'
)

app = web.application(urls, globals())

# config.yaml 로드 함수
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

# 센서/모터 값 생성 함수
def generate_value(cfg):
    # -1 출력 확률
    if random.random() < cfg.get("minus_one_prob", 0):
        return -1
    # 이상치 확률
    if random.random() < cfg.get("outlier_prob", 0):
        # 평균에서 3~5배 표준편차 벗어난 값 생성
        sign = random.choice([-1, 1])
        return round(cfg["mean"] + sign * random.uniform(3, 5) * cfg["stddev"], 2)
    # 정상값
    return round(np.random.normal(cfg["mean"], cfg["stddev"]), 2)

class DeviceHandler:
    def GET(self, device_id):
        try:
            device_id = int(device_id)
            if device_id < 1 or device_id > 5:
                raise ValueError
        except ValueError:
            return web.notfound("Invalid DeviceId")
        # config.yaml 로드
        config = load_config()
        device_cfg = next((d for d in config["devices"] if d["id"] == device_id), None)
        if not device_cfg:
            return web.notfound("Device config not found")
        # 센서/모터 값 생성
        sensors = {}
        for k, v in device_cfg["sensors"].items():
            sensors[k] = generate_value(v)
        motors = {}
        for k, v in device_cfg["motors"].items():
            motors[k] = generate_value(v)
        now = datetime.utcnow()
        response = {
            "time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "DeviceId": device_id,
            **sensors,
            **motors,
            "isFail": False
        }

        # 로그 디렉토리 생성
        os.makedirs(f"log/client", exist_ok=True)
        os.makedirs(f"log/{device_id}", exist_ok=True)

        # 클라이언트 접속 로그 기록
        client_ip = web.ctx.get('ip', 'unknown')
        log_time = now.strftime('%Y%m%d_%H%M%S')
        log_filename = f"log/client/{client_ip}_{log_time}.log"
        with open(log_filename, "a") as f:
            f.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')}, {client_ip}, {response['time']}, DeviceId={device_id}\n")

        # 데이터 로그 기록 (날짜별)
        log_filename = now.strftime("%Y%m%d") + ".log"
        with open(f"log/{device_id}/{log_filename}", "a") as f:
            f.write(json.dumps(response, ensure_ascii=False) + "\n")

        web.header('Content-Type', 'application/json')
        return json.dumps(response)

if __name__ == "__main__":
    from web import httpserver
    httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 9872))
