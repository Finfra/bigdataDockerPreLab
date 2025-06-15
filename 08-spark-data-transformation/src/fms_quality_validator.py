# spark-apps/fms_quality_validator.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from typing import Dict, List, Tuple
import json

class FMSDataQualityValidator:
    def __init__(self, spark_session):
        self.spark = spark_session
        self.quality_rules = self.define_quality_rules()

    def define_quality_rules(self) -> Dict:
        """데이터 품질 검증 규칙 정의"""
        return {
            "completeness_rules": {
                "required_fields": ["DeviceId", "time", "sensor1", "sensor2", "sensor3", 
                                  "motor1", "motor2", "motor3", "isFail"],
                "critical_fields": ["DeviceId", "time"],
                "min_completeness_threshold": 0.95
            },
            "validity_rules": {
                "DeviceId": {"type": "int", "range": [1, 5]},
                "sensor1": {"type": "float", "range": [0, 100]},
                "sensor2": {"type": "float", "range": [0, 100]},
                "sensor3": {"type": "float", "range": [0, 150]},
                "motor1": {"type": "int", "range": [0, 2000]},
                "motor2": {"type": "int", "range": [0, 1500]},
                "motor3": {"type": "int", "range": [0, 1800]},
                "isFail": {"type": "boolean"}
            },
            "consistency_rules": {
                "duplicate_check": True,
                "temporal_order": True,
                "device_sequence": True
            },
            "timeliness_rules": {
                "max_delay_seconds": 60,
                "expected_interval_seconds": 10
            }
        }

    def validate_completeness(self, df):
        """완전성 검증"""
        total_count = df.count()
        
        completeness_results = []
        
        for field in self.quality_rules["completeness_rules"]["required_fields"]:
            non_null_count = df.filter(col(field).isNotNull()).count()
            completeness_rate = non_null_count / total_count if total_count > 0 else 0
            
            completeness_results.append({
                "field": field,
                "total_records": total_count,
                "non_null_records": non_null_count,
                "completeness_rate": completeness_rate,
                "is_critical": field in self.quality_rules["completeness_rules"]["critical_fields"],
                "passes_threshold": completeness_rate >= self.quality_rules["completeness_rules"]["min_completeness_threshold"]
            })
        
        # DataFrame으로 변환
        completeness_df = self.spark.createDataFrame(completeness_results)
        
        # 전체 완전성 점수 계산
        overall_completeness = completeness_df.agg(
            avg("completeness_rate").alias("overall_completeness_rate"),
            sum(when(col("passes_threshold"), 1).otherwise(0)).alias("fields_passing"),
            count("*").alias("total_fields")
        ).collect()[0]
        
        return completeness_df, overall_completeness

    def validate_validity(self, df):
        """유효성 검증"""
        validity_df = df
        validity_checks = []
        
        for field, rules in self.quality_rules["validity_rules"].items():
            if field in df.columns:
                # 범위 검증
                if "range" in rules:
                    min_val, max_val = rules["range"]
                    validity_df = validity_df.withColumn(
                        f"{field}_range_valid",
                        when(col(field).isNull(), lit(True))  # NULL 값은 완전성에서 처리
                        .otherwise((col(field) >= min_val) & (col(field) <= max_val))
                    )
                    
                    validity_checks.append(f"{field}_range_valid")
        
        # 전체 유효성 점수 계산
        validity_condition = lit(True)
        for check in validity_checks:
            validity_condition = validity_condition & col(check)
        
        validity_df = validity_df.withColumn("is_valid_record", validity_condition)
        
        validity_summary = validity_df.agg(
            avg(col("is_valid_record").cast("int")).alias("validity_rate"),
            sum(when(col("is_valid_record"), 1).otherwise(0)).alias("valid_records"),
            count("*").alias("total_records")
        ).collect()[0]
        
        return validity_df, validity_summary

    def generate_quality_report(self, df):
        """종합 품질 리포트 생성"""
        print("Starting comprehensive data quality validation...")
        
        # 각 차원별 검증 수행
        completeness_df, completeness_summary = self.validate_completeness(df)
        validity_df, validity_summary = self.validate_validity(df)
        
        # 품질 리포트 생성
        quality_report = {
            "validation_timestamp": df.select(current_timestamp().alias("ts")).collect()[0]["ts"],
            "dataset_summary": {
                "total_records": df.count(),
                "unique_devices": df.select("DeviceId").distinct().count()
            },
            "dimension_details": {
                "completeness": completeness_summary,
                "validity": validity_summary
            }
        }
        
        return quality_report

# 사용 예제
if __name__ == "__main__":
    spark = SparkSession.builder.appName("FMS-Quality-Validation").getOrCreate()
    
    # 품질 검증 수행
    validator = FMSDataQualityValidator(spark)
    # quality_report = validator.generate_quality_report(sample_df)