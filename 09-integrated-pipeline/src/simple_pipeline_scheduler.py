# simple_pipeline_scheduler.py - Airflow 대신 단순한 스케줄러
import time
import subprocess
import logging
import schedule
from datetime import datetime

class SimplePipelineScheduler:
    def __init__(self):
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/logs/pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_data_collection(self):
        """데이터 수집 작업"""
        try:
            self.logger.info("Starting data collection...")
            
            # FMS 데이터 수집기 실행
            result = subprocess.run([
                'python', '/opt/fms/collector/fms_producer_simple.py'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("Data collection completed successfully")
                return True
            else:
                self.logger.error(f"Data collection failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in data collection: {str(e)}")
            return False

    def run_stream_processing(self):
        """스트림 처리 작업"""
        try:
            self.logger.info("Starting stream processing...")
            
            # Spark 애플리케이션 실행
            result = subprocess.run([
                'spark-submit',
                '--master', 'spark://spark-master:7077',
                '--packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0',
                '/opt/spark-apps/fms-streaming-processor.py'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Stream processing completed successfully")
                return True
            else:
                self.logger.error(f"Stream processing failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in stream processing: {str(e)}")
            return False

    def run_quality_check(self):
        """데이터 품질 검사"""
        try:
            self.logger.info("Starting quality check...")
            
            # 품질 검사 스크립트 실행
            result = subprocess.run([
                'python', '/opt/fms/quality/simple_validator.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.logger.info("Quality check completed successfully")
                return True
            else:
                self.logger.error(f"Quality check failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in quality check: {str(e)}")
            return False

    def run_full_pipeline(self):
        """전체 파이프라인 실행"""
        self.logger.info("=" * 50)
        self.logger.info("Starting FMS Data Pipeline")
        self.logger.info("=" * 50)
        
        # 1단계: 데이터 수집
        if not self.run_data_collection():
            self.logger.error("Pipeline failed at data collection stage")
            return
        
        # 2단계: 스트림 처리  
        if not self.run_stream_processing():
            self.logger.error("Pipeline failed at stream processing stage")
            return
            
        # 3단계: 품질 검사
        if not self.run_quality_check():
            self.logger.error("Pipeline failed at quality check stage")
            return
            
        self.logger.info("Pipeline completed successfully!")

    def run_scheduler(self):
        """스케줄러 실행"""
        self.logger.info("Starting Simple Pipeline Scheduler...")
        
        # 매시간 정각에 실행
        schedule.every().hour.at(":00").do(self.run_full_pipeline)
        
        # 테스트를 위해 매 5분마다 실행 (개발용)
        # schedule.every(5).minutes.do(self.run_full_pipeline)
        
        self.logger.info("Scheduler started. Pipeline will run every hour.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크

# 수동 실행 모드
def run_once():
    """한 번만 실행"""
    scheduler = SimplePipelineScheduler()
    scheduler.run_full_pipeline()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        run_once()
    else:
        scheduler = SimplePipelineScheduler()
        scheduler.run_scheduler()
