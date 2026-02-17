package com.graphrag.search.dto;

import com.graphrag.search.enums.FusionStrategy;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HybridSearchRequest {

    private String query;

    @Builder.Default
    private int topK = 20;

    @Builder.Default
    private boolean keywordEnabled = true;

    @Builder.Default
    private boolean vectorEnabled = true;

    private Map<String, Object> filters;

    @Builder.Default
    private FusionStrategy strategy = FusionStrategy.RRF;

    private List<String> docIds;

    @Builder.Default
    private int keywordTopK = 100;

    @Builder.Default
    private int vectorTopK = 100;

    @Builder.Default
    private int rrfK = 60;
}
