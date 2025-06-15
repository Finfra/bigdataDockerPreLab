# tests/test_performance.py
import time
import threading
from kafka import KafkaProducer
import json
import statistics

class PerformanceTest:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.latencies = []
        
    def send_message_batch(self, batch_size=1000):
        """배치 메시지 전송 성능 테스트"""
        start_time = time.time()
        
        for i in range(batch_size):
            test_data = {
                "DeviceId": i % 5 + 1,
                "time": f"2024-01-15T10:{i:02d}:00Z",
                "sensor1": 80 + (i % 20),
                "sensor2": 50 + (i % 30),
                "sensor3": 100 + (i % 50),
                "motor1": 1100 + (i % 100),
                "motor2": 700 + (i % 80),
                "motor3": 900 + (i % 90),
                "isFail": i % 10 == 0
            }
            
            msg_start = time.time()
            future = self.producer.send('fms-raw-data', test_data)
            future.get()  # 동기 대기
            msg_latency = time.time() - msg_start
            self.latencies.append(msg_latency)
        
        total_time = time.time() - start_time
        throughput = batch_size / total_time
        
        return {
            'total_time': total_time,
            'throughput': throughput,
            'avg_latency': statistics.mean(self.latencies),
            'p95_latency': statistics.quantiles(self.latencies, n=20)[18],
            'max_latency': max(self.latencies)
        }
    
    def concurrent_load_test(self, num_threads=5, messages_per_thread=200):
        """동시성 부하 테스트"""
        def worker():
            for i in range(messages_per_thread):
                test_data = {
                    "DeviceId": threading.current_thread().ident % 5 + 1,
                    "time": f"2024-01-15T10:{i:02d}:00Z",
                    "sensor1": 80,
                    "sensor2": 50,
                    "sensor3": 100,
                    "motor1": 1100,
                    "motor2": 700,
                    "motor3": 900,
                    "isFail": False
                }
                self.producer.send('fms-raw-data', test_data)
        
        start_time = time.time()
        threads = []
        
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        total_time = time.time() - start_time
        total_messages = num_threads * messages_per_thread
        
        return {
            'total_messages': total_messages,
            'total_time': total_time,
            'throughput': total_messages / total_time,
            'threads': num_threads
        }

if __name__ == '__main__':
    perf_test = PerformanceTest()
    
    print("Running batch performance test...")
    batch_result = perf_test.send_message_batch(1000)
    print(f"Batch Test - Throughput: {batch_result['throughput']:.2f} msg/sec")
    print(f"Average Latency: {batch_result['avg_latency']*1000:.2f} ms")
    
    print("\nRunning concurrent load test...")
    load_result = perf_test.concurrent_load_test(5, 200)
    print(f"Load Test - Throughput: {load_result['throughput']:.2f} msg/sec")
    print(f"Total Messages: {load_result['total_messages']}")