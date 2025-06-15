# 8. Spark을 활용한 데이터 변환 로직 구현
**챕터 7 스트리밍 데이터를 기반으로 한 고급 Spark 데이터 변환 및 분석**

## 통합 데이터 변환 파이프라인
### 8.1 스트리밍 데이터 기반 변환
* **데이터 소스**: 챕터 7에서 수집된 Kafka 스트리밍 데이터
* **실시간 변환**: Spark Streaming + 배치 처리 하이브리드
* **저장소 연동**: HDFS 기반 레이어드 데이터 아키텍처
* **처리 위치**: s1(Master) + s2,s3(Workers) 분산 처리

### 8.2 데이터 변환 아키텍처
```
Kafka Stream (i1) → Spark Streaming (s1) → 실시간 변환 → HDFS 저장
                                       ↓
                  배치 변환 (s1,s2,s3) → 고급 분석 → 결과 저장
```

**계층별 데이터 구조**:
- **Raw Layer**: `/fms/raw/` - 원시 스트리밍 데이터
- **Processed Layer**: `/fms/processed/` - 기본 변환 데이터  
- **Analytics Layer**: `/fms/analytics/` - 고급 분석 결과
- **ML Layer**: `/fms/ml-features/` - 머신러닝 피처

## Spark SQL 기반 실시간 변환
### 8.3 SQL 템플릿 기반 변환 엔진
```sql
-- 센서 데이터 정규화 및 품질 검증
WITH cleaned_data AS (
  SELECT 
    device_id,
    location,
    timestamp,
    -- 센서 값 정규화
    CASE 
      WHEN sensors.temperature BETWEEN 20 AND 80 THEN sensors.temperature
      ELSE NULL 
    END as temperature,
    -- 품질 점수 계산
    (CASE WHEN sensors.temperature IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN sensors.humidity BETWEEN 20 AND 90 THEN 1 ELSE 0 END +
     CASE WHEN sensors.vibration > 0 THEN 1 ELSE 0 END) / 3.0 as quality_score
  FROM streaming_data
),
-- 시계열 통계 계산
time_series_stats AS (
  SELECT *,
    -- 이동평균 (1시간 윈도우)
    AVG(temperature) OVER (
      PARTITION BY device_id 
      ORDER BY timestamp 
      RANGE BETWEEN INTERVAL 1 HOUR PRECEDING AND CURRENT ROW
    ) as temp_1h_avg,
    -- 이상 탐지 (Z-Score)
    ABS(temperature - AVG(temperature) OVER (PARTITION BY device_id)) / 
    STDDEV(temperature) OVER (PARTITION BY device_id) as temp_zscore
  FROM cleaned_data
)
SELECT * FROM time_series_stats
WHERE quality_score >= 0.7
```

### 8.4 실시간 변환 실행기
**변환 스크립트**: [`src/realtime-transformer.sh`](src/realtime-transformer.sh)

```bash
# s1에서 실행 - 실시간 변환 파이프라인
bash /df/realtime-transformer.sh start

# 특정 시간 범위 변환
bash /df/realtime-transformer.sh batch 2024-01-15 2024-01-16

# 변환 상태 모니터링
bash /df/realtime-transformer.sh monitor
```

## DataFrame API 고급 변환
### 8.5 PySpark 변환 엔진
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

# 고급 피처 엔지니어링
def advanced_feature_engineering(df):
    # 시간 기반 피처
    df_enriched = df.withColumn("hour", hour("timestamp")) \
                   .withColumn("day_of_week", dayofweek("timestamp")) \
                   .withColumn("is_weekend", when(dayofweek("timestamp").isin([1,7]), 1).otherwise(0))
    
    # 센서 간 상관관계 피처
    df_enriched = df_enriched.withColumn("temp_humidity_ratio", 
                                        col("sensors.temperature") / col("sensors.humidity")) \
                            .withColumn("efficiency_power_ratio",
                                        col("efficiency") / col("sensors.power_consumption"))
    
    # 롤링 통계 (시간 윈도우)
    window_1h = Window.partitionBy("device_id").orderBy("timestamp") \
                      .rangeBetween(-3600, 0)  # 1시간
    
    df_enriched = df_enriched.withColumn("temp_1h_avg", avg("sensors.temperature").over(window_1h)) \
                            .withColumn("temp_1h_std", stddev("sensors.temperature").over(window_1h))
    
    return df_enriched
```

### 8.6 배치 변환 처리기
**배치 변환 스크립트**: [`src/batch-transformer.py`](src/batch-transformer.py)

## 커스텀 UDF 구현
### 8.7 비즈니스 로직 UDF
```python
from pyspark.sql.functions import udf
from pyspark.sql.types import *
import numpy as np

