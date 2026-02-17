# Elasticsearch + Milvus 混合架构代码修改计划

> 版本: v1.0  
> 创建日期: 2026-02-17  
> 基于文档: 03-系统架构设计文档.md、05-开发计划文档.md

---

## 一、修改概述

### 1.1 修改目标

基于已完成的文档修改，实现 Elasticsearch + Milvus 混合检索架构的代码层面修改，包括：
- 添加 Elasticsearch 基础设施支持
- 实现 ES 关键词检索服务
- 实现 Milvus 向量检索服务增强
- 实现 RRF 融合算法
- 实现双存储同步机制

### 1.2 涉及模块

| 模块 | 修改类型 | 说明 |
|------|---------|------|
| docker-compose.yml | 修改 | 添加 Elasticsearch 服务 |
| backend/pom.xml | 修改 | 添加 ES 客户端依赖 |
| graphrag-common | 新增 | ES 配置、客户端、工具类 |
| graphrag-search | 新增 | 混合检索服务实现 |
| ai-services (Python) | 修改 | 双存储支持、RRF融合 |
| 测试用例 | 新增 | 混合检索测试 |

---

## 二、详细修改计划

### 2.1 基础设施层修改

#### 2.1.1 Docker Compose 添加 Elasticsearch

**文件**: `backend/docker-compose.yml`

**修改内容**:
- 添加 Elasticsearch 8.x 服务
- 添加 IK 中文分词器插件
- 配置 ES 集群（单节点开发环境）
- 添加 Kibana 可视化工具（可选）

**新增服务配置**:
```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
  container_name: graphrag-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - ES_JAVA_OPTS=-Xms512m -Xmx512m
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  networks:
    - graphrag-network
```

#### 2.1.2 Maven 依赖添加

**文件**: `backend/pom.xml`

**修改内容**:
- 添加 Elasticsearch Java Client 依赖版本管理

**新增依赖**:
```xml
<elasticsearch.version>8.12.0</elasticsearch.version>

<dependency>
    <groupId>co.elastic.clients</groupId>
    <artifactId>elasticsearch-java</artifactId>
    <version>${elasticsearch.version}</version>
</dependency>
```

---

### 2.2 graphrag-common 模块修改

#### 2.2.1 新增 ES 配置类

**文件**: `backend/graphrag-common/src/main/java/com/graphrag/common/storage/es/`

**新增文件**:
1. `ElasticsearchConfig.java` - ES 客户端配置
2. `ElasticsearchProperties.java` - ES 连接属性配置
3. `ElasticsearchClient.java` - ES 客户端封装

**配置属性**:
```java
@ConfigurationProperties(prefix = "elasticsearch")
public class ElasticsearchProperties {
    private String host = "localhost";
    private int port = 9200;
    private String username;
    private String password;
    private int connectionTimeout = 5000;
    private int socketTimeout = 30000;
}
```

#### 2.2.2 新增 ES 索引常量

**文件**: `backend/graphrag-common/src/main/java/com/graphrag/common/core/constant/ElasticsearchConstants.java`

**新增内容**:
```java
public class ElasticsearchConstants {
    public static final String DOC_INDEX = "doc_index";
    public static final String METADATA_INDEX = "metadata_index";
    public static final int DEFAULT_SHARDS = 3;
    public static final int DEFAULT_REPLICAS = 1;
}
```

---

### 2.3 graphrag-search 模块实现

#### 2.3.1 模块结构

```
graphrag-search/
├── pom.xml
├── src/main/java/com/graphrag/search/
│   ├── config/
│   │   └── SearchConfig.java
│   ├── controller/
│   │   └── SearchController.java
│   ├── dto/
│   │   ├── HybridSearchRequest.java
│   │   ├── HybridSearchResponse.java
│   │   └── SearchResult.java
│   ├── service/
│   │   ├── SearchService.java
│   │   ├── impl/
│   │   │   ├── KeywordSearchService.java      # ES关键词检索
│   │   │   ├── VectorSearchService.java       # Milvus向量检索
│   │   │   ├── HybridSearchService.java       # 混合检索服务
│   │   │   └── RRFFusionService.java          # RRF融合算法
│   │   └── DualStorageService.java            # 双存储同步
│   └── model/
│       └── SearchConstants.java
└── src/test/java/com/graphrag/search/
    ├── service/
    │   ├── KeywordSearchServiceTest.java
    │   ├── VectorSearchServiceTest.java
    │   └── RRFFusionServiceTest.java
    └── integration/
        └── HybridSearchIntegrationTest.java
```

#### 2.3.2 核心服务实现

