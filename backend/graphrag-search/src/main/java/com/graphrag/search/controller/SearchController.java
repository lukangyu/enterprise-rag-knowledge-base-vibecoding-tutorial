package com.graphrag.search.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.search.dto.HybridSearchRequest;
import com.graphrag.search.dto.HybridSearchResponse;
import com.graphrag.search.dto.SearchResult;
import com.graphrag.search.service.impl.HybridSearchService;
import com.graphrag.search.service.impl.KeywordSearchService;
import com.graphrag.search.service.impl.VectorSearchService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/v1/search")
@RequiredArgsConstructor
@Tag(name = "混合检索", description = "关键词检索、向量检索、混合检索API")
public class SearchController {

    private final HybridSearchService hybridSearchService;
    private final KeywordSearchService keywordSearchService;
    private final VectorSearchService vectorSearchService;

    @PostMapping("/hybrid")
    @Operation(summary = "混合检索", description = "执行关键词+向量混合检索，使用RRF融合算法")
    public Result<HybridSearchResponse> hybridSearch(
            @RequestBody HybridSearchRequest request,
            @RequestParam float[] queryVector
    ) {
        log.info("Hybrid search request: query={}, topK={}", request.getQuery(), request.getTopK());
        HybridSearchResponse response = hybridSearchService.search(request, queryVector);
        return Result.success(response);
    }

    @GetMapping("/keyword")
    @Operation(summary = "关键词检索", description = "使用Elasticsearch BM25算法执行关键词检索")
    public Result<List<SearchResult>> keywordSearch(
            @RequestParam String query,
            @RequestParam(defaultValue = "20") int topK
    ) throws IOException {
        log.info("Keyword search request: query={}, topK={}", query, topK);
        List<SearchResult> results = keywordSearchService.search(query, topK);
        return Result.success(results);
    }

    @GetMapping("/vector")
    @Operation(summary = "向量检索", description = "使用Milvus执行向量相似度检索")
    public Result<List<SearchResult>> vectorSearch(
            @RequestParam float[] queryVector,
            @RequestParam(defaultValue = "20") int topK
    ) throws Exception {
        log.info("Vector search request: topK={}", topK);
        List<SearchResult> results = vectorSearchService.search(queryVector, topK);
        return Result.success(results);
    }

    @PostMapping("/hybrid/simple")
    @Operation(summary = "简单混合检索", description = "简化版混合检索接口，仅需提供查询文本和向量")
    public Result<HybridSearchResponse> simpleHybridSearch(
            @RequestParam String query,
            @RequestParam float[] queryVector,
            @RequestParam(defaultValue = "20") int topK
    ) {
        log.info("Simple hybrid search request: query={}, topK={}", query, topK);
        
        HybridSearchRequest request = HybridSearchRequest.builder()
                .query(query)
                .topK(topK)
                .keywordEnabled(true)
                .vectorEnabled(true)
                .build();
        
        HybridSearchResponse response = hybridSearchService.search(request, queryVector);
        return Result.success(response);
    }
}
