#!/bin/bash

# ============================================================================
# Kafka Topic 初始化脚本
# 用于创建GraphRAG项目所需的Kafka Topic
# ============================================================================

set -e

# Kafka配置
KAFKA_BROKER="${KAFKA_BROKER:-kafka:9093}"
KAFKA_TOPICS_CMD="${KAFKA_TOPICS_CMD:-kafka-topics}"

# 最大等待次数
MAX_RETRIES=30
RETRY_INTERVAL=5

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 等待Kafka就绪
wait_for_kafka() {
    log_info "等待Kafka服务就绪..."
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if $KAFKA_TOPICS_CMD --bootstrap-server $KAFKA_BROKER --list > /dev/null 2>&1; then
            log_info "Kafka服务已就绪"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log_warn "Kafka未就绪，等待中... ($retry_count/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    log_error "Kafka服务启动超时"
    return 1
}

# 创建Topic函数
# 参数: topic_name partitions replication_factor
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    
    log_info "检查Topic: $topic_name"
    
    # 检查Topic是否已存在
    if $KAFKA_TOPICS_CMD --bootstrap-server $KAFKA_BROKER --list | grep -q "^${topic_name}$"; then
        log_warn "Topic [$topic_name] 已存在，跳过创建"
        return 0
    fi
    
    # 创建Topic
    log_info "创建Topic: $topic_name (分区数: $partitions, 副本因子: $replication_factor)"
    $KAFKA_TOPICS_CMD --bootstrap-server $KAFKA_BROKER \
        --create \
        --topic $topic_name \
        --partitions $partitions \
        --replication-factor $replication_factor
    
    if [ $? -eq 0 ]; then
        log_info "Topic [$topic_name] 创建成功"
    else
        log_error "Topic [$topic_name] 创建失败"
        return 1
    fi
}

# 显示Topic详情
show_topic_details() {
    log_info "显示所有Topic详情:"
    echo "=========================================="
    $KAFKA_TOPICS_CMD --bootstrap-server $KAFKA_BROKER --list
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始初始化Kafka Topic..."
    log_info "Kafka Broker: $KAFKA_BROKER"
    
    # 等待Kafka就绪
    wait_for_kafka
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # 创建Topic列表
    # Topic名称                    分区数  副本因子
    # document-process: 文档处理Topic
    create_topic "document-process" 3 1
    
    # document-chunk: 文档分块Topic
    create_topic "document-chunk" 3 1
    
    # embedding-task: 向量化任务Topic
    create_topic "embedding-task" 3 1
    
    # kg-extraction: 知识图谱抽取Topic
    create_topic "kg-extraction" 3 1
    
    # notification: 通知消息Topic
    create_topic "notification" 2 1
    
    # 显示创建结果
    show_topic_details
    
    log_info "Kafka Topic初始化完成!"
}

# 执行主函数
main "$@"