**KeywordSearchService (ES关键词检索)**:
```java
@Service
public class KeywordSearchService {
    
    public List<SearchResult> search(String query, int topK, Map<String, Object> filters) {
        // BM25 关键词检索实现
    }
    
    public void indexDocument(String docId, String content, Map<String, Object> metadata) {
        // 文档索引写入
    }
    
    public void deleteDocument(String docId) {
        // 文档索引删除
    }
}
```

**VectorSearchService (Milvus向量检索)**:
```java
@Service
public class VectorSearchService {
    
    public List<SearchResult> search(float[] queryVector, int topK, List<String> docIds) {
        // 向量相似度检索实现
    }
    
    public void insertVectors(String docId, List<String> chunkIds, List<float[]> vectors) {
        // 向量数据写入
    }
    
    public void deleteVectors(String docId) {
        // 向量数据删除
    }
}
```

**RRFFusionService (RRF融合算法)**:
```java
@Service
public class RRFFusionService {
    
    private static final int DEFAULT_K = 60;
    
    public List<SearchResult> fuse(
        List<SearchResult> keywordResults,
        List<SearchResult> vectorResults,
        int k
    ) {
        // RRF融合算法实现
        // 公式: RRF(d) = Σ 1/(k + rank(d))
    }
}
```

**DualStorageService (双存储同步)**:
```java
@Service
public class DualStorageService {
    
    @Transactional
    public void indexDocument(DocumentIndexRequest request) {
        // 并行写入 ES 和 Milvus
        // 确保 doc_id 关联一致性
    }
    
    @Transactional
    public void deleteDocument(String docId) {
        // 并行删除 ES 和 Milvus 数据
    }
}
```

#### 2.3.3 API 接口设计

**HybridSearchRequest**:
```java
public class HybridSearchRequest {
    private String query;
    private int topK = 20;
    private boolean keywordEnabled = true;
    private boolean vectorEnabled = true;
    private Map<String, Object> filters;
    private FusionStrategy strategy = FusionStrategy.RRF;
}
```

**HybridSearchResponse**:
```java
public class HybridSearchResponse {
    private List<SearchResult> results;
    private long keywordTimeMs;
    private long vectorTimeMs;
    private long fusionTimeMs;
    private long totalTimeMs;
}
```

---

### 2.4 ai-services (Python) 模块修改

#### 2.4.1 配置文件修改

**文件**: `backend/ai-services/config/settings.py`

**新增配置**:
```python
class Settings(BaseSettings):
    # Elasticsearch 配置
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_INDEX: str = "doc_index"
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None
```

#### 2.4.2 新增 ES 客户端

**文件**: `backend/ai-services/services/embedding/es_client.py`

**新增内容**:
```python
from elasticsearch import Elasticsearch

class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch([f"http://{settings.ES_HOST}:{settings.ES_PORT}"])
    
    def index_document(self, doc_id: str, chunk_id: str, content: str, metadata: dict):
        # 索引文档
        
    def search(self, query: str, top_k: int = 100) -> List[dict]:
        # BM25 检索
        
    def delete_document(self, doc_id: str):
        # 删除文档
```

#### 2.4.3 修改 embedding API

**文件**: `backend/ai-services/api/embedding.py`

**修改内容**:
- 添加双存储写入逻辑
- 添加 doc_id 关联字段

#### 2.4.4 新增混合检索 API

**文件**: `backend/ai-services/api/search.py`

**新增内容**:
```python
@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    # 并行执行关键词检索和向量检索
    # RRF 融合排序
    # 返回融合结果
```

#### 2.4.5 新增 RRF 融合模块

**文件**: `backend/ai-services/services/search/rrf_fusion.py`

