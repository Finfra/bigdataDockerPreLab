# 6. Docker 기반 Hadoop/Spark 클러스터 구축
**Finfra/hadoopInstall** 검증된 방법을 기반으로 한 완전한 빅데이터 플랫폼 구축

## 전체 시스템 아키텍처 및 컨테이너 구성
### 6.1 컨테이너별 역할 정의
* **i1 (Management & Monitoring Services)**
  - **Kafka Producer**: 센서 데이터 수집 및 Kafka로 전송
  - **Grafana**: 모니터링 대시보드 및 시각화 (:3000)
  - **Prometheus**: 메트릭 수집 및 저장 (:9090)
  - **n8n**: 워크플로우 자동화 및 ETL 처리 (:5678)
  - **Ansible**: 클러스터 관리 및 자동화

* **s1 (Master Node + Kafka Consumer)**
  - **Kafka Consumer**: Kafka에서 데이터 수신 및 실시간 처리
  - **NameNode**: HDFS 메타데이터 관리 (:9870)
  - **ResourceManager**: YARN 리소스 관리 (:8088)
  - **Spark Master**: Spark 클러스터 마스터 (:8080)
  - **MapReduce HistoryServer**: Job History 관리 (:19888)

* **s2, s3 (Worker Nodes)**
  - **DataNode**: HDFS 데이터 저장 및 관리
  - **NodeManager**: YARN 워커 노드
  - **Spark Worker**: Spark 작업 실행

## 환경 준비 및 컨테이너 구축
### 6.2 기본 환경 구성
```bash
# 1. 프로젝트 클론 (검증된 환경)
git clone https://github.com/Finfra/hadoopInstall.git
cd hadoopInstall

# 2. 필수 설치 파일 준비 (/df/i1/ 디렉터리에 배치)
# Hadoop 3.3.6
cd /df/i1/
wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz

# Spark 3.4.4
wget https://dlcdn.apache.org/spark/spark-3.4.4/spark-3.4.4-bin-hadoop3.tgz

# 3. 컨테이너 환경 자동 구성 (Oracle Linux 9 기반)
. do.sh
```

### 6.3 컨테이너 네트워크 및 구성
* **베이스 이미지**: Oracle Linux 9 (엔터프라이즈급 안정성)
* **네트워크**: Docker Compose 기반 내부 네트워크
* **볼륨 구성**: `/df` 디렉터리 공유를 통한 통합 관리
* **SSH 연결**: 자동 키 교환을 통한 무패스워드 접근

## Hadoop 클러스터 자동 설치
### 6.4 Ansible 기반 Hadoop 설치
```bash
# 1. i1 컨테이너 접속 (관리 노드)
docker exec -it i1 bash

# 2. Hadoop 클러스터 자동 설치
ansible-playbook --flush-cache -i /df/ansible-hadoop/hosts /df/ansible-hadoop/hadoop_install.yml
```

**설치 과정**:
- Java 11 OpenJDK 환경 구성
- Hadoop 3.3.6 바이너리 배포
- 클러스터 설정 파일 자동 생성
- SSH 키 교환 및 권한 설정
- NameNode 포맷 및 초기화

### 6.5 Spark 클러스터 설치
```bash
# i1 컨테이너에서 Spark 설치
ansible-playbook --flush-cache -i /df/ansible-spark/hosts /df/ansible-spark/spark_install.yml -e ansible_python_interpreter=/usr/bin/python3.12
```

**설치 구성**:
- Spark 3.4.4 (Hadoop 3 호환)
- Master-Worker 구조 설정
- PySpark 환경 구성
- Event Log 및 History Server 설정

## 통합 클러스터 시작/정지 관리
### 6.6 전체 서비스 시작 (i1에서 실행)
```bash
# 검증된 시작 스크립트 (startAll alias)

# 1단계: HDFS 클러스터 시작
echo "Starting HDFS services..."
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup hdfs --daemon start namenode &" -u root
sleep 10

ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "nohup hdfs --daemon start datanode &" -u root
sleep 10

# 2단계: YARN 클러스터 시작
echo "Starting YARN services..."
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup yarn --daemon start resourcemanager &" -u root
sleep 5

ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "nohup yarn --daemon start nodemanager &" -u root
sleep 5

# 3단계: MapReduce HistoryServer 시작
echo "Starting MapReduce HistoryServer..."
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup mapred --daemon start historyserver &" -u root
sleep 5

# 4단계: Spark 클러스터 시작
echo "Starting Spark cluster..."
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "su - hadoop -c '\$SPARK_HOME/sbin/start-all.sh'" -u root

echo "=== All services started successfully ==="
```

### 6.7 전체 서비스 정지 (i1에서 실행)
```bash
# 안전한 종료 순서 (stopAll alias)

# 1단계: Spark 클러스터 정지
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "su - hadoop -c '\$SPARK_HOME/sbin/stop-all.sh'" -u root

# 2단계: MapReduce HistoryServer 정지
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "mapred --daemon stop historyserver" -u root

# 3단계: YARN 서비스 정지
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "yarn --daemon stop nodemanager" -u root
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "yarn --daemon stop resourcemanager" -u root

# 4단계: HDFS 서비스 정지
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "hdfs --daemon stop datanode" -u root
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "hdfs --daemon stop namenode" -u root

echo "=== All services stopped safely ==="
```

