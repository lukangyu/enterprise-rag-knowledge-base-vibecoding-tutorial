package com.graphrag.search.service.impl;

import com.graphrag.search.dto.SearchResult;
import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.MutationResult;
import io.milvus.grpc.SearchResults;
import io.milvus.param.R;
import io.milvus.param.dml.DeleteParam;
import io.milvus.param.dml.InsertParam;
import io.milvus.param.dml.SearchParam;
import io.milvus.param.MetricType;
import io.milvus.response.MutationResultWrapper;
import io.milvus.response.SearchResultsWrapper;
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

    private final MilvusServiceClient milvusClient;

    @Value("${milvus.collection.doc-chunks:doc_chunks}")
    private String docChunksCollection;

    @Value("${milvus.embedding.dimension:1536}")
    private int embeddingDimension;

    public List<SearchResult> search(float[] queryVector, int topK) throws Exception {
        return search(queryVector, topK, null);
    }

    @SuppressWarnings("deprecation")
    public List<SearchResult> search(float[] queryVector, int topK, List<String> docIds) throws Exception {
        long startTime = System.currentTimeMillis();

        List<Float> floatList = new ArrayList<>();
        for (float f : queryVector) {
            floatList.add(f);
        }
        List<List<Float>> queryVectors = Collections.singletonList(floatList);

        String expr = null;
        if (docIds != null && !docIds.isEmpty()) {
            expr = "doc_id in " + docIds.stream()
                    .map(id -> "'" + id + "'")
                    .collect(Collectors.joining(", ", "[", "]"));
        }

        SearchParam.Builder searchParamBuilder = SearchParam.newBuilder()
                .withCollectionName(docChunksCollection)
                .withMetricType(MetricType.COSINE)
                .withTopK(topK)
                .withVectors(queryVectors)
                .withVectorFieldName("embedding")
                .addOutField("doc_id")
                .addOutField("chunk_id")
                .addOutField("content")
                .addOutField("metadata");

        if (expr != null) {
            searchParamBuilder.withExpr(expr);
        }

        SearchParam searchParam = searchParamBuilder.build();

        R<SearchResults> response = milvusClient.search(searchParam);
        if (response.getStatus() != R.Status.Success.getCode()) {
            throw new RuntimeException("Search failed: " + response.getMessage());
        }

        SearchResultsWrapper wrapper = new SearchResultsWrapper(response.getData().getResults());
        List<SearchResult> results = new ArrayList<>();
        int rank = 1;

        List<SearchResultsWrapper.IDScore> idScores = wrapper.getIDScore(0);
        for (SearchResultsWrapper.IDScore idScore : idScores) {
            SearchResult result = SearchResult.builder()
                    .docId(String.valueOf(idScore.get("doc_id")))
                    .chunkId(String.valueOf(idScore.get("chunk_id")))
                    .content(String.valueOf(idScore.get("content")))
                    .score((double) idScore.getScore())
                    .rank(rank++)
                    .source("vector")
                    .build();

            Object metadata = idScore.get("metadata");
            if (metadata != null) {
                result.setMetadata(Collections.singletonMap("metadata", metadata));
            }

            results.add(result);
        }

        long duration = System.currentTimeMillis() - startTime;
        log.info("Vector search completed: {} results in {}ms", results.size(), duration);

        return results;
    }

    public List<Long> insertVectors(String docId, List<String> chunkIds, List<float[]> vectors, 
                               List<String> contents) throws Exception {
        if (chunkIds.size() != vectors.size() || chunkIds.size() != contents.size()) {
            throw new IllegalArgumentException("chunkIds, vectors, and contents must have the same size");
        }

        List<InsertParam.Field> fields = new ArrayList<>();
        List<String> docIds = new ArrayList<>();
        List<String> chunkIdList = new ArrayList<>();
        List<String> contentList = new ArrayList<>();
        List<List<Float>> vectorList = new ArrayList<>();

        for (int i = 0; i < chunkIds.size(); i++) {
            docIds.add(docId);
            chunkIdList.add(chunkIds.get(i));
            contentList.add(contents.get(i));
            
            List<Float> floatList = new ArrayList<>();
            for (float f : vectors.get(i)) {
                floatList.add(f);
            }
            vectorList.add(floatList);
        }

        fields.add(new InsertParam.Field("doc_id", docIds));
        fields.add(new InsertParam.Field("chunk_id", chunkIdList));
        fields.add(new InsertParam.Field("content", contentList));
        fields.add(new InsertParam.Field("embedding", vectorList));

        InsertParam insertParam = InsertParam.newBuilder()
                .withCollectionName(docChunksCollection)
                .withFields(fields)
                .build();

        R<MutationResult> response = milvusClient.insert(insertParam);
        if (response.getStatus() != R.Status.Success.getCode()) {
            throw new RuntimeException("Insert failed: " + response.getMessage());
        }

        MutationResultWrapper resultWrapper = new MutationResultWrapper(response.getData());
        List<Long> ids = resultWrapper.getLongIDs();
        log.info("Inserted {} vectors for docId={}", vectors.size(), docId);

        return ids;
    }

    public void deleteVectors(String docId) throws Exception {
        String expr = "doc_id in ['" + docId + "']";
        
        DeleteParam deleteParam = DeleteParam.newBuilder()
                .withCollectionName(docChunksCollection)
                .withExpr(expr)
                .build();

        R<MutationResult> response = milvusClient.delete(deleteParam);
        if (response.getStatus() != R.Status.Success.getCode()) {
            throw new RuntimeException("Delete failed: " + response.getMessage());
        }

        log.info("Deleted vectors for docId={}", docId);
    }
}
