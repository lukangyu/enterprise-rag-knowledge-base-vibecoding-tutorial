package com.graphrag.search.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HybridSearchResponse {

    private List<SearchResult> results;

    private long keywordTimeMs;

    private long vectorTimeMs;

    private long fusionTimeMs;

    private long totalTimeMs;

    private int keywordResultCount;

    private int vectorResultCount;

    private int finalResultCount;
}