## HDFS 및 MapReduce 검증 테스트
### 6.8 HDFS 기본 기능 테스트 (s1에서 실행)
```bash
# 1. HDFS 상태 확인
hadoop fs -ls /

# 2. 테스트 디렉터리 및 파일 생성
hadoop fs -mkdir -p /data
echo "Hadoop HDFS Test Data - $(date)" > test.txt
hadoop fs -put test.txt /data/

# 3. 파일 확인 및 읽기
hadoop fs -ls /data
hadoop fs -cat /data/test.txt

# 4. 클러스터 상태 확인
hdfs dfsadmin -report
```

### 6.9 MapReduce WordCount 테스트 (s1에서 실행)
```bash
# 1. 컴파일 환경 준비
cd /df
mkdir -p wordcount_classes

# 2. WordCount 예제 컴파일
javac -classpath $(hadoop classpath) -d wordcount_classes WordCount.java
jar -cvf WordCount.jar -C wordcount_classes/ .

# 3. HDFS 입력 데이터 준비
hdfs dfs -mkdir -p /user/hadoop/input
hdfs dfs -put input.txt /user/hadoop/input/

# 4. Safe Mode 해제 (필요시)
if hdfs dfsadmin -safemode get | grep -q "Safe mode is ON"; then
    hdfs dfsadmin -safemode leave
    echo "Safe mode disabled"
fi

# 5. MapReduce 작업 실행 (기존 출력 제거 후)
hdfs dfs -rm -r /user/hadoop/output 2>/dev/null || true
hadoop jar WordCount.jar WordCount /user/hadoop/input /user/hadoop/output

# 6. 결과 확인
echo "=== WordCount Results ==="
hdfs dfs -cat /user/hadoop/output/part-r-00000
```

## Spark 클러스터 관리 및 테스트
### 6.10 Spark 클러스터 상태 관리
```bash
# Spark 서비스 재시작 (s1에서)
$SPARK_HOME/sbin/stop-all.sh
sleep 5
$SPARK_HOME/sbin/start-all.sh

# Spark 클러스터 상태 확인
$SPARK_HOME/bin/spark-submit --master spark://s1:7077 --class org.apache.spark.examples.SparkPi $SPARK_HOME/examples/jars/spark-examples_*.jar 2
```

### 6.11 PySpark 분산 처리 테스트 (s1에서)
```bash
# PySpark 쉘 실행
pyspark
```

```python
# PySpark 클러스터 검증 코드
from pyspark import SparkContext, SparkConf

# Spark 설정 (검증된 구성)
conf = SparkConf().setAppName("ClusterDistributionTest").setMaster("spark://s1:7077")
sc = SparkContext(conf=conf)

print("=== Spark 클러스터 분산 처리 테스트 ===")

# 1. 기본 RDD 연산 테스트
data = range(1000)
rdd = sc.parallelize(data, 10)
result = rdd.map(lambda x: x * 2).filter(lambda x: x > 100).count()
print(f"필터링된 데이터 개수: {result}")

# 2. 노드별 파티션 분산 확인
def log_partition(index, iterator):
    import socket
    hostname = socket.gethostname()
    count = sum(1 for _ in iterator)
    print(f"파티션 {index} -> 호스트 {hostname}: {count}개 요소")
    return [count]

partition_rdd = sc.parallelize(range(300), 6)
partition_results = partition_rdd.mapPartitionsWithIndex(log_partition).collect()
print(f"파티션 분산 결과: {partition_results}")

# 3. Kafka 연동을 위한 HDFS 데이터 처리 (s1의 Consumer 역할 시뮬레이션)
try:
    # HDFS에서 데이터 읽기
    text_rdd = sc.textFile("hdfs://s1:8020/user/hadoop/input/input.txt")
    
    # 실시간 스트림 처리 시뮬레이션 (단어 카운트)
    words = text_rdd.flatMap(lambda line: line.split(" "))
    word_counts = words.map(lambda word: (word, 1)).reduceByKey(lambda a, b: a + b)
    
    # 결과를 HDFS에 저장 (Consumer 처리 결과)
    hdfs_output_path = "hdfs://s1:8020/user/hadoop/spark_processed"
    word_counts.saveAsTextFile(hdfs_output_path)
    
    print("Kafka Consumer 시뮬레이션: 데이터 처리 완료")
    print(f"결과 저장 경로: {hdfs_output_path}")
    
except Exception as e:
    print(f"HDFS 연동 테스트 실패: {e}")

print("=== 테스트 완료 ===")
sc.stop()
```

