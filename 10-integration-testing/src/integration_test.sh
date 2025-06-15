#!/bin/bash
# tests/integration_test.sh

echo "Starting FMS Integration Tests..."

# 1. 클러스터 상태 체크
echo "1. Checking cluster health..."
./scripts/cluster-health-check.sh

# 2. 데이터 플로우 테스트
echo "2. Testing data flow..."
python tests/test_data_pipeline.py

# 3. 성능 테스트
echo "3. Running performance tests..."
python tests/test_performance.py

# 4. 장애 복구 테스트
echo "4. Testing failure recovery..."
python tests/test_failover.py

echo "Integration tests completed!"