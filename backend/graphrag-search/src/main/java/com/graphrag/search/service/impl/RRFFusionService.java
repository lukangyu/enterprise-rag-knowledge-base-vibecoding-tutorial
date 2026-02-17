package com.graphrag.search.service.impl;

import com.graphrag.search.dto.SearchResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
public class RRFFusionService {

    private static final int DEFAULT_K = 60;

    public List<SearchResult> fuse(
            List<SearchResult> keywordResults,
            List<SearchResult> vectorResults,
            int k
    ) {
        long startTime = System.currentTimeMillis();
        
        Map<String, Double> scores = new HashMap<>();
        Map<String, SearchResult> resultMap = new HashMap<>();

        for (int rank = 1; rank <= keywordResults.size(); rank++) {
            SearchResult result = keywordResults.get(rank - 1);
            String docId = result.getDocId();
            double score = 1.0 / (k + rank);
            scores.merge(docId, score, Double::sum);
            resultMap.putIfAbsent(docId, result);
            log.debug("Keyword rank {}: docId={}, score contribution={}", rank, docId, score);
        }

        for (int rank = 1; rank <= vectorResults.size(); rank++) {
            SearchResult result = vectorResults.get(rank - 1);
            String docId = result.getDocId();
            double score = 1.0 / (k + rank);
            scores.merge(docId, score, Double::sum);
            
            if (!resultMap.containsKey(docId)) {
                resultMap.put(docId, result);
            } else {
                SearchResult existing = resultMap.get(docId);
                if (existing.getContent() == null && result.getContent() != null) {
                    resultMap.put(docId, result);
                }
            }
            log.debug("Vector rank {}: docId={}, score contribution={}", rank, docId, score);
        }

        List<SearchResult> fusedResults = scores.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
                .map(entry -> {
                    SearchResult result = resultMap.get(entry.getKey());
                    result.setScore(entry.getValue());
                    return result;
                })
                .collect(Collectors.toList());

        for (int i = 0; i < fusedResults.size(); i++) {
            fusedResults.get(i).setRank(i + 1);
        }

        long duration = System.currentTimeMillis() - startTime;
        log.info("RRF fusion completed: {} results fused in {}ms", fusedResults.size(), duration);
        
        return fusedResults;
    }

    public List<SearchResult> fuse(
            List<SearchResult> keywordResults,
            List<SearchResult> vectorResults
    ) {
        return fuse(keywordResults, vectorResults, DEFAULT_K);
    }

    public List<SearchResult> weightedFuse(
            List<SearchResult> keywordResults,
            List<SearchResult> vectorResults,
            double keywordWeight,
            double vectorWeight
    ) {
        long startTime = System.currentTimeMillis();
        
        Map<String, Double> scores = new HashMap<>();
        Map<String, SearchResult> resultMap = new HashMap<>();

        double maxKeywordScore = keywordResults.stream()
                .mapToDouble(r -> r.getScore() != null ? r.getScore() : 0.0)
                .max()
                .orElse(1.0);
        
        double maxVectorScore = vectorResults.stream()
                .mapToDouble(r -> r.getScore() != null ? r.getScore() : 0.0)
                .max()
                .orElse(1.0);

        for (SearchResult result : keywordResults) {
            String docId = result.getDocId();
            double normalizedScore = (result.getScore() != null ? result.getScore() : 0.0) / maxKeywordScore;
            double weightedScore = normalizedScore * keywordWeight;
            scores.merge(docId, weightedScore, Double::sum);
            resultMap.putIfAbsent(docId, result);
        }

        for (SearchResult result : vectorResults) {
            String docId = result.getDocId();
            double normalizedScore = (result.getScore() != null ? result.getScore() : 0.0) / maxVectorScore;
            double weightedScore = normalizedScore * vectorWeight;
            scores.merge(docId, weightedScore, Double::sum);
            
            if (!resultMap.containsKey(docId)) {
                resultMap.put(docId, result);
            }
        }

        List<SearchResult> fusedResults = scores.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
                .map(entry -> {
                    SearchResult result = resultMap.get(entry.getKey());
                    result.setScore(entry.getValue());
                    return result;
                })
                .collect(Collectors.toList());

        for (int i = 0; i < fusedResults.size(); i++) {
            fusedResults.get(i).setRank(i + 1);
        }

        long duration = System.currentTimeMillis() - startTime;
        log.info("Weighted fusion completed: {} results fused in {}ms", fusedResults.size(), duration);
        
        return fusedResults;
    }
}
