# spark-apps/fms-realtime-processor.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

class FMSStreamProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("FMS-RealTime-Processor") \
            .config("spark.sql.streaming.checkpointLocation", "/opt/spark-data/checkpoint") \
            .getOrCreate()
        
        self.schema = StructType([
            StructField("time", StringType(), True),
            StructField("DeviceId", IntegerType(), True),
            StructField("sensor1", FloatType(), True),
            StructField("sensor2", FloatType(), True), 
            StructField("sensor3", FloatType(), True),
            StructField("motor1", IntegerType(), True),
            StructField("motor2", IntegerType(), True),
            StructField("motor3", IntegerType(), True),
            StructField("isFail", BooleanType(), True)
        ])

    def process_stream(self):
        # Kafka 스트림 읽기
        raw_stream = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka-1:9092") \
            .option("subscribe", "fms-raw-data") \
            .load()
        
        # 데이터 파싱 및 검증
        processed_stream = raw_stream \
            .select(from_json(col("value").cast("string"), self.schema).alias("data")) \
            .select("data.*") \
            .withColumn("quality_score", self.calculate_quality_score()) \
            .withColumn("processed_at", current_timestamp())
        
        return processed_stream

    def calculate_quality_score(self):
        return when(
            (col("sensor1").between(0, 100)) &
            (col("sensor2").between(0, 100)) &
            (col("sensor3").between(0, 150)), 1.0
        ).otherwise(0.0)