## 모니터링 및 운영 관리
### 6.12 주요 웹 UI 접속 정보
| 서비스               | 포트  | 접속 URL                    | 용도                     |
| -------------------- | ----- | --------------------------- | ------------------------ |
| Hadoop NameNode      | 9870  | http://localhost:9870       | HDFS 클러스터 관리       |
| YARN ResourceManager | 8088  | http://localhost:8088       | YARN 리소스 관리         |
| Spark Master         | 8080  | http://localhost:8080       | Spark 클러스터 상태      |
| MapReduce History    | 19888 | http://localhost:19888      | Job History 확인         |
| Grafana              | 3000  | http://localhost:3000       | 통합 모니터링 대시보드   |
| Prometheus           | 9090  | http://localhost:9090       | 메트릭 수집 및 조회      |
| n8n                  | 5678  | http://localhost:5678       | 워크플로우 자동화        |

### 6.13 종합 클러스터 상태 점검 스크립트
```bash
# 어느 컨테이너에서든 실행 가능한 헬스체크
bash /df/cluster-health-check.sh
```

**점검 항목**:
- 모든 컨테이너 상태 확인
- Hadoop/Spark 서비스 상태
- HDFS 클러스터 건강성
- YARN 리소스 상태
- Kafka/모니터링 서비스 상태
- 웹 UI 접근성 확인

## 실제 운영 시나리오
### 6.14 Kafka Producer/Consumer 통합 테스트
```bash
# 1. i1에서 Kafka Producer로 데이터 생성
docker exec -it i1 bash
# (Kafka Producer 스크립트 실행)

# 2. s1에서 Kafka Consumer로 데이터 수신 및 Spark 처리
docker exec -it s1 bash
# (Consumer 스크립트 + Spark 스트리밍 처리)

# 3. Grafana에서 실시간 모니터링
# http://localhost:3000 접속하여 대시보드 확인
```

## 문제 해결 및 운영 팁
### 6.15 일반적인 문제 해결
* **컨테이너 네트워크 문제**
```bash
# 전체 환경 재구성
docker-compose down
. do.sh
```

* **Safe Mode 해결**
```bash
# Safe mode 강제 해제
hdfs dfsadmin -safemode leave
hdfs dfsadmin -safemode get  # 상태 확인
```

* **포트 충돌 해결**
```bash
# 사용 중인 포트 확인
docker ps --format "table {{.Names}}\t{{.Ports}}"
netstat -tulpn | grep LISTEN
```

* **로그 확인**
```bash
# 각 서비스 로그 위치
# Hadoop: $HADOOP_HOME/logs/
# Spark: $SPARK_HOME/logs/
# Docker: docker logs [container_name]
```

## 핵심 특징 및 장점
* **검증된 안정성**: Finfra 프로덕션 환경에서 검증된 구성
* **완전 자동화**: Ansible 기반 무인 설치 및 관리
* **통합 모니터링**: Grafana + Prometheus 실시간 모니터링
* **실시간 처리**: Kafka + Spark 스트리밍 파이프라인
* **확장성**: 수평 확장 가능한 마이크로서비스 구조

## 주요 산출물
* Oracle Linux 9 기반 컨테이너 환경
* Ansible 자동화 설치 플레이북
* 완전 통합된 빅데이터 플랫폼
* 실시간 모니터링 및 알림 시스템
* Kafka 기반 스트리밍 데이터 파이프라인

---

## 실습 가이드

### 실습 1: 전체 환경 구축
```bash
# 1. 프로젝트 환경 구성
git clone https://github.com/Finfra/hadoopInstall.git
cd hadoopInstall

# 2. 필수 파일 다운로드 및 배치
wget -O hadoop-3.3.6.tar.gz https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
wget -O spark-3.4.4-bin-hadoop3.tgz https://dlcdn.apache.org/spark/spark-3.4.4/spark-3.4.4-bin-hadoop3.tgz

# 3. 컨테이너 환경 생성
. do.sh
```

### 실습 2: 클러스터 설치 및 시작
```bash
# 1. Hadoop/Spark 설치
docker exec -it i1 bash
ansible-playbook --flush-cache -i /df/ansible-hadoop/hosts /df/ansible-hadoop/hadoop_install.yml
ansible-playbook --flush-cache -i /df/ansible-spark/hosts /df/ansible-spark/spark_install.yml -e ansible_python_interpreter=/usr/bin/python3.12

# 2. 전체 클러스터 시작 (startAll 명령)
# (위의 6.6 시작 스크립트 실행)
```

### 실습 3: 기능 검증
```bash
# 1. s1 컨테이너에서 HDFS 테스트
docker exec -it s1 bash
bash /df/test-hdfs.sh

# 2. MapReduce 테스트
bash /df/test-mapreduce.sh

# 3. Spark 클러스터 테스트
bash /df/test-spark.sh
```

### 실습 4: 웹 UI 모니터링
* **Hadoop 관리**: http://localhost:9870
* **YARN 리소스**: http://localhost:8088
* **Spark 클러스터**: http://localhost:8080
* **통합 모니터링**: http://localhost:3000

### 주의사항
* 모든 서비스가 순차적으로 시작되어야 함
* 충분한 메모리 (최소 8GB) 확보 필요
* 방화벽 및 포트 충돌 사전 확인
* 컨테이너 간 네트워크 연결 상태 점검
