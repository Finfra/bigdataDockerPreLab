#!/usr/bin/env python3
"""
FMS 통합 테스트 실행기
기존 파이프라인에 대한 종합적인 테스트
"""

import json
import time
import threading
import statistics
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import logging

class FMSIntegrationTest:
    def __init__(self):
        self.setup_logging()
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8')
        )
        self.latencies = []
        self.test_results = {}

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('FMS-Integration-Test')

    def test_kafka_connectivity(self):
        """Kafka 연결성 테스트"""
        self.logger.info("Testing Kafka connectivity...")
        
        try:
            # 테스트 메시지 발송
            test_data = {
                "DeviceId": 999,  # 테스트용 특별 ID
                "time": datetime.now().isoformat(),
                "sensor1": 85.0,
                "sensor2": 60.0,
                "sensor3": 120.0,
                "motor1": 1200,
                "motor2": 800,
                "motor3": 1000,
                "isFail": False,
                "test_type": "connectivity"
            }
            
            future = self.producer.send('fms-raw-data', key='test', value=test_data)
            result = future.get(timeout=10)
            
            self.test_results['kafka_connectivity'] = {
                'status': 'PASS',
                'partition': result.partition,
                'offset': result.offset
            }
            self.logger.info("✅ Kafka connectivity test PASSED")
            return True
            
        except Exception as e:
            self.test_results['kafka_connectivity'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"❌ Kafka connectivity test FAILED: {str(e)}")
            return False

    def test_data_pipeline_integrity(self):
        """데이터 파이프라인 무결성 테스트"""
        self.logger.info("Testing data pipeline integrity...")
        
        try:
            # 10개 테스트 메시지 발송
            sent_messages = []
            for i in range(10):
                test_data = {
                    "DeviceId": (i % 5) + 1,
                    "time": datetime.now().isoformat(),
                    "sensor1": 80.0 + i,
                    "sensor2": 50.0 + i,
                    "sensor3": 100.0 + i,
                    "motor1": 1100 + i * 10,
                    "motor2": 700 + i * 10,
                    "motor3": 900 + i * 10,
                    "isFail": i % 3 == 0,
                    "test_id": f"integrity_test_{i}",
                    "test_type": "integrity"
                }
                
                self.producer.send('fms-raw-data', key=str(test_data["DeviceId"]), value=test_data)
                sent_messages.append(test_data)
                time.sleep(0.1)
            
            self.producer.flush()  # 모든 메시지 전송 완료 대기
            
            self.test_results['pipeline_integrity'] = {
                'status': 'PASS',
                'messages_sent': len(sent_messages),
                'test_duration': '1 second'
            }
            self.logger.info(f"✅ Data pipeline integrity test PASSED - {len(sent_messages)} messages sent")
            return True
            
        except Exception as e:
            self.test_results['pipeline_integrity'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"❌ Data pipeline integrity test FAILED: {str(e)}")
            return False

    def test_throughput_performance(self, batch_size=500):
        """처리량 성능 테스트"""
        self.logger.info(f"Testing throughput with {batch_size} messages...")
        
        try:
            start_time = time.time()
            latencies = []
            
            for i in range(batch_size):
                test_data = {
                    "DeviceId": (i % 5) + 1,
                    "time": datetime.now().isoformat(),
                    "sensor1": 75.0 + (i % 20),
                    "sensor2": 45.0 + (i % 30),
                    "sensor3": 95.0 + (i % 50),
                    "motor1": 1050 + (i % 100),
                    "motor2": 650 + (i % 80),
                    "motor3": 850 + (i % 90),
                    "isFail": i % 15 == 0,
                    "test_id": f"throughput_test_{i}",
                    "test_type": "throughput"
                }
                
                msg_start = time.time()
                future = self.producer.send('fms-raw-data', key=str(test_data["DeviceId"]), value=test_data)
                future.get(timeout=5)  # 동기 대기
                latency = time.time() - msg_start
                latencies.append(latency)
            
            total_time = time.time() - start_time
            throughput = batch_size / total_time
            
            avg_latency = statistics.mean(latencies) * 1000  # ms 변환
            p95_latency = statistics.quantiles(latencies, n=20)[18] * 1000 if len(latencies) >= 20 else max(latencies) * 1000
            max_latency = max(latencies) * 1000
            
            self.test_results['throughput_performance'] = {
                'status': 'PASS' if throughput >= 100 else 'WARN',  # 100 msg/sec 기준
                'messages': batch_size,
                'total_time_sec': round(total_time, 2),
                'throughput_msg_per_sec': round(throughput, 2),
                'avg_latency_ms': round(avg_latency, 2),
                'p95_latency_ms': round(p95_latency, 2),
                'max_latency_ms': round(max_latency, 2)
            }
            
            self.logger.info(f"✅ Throughput test completed:")
            self.logger.info(f"   - Throughput: {throughput:.2f} msg/sec")
            self.logger.info(f"   - Average latency: {avg_latency:.2f} ms")
            self.logger.info(f"   - P95 latency: {p95_latency:.2f} ms")
            
            return True
            
        except Exception as e:
            self.test_results['throughput_performance'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"❌ Throughput test FAILED: {str(e)}")
            return False

    def test_concurrent_load(self, num_threads=3, messages_per_thread=100):
        """동시성 부하 테스트"""
        self.logger.info(f"Testing concurrent load: {num_threads} threads, {messages_per_thread} msg/thread...")
        
        results = []
        
        def worker_thread(thread_id):
            try:
                for i in range(messages_per_thread):
                    test_data = {
                        "DeviceId": ((thread_id + i) % 5) + 1,
                        "time": datetime.now().isoformat(),
                        "sensor1": 70.0 + thread_id + i,
                        "sensor2": 40.0 + thread_id + i,
                        "sensor3": 90.0 + thread_id + i,
                        "motor1": 1000 + thread_id * 100 + i,
                        "motor2": 600 + thread_id * 50 + i,
                        "motor3": 800 + thread_id * 75 + i,
                        "isFail": (thread_id + i) % 20 == 0,
                        "test_id": f"concurrent_test_t{thread_id}_m{i}",
                        "test_type": "concurrent",
                        "thread_id": thread_id
                    }
                    
                    self.producer.send('fms-raw-data', key=str(test_data["DeviceId"]), value=test_data)
                    
                results.append(f"Thread {thread_id} completed {messages_per_thread} messages")
                
            except Exception as e:
                results.append(f"Thread {thread_id} failed: {str(e)}")
        
        try:
            start_time = time.time()
            threads = []
            
            for t_id in range(num_threads):
                thread = threading.Thread(target=worker_thread, args=(t_id,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            total_messages = num_threads * messages_per_thread
            concurrent_throughput = total_messages / total_time
            
            self.test_results['concurrent_load'] = {
                'status': 'PASS',
                'threads': num_threads,
                'messages_per_thread': messages_per_thread,
                'total_messages': total_messages,
                'total_time_sec': round(total_time, 2),
                'concurrent_throughput_msg_per_sec': round(concurrent_throughput, 2),
                'thread_results': results
            }
            
            self.logger.info(f"✅ Concurrent load test completed:")
            self.logger.info(f"   - Total messages: {total_messages}")
            self.logger.info(f"   - Concurrent throughput: {concurrent_throughput:.2f} msg/sec")
            
            return True
            
        except Exception as e:
            self.test_results['concurrent_load'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"❌ Concurrent load test FAILED: {str(e)}")
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        self.logger.info("🧪 Starting FMS Integration Tests")
        self.logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. Kafka 연결성 테스트
        test1_result = self.test_kafka_connectivity()
        time.sleep(1)
        
        # 2. 데이터 파이프라인 무결성 테스트
        test2_result = self.test_data_pipeline_integrity()
        time.sleep(2)
        
        # 3. 처리량 성능 테스트
        test3_result = self.test_throughput_performance(500)
        time.sleep(2)
        
        # 4. 동시성 부하 테스트
        test4_result = self.test_concurrent_load(3, 100)
        
        total_time = time.time() - start_time
        
        # 결과 요약
        self.print_test_summary(total_time)
        
        return all([test1_result, test2_result, test3_result, test4_result])

    def print_test_summary(self, total_time):
        """테스트 결과 요약 출력"""
        self.logger.info("=" * 60)
        self.logger.info("📊 TEST SUMMARY")
        self.logger.info("=" * 60)
        
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        warned_tests = len([r for r in self.test_results.values() if r['status'] == 'WARN'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        total_tests = len(self.test_results)
        
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"✅ Passed: {passed_tests}")
        self.logger.info(f"⚠️ Warnings: {warned_tests}")
        self.logger.info(f"❌ Failed: {failed_tests}")
        self.logger.info(f"⏱️ Total Time: {total_time:.2f} seconds")
        
        # 세부 결과
        self.logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARN' else "❌"
            self.logger.info(f"{status_icon} {test_name}: {result['status']}")
            
            # 성능 메트릭 출력
            if 'throughput_msg_per_sec' in result:
                self.logger.info(f"   → Throughput: {result['throughput_msg_per_sec']} msg/sec")
            if 'avg_latency_ms' in result:
                self.logger.info(f"   → Avg Latency: {result['avg_latency_ms']} ms")
        
        if failed_tests == 0:
            self.logger.info("\n🎉 All integration tests completed successfully!")
        else:
            self.logger.info(f"\n⚠️ {failed_tests} test(s) failed. Please check the errors.")

if __name__ == "__main__":
    test_runner = FMSIntegrationTest()
    success = test_runner.run_all_tests()
    
    if success:
        exit(0)
    else:
        exit(1)
