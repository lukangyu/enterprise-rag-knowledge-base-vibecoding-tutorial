package com.graphrag.common.storage.es;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch.core.SearchRequest;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.elasticsearch.indices.CreateIndexRequest;
import co.elastic.clients.elasticsearch.indices.CreateIndexResponse;
import co.elastic.clients.elasticsearch.indices.ExistsRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class ElasticsearchClientWrapper {

    private final ElasticsearchClient client;

    public boolean createIndex(String indexName, Map<String, Object> settings, Map<String, Object> mappings) throws IOException {
        CreateIndexRequest request = CreateIndexRequest.of(builder ->
                builder.index(indexName)
                        .settings(s -> s.otherSettings(settings.toString()))
                        .mappings(m -> m.properties(mappings.toString()))
        );
        CreateIndexResponse response = client.indices().create(request);
        log.info("Created index: {}, acknowledged: {}", indexName, response.acknowledged());
        return response.acknowledged();
    }

    public boolean indexExists(String indexName) throws IOException {
        ExistsRequest request = ExistsRequest.of(builder -> builder.index(indexName));
        return client.indices().exists(request).value();
    }

    public void indexDocument(String indexName, String id, Map<String, Object> document) throws IOException {
        client.index(i -> i
                .index(indexName)
                .id(id)
                .document(document)
        );
        log.debug("Indexed document: {} in index: {}", id, indexName);
    }

    public void bulkIndex(String indexName, List<Map<String, Object>> documents) throws IOException {
        client.bulk(b -> {
            for (Map<String, Object> doc : documents) {
                String id = (String) doc.get("id");
                if (id == null) {
                    id = java.util.UUID.randomUUID().toString();
                }
                b.operations(op -> op.index(idx ->
                        idx.index(indexName).id(id).document(doc)
                ));
            }
            return b;
        });
        log.info("Bulk indexed {} documents in index: {}", documents.size(), indexName);
    }

    public void deleteDocument(String indexName, String id) throws IOException {
        client.delete(d -> d.index(indexName).id(id));
        log.debug("Deleted document: {} from index: {}", id, indexName);
    }

    public void deleteByQuery(String indexName, Query query) throws IOException {
        client.deleteByQuery(d -> d
                .index(indexName)
                .query(query)
        );
        log.info("Deleted documents by query from index: {}", indexName);
    }

    public List<Map<String, Object>> search(String indexName, Query query, int from, int size) throws IOException {
        SearchRequest request = SearchRequest.of(s -> s
                .index(indexName)
                .query(query)
                .from(from)
                .size(size)
        );

        SearchResponse<Map> response = client.search(request, Map.class);
        List<Map<String, Object>> results = new ArrayList<>();
        
        for (Hit<Map> hit : response.hits().hits()) {
            Map<String, Object> result = hit.source();
            if (result != null) {
                result.put("_id", hit.id());
                result.put("_score", hit.score());
                results.add(result);
            }
        }
        
        log.debug("Search returned {} results from index: {}", results.size(), indexName);
        return results;
    }

    public List<Map<String, Object>> keywordSearch(String indexName, String field, String text, int topK) throws IOException {
        Query query = Query.of(q -> q
                .match(m -> m
                        .field(field)
                        .query(text)
                )
        );
        return search(indexName, query, 0, topK);
    }

    public List<Map<String, Object>> bm25Search(String indexName, String text, List<String> fields, int topK) throws IOException {
        Query query = Query.of(q -> q
                .multiMatch(m -> m
                        .fields(fields)
                        .query(text)
                )
        );
        return search(indexName, query, 0, topK);
    }

    public long count(String indexName, Query query) throws IOException {
        return client.count(c -> c.index(indexName).query(query)).count();
    }

    public void close() throws IOException {
        client.shutdown();
        log.info("Elasticsearch client closed");
    }
}