# 장비 상태 분류 UDF
@udf(returnType=StringType())
def classify_equipment_status(temperature, vibration, efficiency):
    """장비 상태를 4단계로 분류"""
    if temperature > 70 or vibration > 2.5 or efficiency < 60:
        return "CRITICAL"
    elif temperature > 60 or vibration > 2.0 or efficiency < 70:
        return "WARNING"
    elif temperature > 50 or vibration > 1.5 or efficiency < 80:
        return "CAUTION"
    else:
        return "NORMAL"

# 이상 점수 계산 UDF
@udf(returnType=DoubleType())
def calculate_anomaly_score(temp, humidity, vibration, efficiency):
    """다차원 이상 점수 계산"""
    temp_score = abs(temp - 50) / 30  # 50도 기준 정규화
    humidity_score = abs(humidity - 60) / 40  # 60% 기준
    vibration_score = max(0, vibration - 1.0) / 2.0  # 1.0 이상만 점수
    efficiency_score = max(0, 85 - efficiency) / 30  # 85% 미만만 점수
    
    return float(temp_score + humidity_score + vibration_score + efficiency_score)

# 예측 유지보수 점수 UDF  
@udf(returnType=StructType([
    StructField("maintenance_score", DoubleType(), False),
    StructField("risk_level", StringType(), False),
    StructField("recommended_action", StringType(), False)
]))
def predict_maintenance_need(temp, vibration, efficiency, operation_hours):
    """예측 유지보수 필요도 계산"""
    # 가중치 기반 점수 계산
    temp_weight = min(temp / 80, 1.0) * 0.3
    vibration_weight = min(vibration / 3.0, 1.0) * 0.4
    efficiency_weight = max(0, (90 - efficiency) / 30) * 0.3
    
    maintenance_score = temp_weight + vibration_weight + efficiency_weight
    
    # 리스크 레벨 결정
    if maintenance_score > 0.8:
        risk_level = "HIGH"
        action = "IMMEDIATE_MAINTENANCE"
    elif maintenance_score > 0.6:
        risk_level = "MEDIUM" 
        action = "SCHEDULE_MAINTENANCE"
    elif maintenance_score > 0.4:
        risk_level = "LOW"
        action = "MONITOR_CLOSELY"
    else:
        risk_level = "NORMAL"
        action = "ROUTINE_CHECK"
    
    return (float(maintenance_score), risk_level, action)
```

## 데이터 품질 검증 시스템
### 8.8 실시간 품질 모니터링
```python
class DataQualityValidator:
    def __init__(self, spark):
        self.spark = spark
        
    def validate_completeness(self, df):
        """완전성 검증 - NULL 값 비율"""
        total_count = df.count()
        quality_metrics = {}
        
        for col_name in df.columns:
            null_count = df.filter(col(col_name).isNull()).count()
            completeness = (total_count - null_count) / total_count
            quality_metrics[f"{col_name}_completeness"] = completeness
            
        return quality_metrics
    
    def validate_validity(self, df):
        """유효성 검증 - 데이터 범위 및 타입"""
        validity_checks = {
            "temperature_valid": df.filter(
                (col("sensors.temperature") >= 20) & 
                (col("sensors.temperature") <= 80)
            ).count() / df.count(),
            
            "humidity_valid": df.filter(
                (col("sensors.humidity") >= 20) & 
                (col("sensors.humidity") <= 90)
            ).count() / df.count(),
            
            "efficiency_valid": df.filter(
                (col("efficiency") >= 30) & 
                (col("efficiency") <= 100)
            ).count() / df.count()
        }
        
        return validity_checks
    
    def validate_consistency(self, df):
        """일관성 검증 - 논리적 관계"""
        consistency_checks = {
            "timestamp_order": df.filter(
                col("timestamp") > "2020-01-01"
            ).count() / df.count(),
            
            "device_location_consistency": df.groupBy("device_id") \
                .agg(countDistinct("location")) \
                .filter(col("count(DISTINCT location)") == 1) \
                .count() / df.select("device_id").distinct().count()
        }
        
        return consistency_checks
    
    def generate_quality_report(self, df):
        """종합 품질 리포트 생성"""
        completeness = self.validate_completeness(df)
        validity = self.validate_validity(df)
        consistency = self.validate_consistency(df)
        
        overall_score = (
            sum(completeness.values()) / len(completeness) * 0.3 +
            sum(validity.values()) / len(validity) * 0.4 +
            sum(consistency.values()) / len(consistency) * 0.3
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_records": df.count(),
            "overall_quality_score": overall_score,
            "quality_grade": "A" if overall_score > 0.9 else "B" if overall_score > 0.8 else "C",
            "completeness": completeness,
            "validity": validity,
            "consistency": consistency,
            "recommendations": self._generate_recommendations(overall_score, completeness, validity)
        }
