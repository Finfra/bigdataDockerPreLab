#!/bin/bash

# BigData Docker Pre-Lab 환경 체크 스크립트
# 작성일: 2025-06-14

echo "=== BigData Docker Pre-Lab 환경 체크 시작 ==="
echo

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 체크 결과 저장
PASS_COUNT=0
FAIL_COUNT=0

# 함수: 체크 결과 출력
check_result() {
    local name="$1"
    local result="$2"
    local detail="$3"
    
    if [ "$result" = "PASS" ]; then
        echo -e "✅ ${GREEN}$name: PASS${NC} - $detail"
        ((PASS_COUNT++))
    else
        echo -e "❌ ${RED}$name: FAIL${NC} - $detail"
        ((FAIL_COUNT++))
    fi
}

# 1. Docker 체크
echo "1. Docker 설치 및 실행 상태 체크"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>/dev/null)
    if docker info &> /dev/null; then
        check_result "Docker" "PASS" "$DOCKER_VERSION (실행 중)"
    else
        check_result "Docker" "FAIL" "설치되어 있지만 실행되지 않음"
    fi
else
    check_result "Docker" "FAIL" "설치되지 않음"
fi

# 2. Docker Compose 체크
echo
echo "2. Docker Compose 설치 체크"
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>/dev/null)
    check_result "Docker Compose" "PASS" "$COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version 2>/dev/null)
    check_result "Docker Compose" "PASS" "$COMPOSE_VERSION (플러그인)"
else
    check_result "Docker Compose" "FAIL" "설치되지 않음"
fi

# 3. Python 체크
echo
echo "3. Python 설치 체크"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>/dev/null)
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        check_result "Python" "PASS" "$PYTHON_VERSION"
    else
        check_result "Python" "FAIL" "$PYTHON_VERSION (3.8 이상 필요)"
    fi
else
    check_result "Python" "FAIL" "설치되지 않음"
fi

# 4. Git 체크
echo
echo "4. Git 설치 체크"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version 2>/dev/null)
    check_result "Git" "PASS" "$GIT_VERSION"
else
    check_result "Git" "FAIL" "설치되지 않음"
fi

# 5. 시스템 리소스 체크
echo
echo "5. 시스템 리소스 체크"

# 메모리 체크 (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(sysctl -n hw.memsize)
    TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
    if [ "$TOTAL_MEM_GB" -ge 8 ]; then
        check_result "메모리" "PASS" "${TOTAL_MEM_GB}GB (8GB 이상 권장)"
    else
        check_result "메모리" "FAIL" "${TOTAL_MEM_GB}GB (8GB 이상 권장)"
    fi
else
    # Linux
    TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
    if [ "$TOTAL_MEM_GB" -ge 8 ]; then
        check_result "메모리" "PASS" "${TOTAL_MEM_GB}GB (8GB 이상 권장)"
    else
        check_result "메모리" "FAIL" "${TOTAL_MEM_GB}GB (8GB 이상 권장)"
    fi
fi

# 6. 포트 사용 가능 여부 체크
echo
echo "6. 필요 포트 사용 가능 여부 체크"
PORTS=(8080 8081 9092 2181 50070 8088 9870 3000 9090)
AVAILABLE_PORTS=0
TOTAL_PORTS=${#PORTS[@]}

for port in "${PORTS[@]}"; do
    echo -n " :$port "
    echo ""
    if ! lsof -i :$port &> /dev/null; then
        ((AVAILABLE_PORTS++))
    fi
done

if [ "$AVAILABLE_PORTS" -eq "$TOTAL_PORTS" ]; then
    check_result "포트 가용성" "PASS" "모든 필요 포트(${PORTS[*]}) 사용 가능"
else
    USED_COUNT=$((TOTAL_PORTS - AVAILABLE_PORTS))
    check_result "포트 가용성" "FAIL" "$USED_COUNT개 포트가 사용 중"
fi

# 7. 디스크 공간 체크
echo
echo "7. 디스크 공간 체크"
AVAILABLE_SPACE=$(df -h . | tail -1 | awk '{print $4}' | sed 's/[^0-9.]//g')
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS에서 GB 단위로 변환
    SPACE_NUM=$(echo "$AVAILABLE_SPACE" | sed 's/G//g')
    if (( $(echo "$SPACE_NUM > 50" | bc -l) )); then
        check_result "디스크 공간" "PASS" "${AVAILABLE_SPACE}G 사용 가능 (50GB 이상 권장)"
    else
        check_result "디스크 공간" "FAIL" "${AVAILABLE_SPACE}G 사용 가능 (50GB 이상 권장)"
    fi
else
    check_result "디스크 공간" "PASS" "체크 완료"
fi

# 최종 결과
echo
echo "=== 환경 체크 결과 ==="
echo -e "통과: ${GREEN}$PASS_COUNT${NC}개"
echo -e "실패: ${RED}$FAIL_COUNT${NC}개"
echo

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 환경 체크를 통과했습니다! Pre-Lab을 진행할 준비가 되었습니다.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ 일부 환경 설정이 필요합니다. 실패 항목을 확인 후 설치/설정을 완료해주세요.${NC}"
    exit 1
fi
