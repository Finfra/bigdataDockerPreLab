# spark-apps/fms_transformations.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

class FMSDataTransformations:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("FMS-Data-Transformations") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .getOrCreate()
        
        # 임시 뷰 등록을 위한 스키마 정의
        self.setup_sql_functions()

    def setup_sql_functions(self):
        """SQL 함수 및 뷰 설정"""
        # 커스텀 SQL 함수 등록
        self.spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW sensor_thresholds AS
        SELECT 'sensor1' as sensor_name, 0.0 as min_val, 100.0 as max_val, 'temperature' as unit
        UNION ALL
        SELECT 'sensor2' as sensor_name, 0.0 as min_val, 100.0 as max_val, 'humidity' as unit
        UNION ALL  
        SELECT 'sensor3' as sensor_name, 0.0 as min_val, 150.0 as max_val, 'pressure' as unit
        """)

    def basic_data_cleaning(self, df):
        """기본 데이터 정제"""
        # 임시 뷰 생성
        df.createOrReplaceTempView("raw_fms_data")
        
        cleaned_df = self.spark.sql("""
        SELECT 
            DeviceId,
            CAST(time AS TIMESTAMP) as event_time,
            CASE 
                WHEN sensor1 BETWEEN 0 AND 100 THEN sensor1 
                ELSE NULL 
            END as sensor1_clean,
            CASE 
                WHEN sensor2 BETWEEN 0 AND 100 THEN sensor2 
                ELSE NULL 
            END as sensor2_clean,
            CASE 
                WHEN sensor3 BETWEEN 0 AND 150 THEN sensor3 
                ELSE NULL 
            END as sensor3_clean,
            CASE 
                WHEN motor1 BETWEEN 0 AND 2000 THEN motor1 
                ELSE NULL 
            END as motor1_clean,
            CASE 
                WHEN motor2 BETWEEN 0 AND 1500 THEN motor2 
                ELSE NULL 
            END as motor2_clean,
            CASE 
                WHEN motor3 BETWEEN 0 AND 1800 THEN motor3 
                ELSE NULL 
            END as motor3_clean,
            isFail,
            current_timestamp() as processed_at
        FROM raw_fms_data
        WHERE DeviceId IS NOT NULL 
          AND time IS NOT NULL
        """)
        
        return cleaned_df

    def calculate_device_statistics(self, df):
        """장비별 통계 계산"""
        df.createOrReplaceTempView("clean_fms_data")
        
        stats_df = self.spark.sql("""
        SELECT 
            DeviceId,
            DATE(event_time) as date,
            HOUR(event_time) as hour,
            
            -- 센서 통계
            AVG(sensor1_clean) as sensor1_avg,
            MIN(sensor1_clean) as sensor1_min,
            MAX(sensor1_clean) as sensor1_max,
            STDDEV(sensor1_clean) as sensor1_stddev,
            
            AVG(sensor2_clean) as sensor2_avg,
            MIN(sensor2_clean) as sensor2_min,
            MAX(sensor2_clean) as sensor2_max,
            STDDEV(sensor2_clean) as sensor2_stddev,
            
            AVG(sensor3_clean) as sensor3_avg,
            MIN(sensor3_clean) as sensor3_min,
            MAX(sensor3_clean) as sensor3_max,
            STDDEV(sensor3_clean) as sensor3_stddev,
            
            -- 모터 통계
            AVG(motor1_clean) as motor1_avg,
            MIN(motor1_clean) as motor1_min,
            MAX(motor1_clean) as motor1_max,
            
            AVG(motor2_clean) as motor2_avg,
            MIN(motor2_clean) as motor2_min,
            MAX(motor2_clean) as motor2_max,
            
            AVG(motor3_clean) as motor3_avg,
            MIN(motor3_clean) as motor3_min,
            MAX(motor3_clean) as motor3_max,
            
            -- 기타 메트릭
            COUNT(*) as record_count,
            SUM(CASE WHEN isFail THEN 1 ELSE 0 END) as failure_count,
            COUNT(*) - COUNT(sensor1_clean) as sensor1_null_count,
            COUNT(*) - COUNT(motor1_clean) as motor1_null_count
            
        FROM clean_fms_data
        GROUP BY DeviceId, DATE(event_time), HOUR(event_time)
        """)
        
        return stats_df

    def detect_anomalies(self, df):
        """이상 징후 탐지"""
        df.createOrReplaceTempView("fms_with_stats")
        
        anomaly_df = self.spark.sql("""
        WITH device_baselines AS (
            SELECT 
                DeviceId,
                PERCENTILE_APPROX(sensor1_clean, 0.95) as sensor1_p95,
                PERCENTILE_APPROX(sensor2_clean, 0.95) as sensor2_p95,
                PERCENTILE_APPROX(sensor3_clean, 0.95) as sensor3_p95,
                AVG(sensor1_clean) as sensor1_mean,
                AVG(sensor2_clean) as sensor2_mean,
                AVG(sensor3_clean) as sensor3_mean,
                STDDEV(sensor1_clean) as sensor1_std,
                STDDEV(sensor2_clean) as sensor2_std,
                STDDEV(sensor3_clean) as sensor3_std
            FROM fms_with_stats
            GROUP BY DeviceId
        )
        SELECT 
            f.*,
            b.sensor1_p95, b.sensor2_p95, b.sensor3_p95,
            
            -- 이상치 플래그
            CASE 
                WHEN ABS(f.sensor1_clean - b.sensor1_mean) > 3 * b.sensor1_std 
                THEN TRUE ELSE FALSE 
            END as sensor1_outlier,
            
            CASE 
                WHEN ABS(f.sensor2_clean - b.sensor2_mean) > 3 * b.sensor2_std 
                THEN TRUE ELSE FALSE 
            END as sensor2_outlier,
            
            CASE 
                WHEN ABS(f.sensor3_clean - b.sensor3_mean) > 3 * b.sensor3_std 
                THEN TRUE ELSE FALSE 
            END as sensor3_outlier,
            
            -- 임계값 초과 플래그
            CASE WHEN f.sensor1_clean > b.sensor1_p95 THEN TRUE ELSE FALSE END as sensor1_high,
            CASE WHEN f.sensor2_clean > b.sensor2_p95 THEN TRUE ELSE FALSE END as sensor2_high,
            CASE WHEN f.sensor3_clean > b.sensor3_p95 THEN TRUE ELSE FALSE END as sensor3_high
            
        FROM fms_with_stats f
        LEFT JOIN device_baselines b ON f.DeviceId = b.DeviceId
        """)
        
        return anomaly_df