```

### 8.9 자동 품질 개선
```python
def auto_data_repair(df):
    """자동 데이터 복구 및 개선"""
    # 1. 이상치 자동 수정
    df_repaired = df.withColumn("sensors.temperature",
        when(col("sensors.temperature") > 100, 100)
        .when(col("sensors.temperature") < 0, 0)
        .otherwise(col("sensors.temperature"))
    )
    
    # 2. 결측값 자동 보간
    device_averages = df.groupBy("device_id").agg(
        avg("sensors.temperature").alias("avg_temp"),
        avg("sensors.humidity").alias("avg_humidity")
    )
    
    df_repaired = df_repaired.join(device_averages, "device_id") \
        .withColumn("sensors.temperature",
            when(col("sensors.temperature").isNull(), col("avg_temp"))
            .otherwise(col("sensors.temperature"))
        )
    
    # 3. 데이터 타입 자동 변환
    df_repaired = df_repaired.withColumn("efficiency", 
        col("efficiency").cast("integer")
    )
    
    return df_repaired.drop("avg_temp", "avg_humidity")
```

## 변환 파이프라인 실행
### 8.10 통합 변환 워크플로우
```bash
# 1. 실시간 스트리밍 변환 시작
docker exec -it s1 bash
bash /df/realtime-transformer.sh start

# 2. 배치 변환 (기존 데이터)
bash /df/batch-transformer.sh process /fms/raw/2024/01/15

# 3. 품질 검증 실행
bash /df/quality-validator.sh validate /fms/processed/latest

# 4. 변환 결과 확인
bash /df/transformation-monitor.sh
```

### 8.11 변환 결과 활용
```bash
# 변환된 데이터 확인
hadoop fs -ls /fms/processed/

# ML 피처 데이터 확인  
hadoop fs -ls /fms/ml-features/

# 품질 리포트 확인
hadoop fs -cat /fms/quality-reports/latest/quality_summary.json
```

## 성능 최적화 및 모니터링
### 8.12 변환 성능 튜닝
* **파티션 최적화**: 장비별, 날짜별 파티셔닝
* **캐시 전략**: 중간 결과 메모리 캐싱
* **조인 최적화**: 브로드캐스트 조인 활용
* **컬럼 프루닝**: 필요한 컬럼만 선택적 로딩

### 8.13 변환 모니터링
* **처리량 추적**: 시간당 변환 레코드 수
* **지연시간 모니터링**: 데이터 수집부터 변환 완료까지
* **리소스 사용률**: CPU, 메모리, 디스크 I/O
* **품질 트렌드**: 시간별 데이터 품질 변화

## 핵심 기술 특징
* **실시간 + 배치**: 하이브리드 처리 아키텍처
* **자동 품질 관리**: 지속적인 데이터 품질 모니터링
* **확장 가능**: 새로운 변환 로직 쉽게 추가
* **모니터링 통합**: Grafana 대시보드 연동

## 주요 산출물
* 실시간 스트리밍 변환 엔진
* 배치 처리 기반 고급 분석
* 커스텀 UDF 라이브러리
* 자동화된 데이터 품질 시스템
* ML 준비된 피처 데이터셋

---

## 실습 가이드

### 실습 1: 실시간 변환 파이프라인
```bash
# 1. 스트리밍 데이터 생성 (i1)
docker exec -it i1 bash
bash /df/kafka-producer.sh continuous

# 2. 실시간 변환 시작 (s1)
docker exec -it s1 bash  
bash /df/realtime-transformer.sh start

# 3. 변환 결과 모니터링
bash /df/transformation-monitor.sh
```

### 실습 2: 배치 변환 및 품질 검증
```bash
# 1. 배치 변환 실행
bash /df/batch-transformer.sh process-all

# 2. 품질 검증
bash /df/quality-validator.sh comprehensive

# 3. 결과 확인
hadoop fs -ls /fms/analytics/
```

### 실습 3: 커스텀 UDF 개발
```bash
# 1. UDF 개발 환경 설정
bash /df/setup-udf-env.sh

# 2. 샘플 UDF 테스트
bash /df/test-custom-udfs.sh

# 3. 프로덕션 배포
bash /df/deploy-udfs.sh
```

**다음 챕터**: [9. 통합 파이프라인 구축](../09-integrated-pipeline/) - 전체 데이터 파이프라인 통합 및 최적화
