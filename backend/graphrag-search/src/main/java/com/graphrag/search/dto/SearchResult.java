package com.graphrag.search.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SearchResult {

    private String docId;

    private String chunkId;

    private String content;

    private Double score;

    private String source;

    private Integer rank;

    private Map<String, Object> metadata;

    private String title;

    private String milvusId;

    private String esId;
}
