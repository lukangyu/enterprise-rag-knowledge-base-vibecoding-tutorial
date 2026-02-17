package com.graphrag.search.service.impl;

import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery;
import com.graphrag.common.core.constant.ElasticsearchConstants;
import com.graphrag.common.storage.es.ElasticsearchClientWrapper;
import com.graphrag.search.dto.SearchResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class KeywordSearchService {

    private final ElasticsearchClientWrapper esClient;

    public List<SearchResult> search(String query, int topK) throws IOException {
        return search(query, topK, null);
    }

    public List<SearchResult> search(String query, int topK, Map<String, Object> filters) throws IOException {
        long startTime = System.currentTimeMillis();
        
        List<String> searchFields = Arrays.asList(
                ElasticsearchConstants.FIELD_CONTENT,
                ElasticsearchConstants.FIELD_TITLE,
                ElasticsearchConstants.FIELD_KEYWORDS
        );

        Query searchQuery = buildSearchQuery(query, filters);

        List<Map<String, Object>> results = esClient.search(
                ElasticsearchConstants.DOC_INDEX,
                searchQuery,
                0,
                topK
        );

        List<SearchResult> searchResults = results.stream()
                .map(this::mapToSearchResult)
                .collect(Collectors.toList());

        long duration = System.currentTimeMillis() - startTime;
        log.info("Keyword search completed: query='{}', {} results in {}ms", query, searchResults.size(), duration);
        
        return searchResults;
    }

    private Query buildSearchQuery(String query, Map<String, Object> filters) {
        BoolQuery.Builder boolBuilder = new BoolQuery.Builder();

        boolBuilder.must(m -> m
                .multiMatch(mm -> mm
                        .fields(ElasticsearchConstants.FIELD_CONTENT, ElasticsearchConstants.FIELD_TITLE)
                        .query(query)
                )
        );

        if (filters != null && !filters.isEmpty()) {
            addFilters(boolBuilder, filters);
        }

        return Query.of(q -> q.bool(boolBuilder.build()));
    }

    private void addFilters(BoolQuery.Builder boolBuilder, Map<String, Object> filters) {
        if (filters.containsKey(ElasticsearchConstants.FIELD_DOC_TYPE)) {
            boolBuilder.filter(f -> f
                    .term(t -> t
                            .field(ElasticsearchConstants.FIELD_DOC_TYPE)
                            .value(filters.get(ElasticsearchConstants.FIELD_DOC_TYPE).toString())
                    )
            );
        }

        if (filters.containsKey(ElasticsearchConstants.FIELD_CATEGORY)) {
            boolBuilder.filter(f -> f
                    .term(t -> t
                            .field(ElasticsearchConstants.FIELD_CATEGORY)
                            .value(filters.get(ElasticsearchConstants.FIELD_CATEGORY).toString())
                    )
            );
        }

        if (filters.containsKey(ElasticsearchConstants.FIELD_TAGS)) {
            Object tagsValue = filters.get(ElasticsearchConstants.FIELD_TAGS);
            if (tagsValue instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> tags = (List<String>) tagsValue;
                for (String tag : tags) {
                    boolBuilder.filter(f -> f
                            .term(t -> t
                                    .field(ElasticsearchConstants.FIELD_TAGS)
                                    .value(tag)
                            )
                    );
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    private SearchResult mapToSearchResult(Map<String, Object> map) {
        SearchResult result = SearchResult.builder()
                .docId((String) map.get(ElasticsearchConstants.FIELD_DOC_ID))
                .chunkId((String) map.get(ElasticsearchConstants.FIELD_CHUNK_ID))
                .content((String) map.get(ElasticsearchConstants.FIELD_CONTENT))
                .title((String) map.get(ElasticsearchConstants.FIELD_TITLE))
                .milvusId((String) map.get(ElasticsearchConstants.FIELD_MILVUS_ID))
                .esId((String) map.get("_id"))
                .build();

        Object score = map.get("_score");
        if (score != null) {
            result.setScore(((Number) score).doubleValue());
        }

        Object metadata = map.get(ElasticsearchConstants.FIELD_METADATA);
        if (metadata instanceof Map) {
            result.setMetadata((Map<String, Object>) metadata);
        }

        return result;
    }

    public void indexDocument(String docId, String chunkId, String content, 
                              String title, Map<String, Object> metadata) throws IOException {
        Map<String, Object> document = new HashMap<>();
        document.put(ElasticsearchConstants.FIELD_DOC_ID, docId);
        document.put(ElasticsearchConstants.FIELD_CHUNK_ID, chunkId);
        document.put(ElasticsearchConstants.FIELD_CONTENT, content);
        document.put(ElasticsearchConstants.FIELD_TITLE, title);
        document.put(ElasticsearchConstants.FIELD_METADATA, metadata);
        document.put(ElasticsearchConstants.FIELD_CREATED_AT, new Date());

        String id = docId + "_" + chunkId;
        esClient.indexDocument(ElasticsearchConstants.DOC_INDEX, id, document);
        log.info("Indexed document: docId={}, chunkId={}", docId, chunkId);
    }

    public void deleteDocument(String docId) throws IOException {
        Query query = Query.of(q -> q
                .term(t -> t
                        .field(ElasticsearchConstants.FIELD_DOC_ID)
                        .value(docId)
                )
        );
        esClient.deleteByQuery(ElasticsearchConstants.DOC_INDEX, query);
        log.info("Deleted document from ES: docId={}", docId);
    }
}
