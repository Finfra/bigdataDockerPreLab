# spark-apps/fms_udfs.py
from pyspark.sql.functions import udf
from pyspark.sql.types import *
import numpy as np
import math
from typing import List, Tuple, Optional

class FMSUDFs:
    def __init__(self, spark):
        self.spark = spark
        self.register_udfs()

    def register_udfs(self):
        """UDF 등록"""
        # 센서 상태 분류 UDF
        self.sensor_status_udf = udf(self.classify_sensor_status, StringType())
        self.spark.udf.register("classify_sensor_status", self.sensor_status_udf)
        
        # 모터 효율성 계산 UDF
        self.motor_efficiency_udf = udf(self.calculate_motor_efficiency, DoubleType())
        self.spark.udf.register("calculate_motor_efficiency", self.motor_efficiency_udf)
        
        # 이상치 점수 계산 UDF
        self.outlier_score_udf = udf(self.calculate_outlier_score, DoubleType())
        self.spark.udf.register("calculate_outlier_score", self.outlier_score_udf)
        
        # 장비 위험도 평가 UDF
        self.risk_assessment_udf = udf(self.assess_equipment_risk, StructType([
            StructField("risk_level", StringType(), True),
            StructField("risk_score", DoubleType(), True),
            StructField("risk_factors", ArrayType(StringType()), True)
        ]))
        self.spark.udf.register("assess_equipment_risk", self.risk_assessment_udf)

    @staticmethod
    def classify_sensor_status(sensor1: float, sensor2: float, sensor3: float) -> str:
        """센서 상태 분류"""
        if any(v is None for v in [sensor1, sensor2, sensor3]):
            return "DATA_MISSING"
        
        # 임계값 정의
        temp_critical = 90.0  # sensor1 (온도)
        humidity_critical = 85.0  # sensor2 (습도)  
        pressure_critical = 130.0  # sensor3 (압력)
        
        critical_count = 0
        warning_count = 0
        
        # 온도 체크
        if sensor1 > temp_critical:
            critical_count += 1
        elif sensor1 > temp_critical * 0.9:
            warning_count += 1
            
        # 습도 체크
        if sensor2 > humidity_critical:
            critical_count += 1
        elif sensor2 > humidity_critical * 0.9:
            warning_count += 1
            
        # 압력 체크
        if sensor3 > pressure_critical:
            critical_count += 1
        elif sensor3 > pressure_critical * 0.9:
            warning_count += 1
        
        if critical_count >= 2:
            return "CRITICAL"
        elif critical_count >= 1:
            return "HIGH_WARNING"
        elif warning_count >= 2:
            return "WARNING"
        else:
            return "NORMAL"

    @staticmethod
    def calculate_motor_efficiency(motor1_rpm: int, motor2_rpm: int, motor3_rpm: int,
                                 sensor1: float, sensor2: float) -> float:
        """모터 효율성 계산"""
        if any(v is None for v in [motor1_rpm, motor2_rpm, motor3_rpm, sensor1, sensor2]):
            return 0.0
        
        try:
            # 기준 RPM 대비 실제 RPM 효율성
            motor1_eff = motor1_rpm / 2000.0 if motor1_rpm <= 2000 else 2000.0 / motor1_rpm
            motor2_eff = motor2_rpm / 1500.0 if motor2_rpm <= 1500 else 1500.0 / motor2_rpm  
            motor3_eff = motor3_rpm / 1800.0 if motor3_rpm <= 1800 else 1800.0 / motor3_rpm
            
            # 온도/습도에 따른 효율성 보정
            temp_factor = max(0.5, 1.0 - (sensor1 - 70) / 100) if sensor1 > 70 else 1.0
            humidity_factor = max(0.7, 1.0 - (sensor2 - 60) / 100) if sensor2 > 60 else 1.0
            
            # 종합 효율성 계산
            base_efficiency = (motor1_eff + motor2_eff + motor3_eff) / 3.0
            adjusted_efficiency = base_efficiency * temp_factor * humidity_factor
            
            return min(1.0, max(0.0, adjusted_efficiency))
            
        except (ZeroDivisionError, TypeError):
            return 0.0

    @staticmethod
    def assess_equipment_risk(device_id: int, sensor_status: str, motor_efficiency: float,
                            failure_rate: float, outlier_score: float) -> Tuple[str, float, List[str]]:
        """장비 위험도 종합 평가"""
        risk_factors = []
        risk_score = 0.0
        
        # 센서 상태 기반 위험도
        sensor_risk_map = {
            "CRITICAL": 0.4,
            "HIGH_WARNING": 0.3,
            "WARNING": 0.15,
            "NORMAL": 0.0,
            "DATA_MISSING": 0.2
        }
        
        sensor_risk = sensor_risk_map.get(sensor_status, 0.2)
        risk_score += sensor_risk
        
        if sensor_risk > 0.2:
            risk_factors.append(f"sensor_status_{sensor_status.lower()}")
        
        # 모터 효율성 기반 위험도
        if motor_efficiency < 0.3:
            risk_score += 0.3
            risk_factors.append("low_motor_efficiency")
        elif motor_efficiency < 0.6:
            risk_score += 0.15
            risk_factors.append("reduced_motor_efficiency")
        
        # 장애율 기반 위험도
        if failure_rate > 0.5:
            risk_score += 0.4
            risk_factors.append("high_failure_rate")
        elif failure_rate > 0.2:
            risk_score += 0.2
            risk_factors.append("elevated_failure_rate")
        
        # 위험도 레벨 결정
        risk_score = min(1.0, risk_score)
        
        if risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif risk_score >= 0.6:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        elif risk_score >= 0.2:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return (risk_level, risk_score, risk_factors)