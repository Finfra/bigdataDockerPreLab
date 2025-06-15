#!/bin/bash
# Kafka 클러스터 설치 스크립트

# Kafka 다운로드 및 설치
install_kafka() {
    echo "Installing Kafka..."
    dnf install -y java-1.8.0-openjdk-devel 
    cd /df
    wget https://dlcdn.apache.org/kafka/3.9.0/kafka_2.12-3.9.0.tgz
    tar -xvf kafka_2.12-3.9.0.tgz
    mv kafka_2.12-3.9.0 /opt/kafka
    echo 'export PATH=$PATH:/opt/kafka/bin' >> /etc/bashrc
    source /etc/bashrc
    
    # Python 패키지 설치
    pip3 install confluent-kafka
    pip3 install kafka-python
}

# Kafka 브로커 설정
configure_broker() {
    local broker_id=$1
    echo "Configuring broker $broker_id..."
    
    cat >> /opt/kafka/config/server.properties <<EOF
broker.id=${broker_id}
zookeeper.connect=s1:2181
log.dirs=/tmp/kafka-logs
listeners=PLAINTEXT://0.0.0.0:9092
EOF
}

# 사용법
echo "Usage: $0 [install|configure] [broker_id]"
if [ "$1" = "install" ]; then
    install_kafka
elif [ "$1" = "configure" ]; then
    configure_broker $2
fi
