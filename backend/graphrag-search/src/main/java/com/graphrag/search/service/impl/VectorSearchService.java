package com.graphrag.search.service.impl;

import com.graphrag.search.dto.SearchResult;
import io.milvus.v2.client.MilvusClientV2;
import io.milvus.v2.service.vector.request.DeleteReq;
import io.milvus.v2.service.vector.request.InsertReq;
import io.milvus.v2.service.vector.request.SearchReq;
import io.milvus.v2.service.vector.request.data.FloatVec;
import io.milvus.v2.service.vector.response.SearchResp;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class VectorSearchService {

    private final MilvusClientV2 milvusClient;

    @Value("${milvus.collection.doc-chunks:doc_chunks}")
    private String docChunksCollection;

    public List<SearchResult> search(float[] queryVector, int topK) throws Exception {
        return search(queryVector, topK, null);
    }

    public List<SearchResult> search(float[] queryVector, int topK, List<String> docIds) throws Exception {
        long startTime = System.currentTimeMillis();

        FloatVec queryData = new FloatVec(queryVector);

        SearchReq.SearchReqBuilder builder = SearchReq.builder()
                .collectionName(docChunksCollection)
                .data(Collections.singletonList(queryData))
                .topK(topK)
                .fieldName("embedding");

        if (docIds != null && !docIds.isEmpty()) {
            String filter = "doc_id in " + docIds.stream()
                    .map(id -> "\"" + id + "\"")
                    .collect(Collectors.joining(", ", "[", "]"));
            builder.filter(filter);
        }

        SearchResp searchResp = milvusClient.search(builder.build());

        List<SearchResult> results = new ArrayList<>();
        List<List<SearchResp.SearchResult>> searchResults = searchResp.getSearchResults();
        
        if (searchResults != null && !searchResults.isEmpty()) {
            int rank = 1;
            for (SearchResp.SearchResult hit : searchResults.get(0)) {
                SearchResult result = SearchResult.builder()
                        .docId((String) hit.getEntity().get("doc_id"))
                        .chunkId((String) hit.getEntity().get("chunk_id"))
                        .content((String) hit.getEntity().get("content"))
                        .score((double) hit.getScore())
                        .rank(rank++)
                        .source("vector")
                        .build();

                Object metadata = hit.getEntity().get("metadata");
                if (metadata instanceof Map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> metaMap = (Map<String, Object>) metadata;
                    result.setMetadata(metaMap);
                }

                results.add(result);
            }
        }

        long duration = System.currentTimeMillis() - startTime;
        log.info("Vector search completed: {} results in {}ms", results.size(), duration);

        return results;
    }

    public void insertVectors(String docId, List<String> chunkIds, List<float[]> vectors, 
                               List<String> contents) throws Exception {
        if (chunkIds.size() != vectors.size() || chunkIds.size() != contents.size()) {
            throw new IllegalArgumentException("chunkIds, vectors, and contents must have the same size");
        }

        List<Map<String, Object>> data = new ArrayList<>();
        for (int i = 0; i < chunkIds.size(); i++) {
            Map<String, Object> row = new HashMap<>();
            row.put("id", UUID.randomUUID().toString());
            row.put("doc_id", docId);
            row.put("chunk_id", chunkIds.get(i));
            row.put("content", contents.get(i));
            row.put("embedding", vectors.get(i));
            data.add(row);
        }

        milvusClient.insert(InsertReq.builder()
                .collectionName(docChunksCollection)
                .data(data)
                .build());

        log.info("Inserted {} vectors for docId={}", vectors.size(), docId);
    }

    public void deleteVectors(String docId) throws Exception {
        String filter = "doc_id == \"" + docId + "\"";
        
        milvusClient.delete(DeleteReq.builder()
                .collectionName(docChunksCollection)
                .filter(filter)
                .build());

        log.info("Deleted vectors for docId={}", docId);
    }
}