**新增内容**:
```python
class RRFFusion:
    @staticmethod
    def fuse(keyword_results: List[dict], vector_results: List[dict], k: int = 60) -> List[dict]:
        scores = defaultdict(float)
        for rank, result in enumerate(keyword_results, 1):
            scores[result["doc_id"]] += 1.0 / (k + rank)
        for rank, result in enumerate(vector_results, 1):
            scores[result["doc_id"]] += 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

#### 2.4.6 修改 requirements.txt

**新增依赖**:
```
elasticsearch>=8.12.0
```

---

### 2.5 测试用例

#### 2.5.1 Java 单元测试

| 测试类 | 测试内容 |
|--------|---------|
| `KeywordSearchServiceTest` | ES 关键词检索功能测试 |
| `VectorSearchServiceTest` | Milvus 向量检索功能测试 |
| `RRFFusionServiceTest` | RRF 融合算法测试 |
| `DualStorageServiceTest` | 双存储同步测试 |

#### 2.5.2 Python 单元测试

| 测试文件 | 测试内容 |
|---------|---------|
| `test_es_client.py` | ES 客户端功能测试 |
| `test_rrf_fusion.py` | RRF 融合算法测试 |
| `test_hybrid_search.py` | 混合检索集成测试 |

#### 2.5.3 集成测试

- 双存储写入一致性测试
- 混合检索性能测试
- 并发检索压力测试

---

## 三、实施顺序

### 阶段一：基础设施 (1天)

1. 修改 `docker-compose.yml` 添加 Elasticsearch
2. 修改 `pom.xml` 添加 ES 依赖
3. 修改 `requirements.txt` 添加 Python ES 依赖

### 阶段二：graphrag-common 模块 (1天)

1. 创建 ES 配置类
2. 创建 ES 客户端封装
3. 创建 ES 常量定义

### 阶段三：graphrag-search 模块 (2天)

1. 创建模块基础结构
2. 实现 KeywordSearchService
3. 实现 VectorSearchService
4. 实现 RRFFusionService
5. 实现 DualStorageService
6. 实现 HybridSearchService
7. 创建 SearchController

### 阶段四：ai-services 模块修改 (1天)

1. 修改 settings.py 添加 ES 配置
2. 创建 es_client.py
3. 修改 embedding.py 支持双存储
4. 创建 search.py 混合检索 API
5. 创建 rrf_fusion.py

### 阶段五：测试与验证 (1天)

1. 编写单元测试
2. 编写集成测试
3. 性能测试验证
4. 文档更新

---

## 四、验收标准

### 4.1 功能验收

| 验收项 | 验收标准 |
|--------|---------|
| ES 关键词检索 | BM25 排序正确，返回相关文档 |
| Milvus 向量检索 | COSINE 相似度正确，返回语义相似文档 |
| RRF 融合 | 融合结果综合两种检索优势 |
| 双存储同步 | ES 和 Milvus 数据一致 |
| doc_id 关联 | 同一文档在两个存储中 ID 一致 |

### 4.2 性能验收

| 指标 | 目标值 |
|------|--------|
| ES 检索延迟 | < 20ms |
| Milvus 检索延迟 | < 50ms |
| 混合检索总延迟 | < 100ms |
| 召回率提升 | > 10% |

### 4.3 代码质量

| 指标 | 目标值 |
|------|--------|
| 单元测试覆盖率 | > 70% |
| 代码规范检查 | 100% 通过 |
| 无高危安全漏洞 | 0 个 |

---

## 五、风险与应对

| 风险 | 应对措施 |
|------|---------|
| ES 与 Milvus 数据不一致 | 实现事务补偿机制，定期一致性检查 |
| 混合检索性能不达标 | 优化并行检索，添加缓存层 |
| IK 分词器安装失败 | 使用官方镜像或手动安装 |

---

## 六、文件修改清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `graphrag-common/.../es/ElasticsearchConfig.java` | ES 配置类 |
| `graphrag-common/.../es/ElasticsearchProperties.java` | ES 属性类 |
| `graphrag-common/.../es/ElasticsearchClient.java` | ES 客户端 |
| `graphrag-common/.../constant/ElasticsearchConstants.java` | ES 常量 |
| `graphrag-search/pom.xml` | 搜索模块 POM |
| `graphrag-search/.../service/impl/KeywordSearchService.java` | 关键词检索服务 |
| `graphrag-search/.../service/impl/VectorSearchService.java` | 向量检索服务 |
| `graphrag-search/.../service/impl/HybridSearchService.java` | 混合检索服务 |
| `graphrag-search/.../service/impl/RRFFusionService.java` | RRF 融合服务 |
| `graphrag-search/.../service/DualStorageService.java` | 双存储服务 |
| `graphrag-search/.../controller/SearchController.java` | 搜索控制器 |
| `ai-services/services/embedding/es_client.py` | ES Python 客户端 |
| `ai-services/services/search/rrf_fusion.py` | RRF 融合算法 |
| `ai-services/api/search.py` | 混合检索 API |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `docker-compose.yml` | 添加 Elasticsearch 服务 |
| `pom.xml` | 添加 ES 依赖版本 |
| `graphrag-common/pom.xml` | 添加 ES 依赖 |
| `ai-services/config/settings.py` | 添加 ES 配置 |
| `ai-services/api/embedding.py` | 支持双存储写入 |
| `ai-services/requirements.txt` | 添加 elasticsearch 依赖 |
| `ai-services/app/main.py` | 注册新的路由 |

---

> **计划状态**: 待确认  
> **预计工期**: 5-6 天
