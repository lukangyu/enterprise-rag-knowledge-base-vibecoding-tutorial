package com.graphrag.search.service.impl;

import com.graphrag.search.dto.HybridSearchRequest;
import com.graphrag.search.dto.HybridSearchResponse;
import com.graphrag.search.dto.SearchResult;
import com.graphrag.search.enums.FusionStrategy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Slf4j
@Service
@RequiredArgsConstructor
public class HybridSearchService {

    private final KeywordSearchService keywordSearchService;
    private final VectorSearchService vectorSearchService;
    private final RRFFusionService rrfFusionService;
    
    private final ExecutorService executorService = Executors.newFixedThreadPool(2);

    public HybridSearchResponse search(HybridSearchRequest request, float[] queryVector) {
        long totalStartTime = System.currentTimeMillis();
        
        List<SearchResult> keywordResults = new ArrayList<>();
        List<SearchResult> vectorResults = new ArrayList<>();
        long keywordTimeMs = 0;
        long vectorTimeMs = 0;

        if (request.isKeywordEnabled() && request.isVectorEnabled()) {
            CompletableFuture<Long> keywordFuture = CompletableFuture.supplyAsync(() -> {
                try {
                    long start = System.currentTimeMillis();
                    keywordResults.addAll(keywordSearchService.search(
                            request.getQuery(),
                            request.getKeywordTopK(),
                            request.getFilters()
                    ));
                    return System.currentTimeMillis() - start;
                } catch (IOException e) {
                    log.error("Keyword search failed", e);
                    return 0L;
                }
            }, executorService);

            CompletableFuture<Long> vectorFuture = CompletableFuture.supplyAsync(() -> {
                try {
                    long start = System.currentTimeMillis();
                    vectorResults.addAll(vectorSearchService.search(
                            queryVector,
                            request.getVectorTopK(),
                            request.getDocIds()
                    ));
                    return System.currentTimeMillis() - start;
                } catch (Exception e) {
                    log.error("Vector search failed", e);
                    return 0L;
                }
            }, executorService);

            CompletableFuture.allOf(keywordFuture, vectorFuture).join();
            keywordTimeMs = keywordFuture.join();
            vectorTimeMs = vectorFuture.join();
        } else if (request.isKeywordEnabled()) {
            try {
                long start = System.currentTimeMillis();
                keywordResults = keywordSearchService.search(
                        request.getQuery(),
                        request.getKeywordTopK(),
                        request.getFilters()
                );
                keywordTimeMs = System.currentTimeMillis() - start;
            } catch (IOException e) {
                log.error("Keyword search failed", e);
            }
        } else if (request.isVectorEnabled()) {
            try {
                long start = System.currentTimeMillis();
                vectorResults = vectorSearchService.search(
                        queryVector,
                        request.getVectorTopK(),
                        request.getDocIds()
                );
                vectorTimeMs = System.currentTimeMillis() - start;
            } catch (Exception e) {
                log.error("Vector search failed", e);
            }
        }

        long fusionStartTime = System.currentTimeMillis();
        List<SearchResult> fusedResults;
        
        if (request.getStrategy() == FusionStrategy.RRF) {
            fusedResults = rrfFusionService.fuse(keywordResults, vectorResults, request.getRrfK());
        } else if (request.getStrategy() == FusionStrategy.WEIGHTED) {
            fusedResults = rrfFusionService.weightedFuse(keywordResults, vectorResults, 0.3, 0.7);
        } else {
            fusedResults = new ArrayList<>();
            fusedResults.addAll(keywordResults);
            fusedResults.addAll(vectorResults);
            fusedResults.sort((a, b) -> Double.compare(
                    b.getScore() != null ? b.getScore() : 0.0,
                    a.getScore() != null ? a.getScore() : 0.0
            ));
        }

        if (fusedResults.size() > request.getTopK()) {
            fusedResults = fusedResults.subList(0, request.getTopK());
        }

        long fusionTimeMs = System.currentTimeMillis() - fusionStartTime;
        long totalTimeMs = System.currentTimeMillis() - totalStartTime;

        log.info("Hybrid search completed: keyword={} results ({}ms), vector={} results ({}ms), " +
                "fusion={} results ({}ms), total={}ms",
                keywordResults.size(), keywordTimeMs,
                vectorResults.size(), vectorTimeMs,
                fusedResults.size(), fusionTimeMs,
                totalTimeMs);

        return HybridSearchResponse.builder()
                .results(fusedResults)
                .keywordTimeMs(keywordTimeMs)
                .vectorTimeMs(vectorTimeMs)
                .fusionTimeMs(fusionTimeMs)
                .totalTimeMs(totalTimeMs)
                .keywordResultCount(keywordResults.size())
                .vectorResultCount(vectorResults.size())
                .finalResultCount(fusedResults.size())
                .build();
    }

    public List<SearchResult> keywordOnlySearch(String query, int topK) throws IOException {
        return keywordSearchService.search(query, topK);
    }

    public List<SearchResult> vectorOnlySearch(float[] queryVector, int topK) throws Exception {
        return vectorSearchService.search(queryVector, topK);
    }
}
