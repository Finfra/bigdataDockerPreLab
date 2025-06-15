#!/usr/bin/env python3
"""
Spark Streaming with Kafka Integration
Kafka에서 데이터를 수신하여 실시간 분석
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StringType, IntegerType

def create_spark_session():
    return SparkSession.builder \
        .appName("KafkaSparkStreaming") \
        .master("spark://s1:7077") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
        .getOrCreate()

def kafka_stream_processing():
    spark = create_spark_session()
    
    # Kafka 스트림 읽기
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "s1:9092,s2:9092,s3:9092") \
        .option("subscribe", "sensor-data") \
        .load()

    # 메시지 처리
    processed_df = df.select(
        col("key").cast("string"),
        col("value").cast("string"),
        col("timestamp")
    ) \
    .withColumn("processing_time", current_timestamp()) \
    .withColumn("word_count", size(split(col("value"), " ")))

    # 콘솔 출력
    query = processed_df.writeStream \
        .outputMode("append") \
        .format("console") \
        .trigger(processingTime='10 seconds') \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    kafka_stream_processing()
