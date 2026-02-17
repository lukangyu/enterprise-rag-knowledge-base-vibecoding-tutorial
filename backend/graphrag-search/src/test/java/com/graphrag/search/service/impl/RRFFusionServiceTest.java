package com.graphrag.search.service.impl;

import com.graphrag.search.dto.SearchResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class RRFFusionServiceTest {

    private RRFFusionService rrfFusionService;

    @BeforeEach
    void setUp() {
        rrfFusionService = new RRFFusionService();
    }

    @Test
    void testFuse_withBothResults() {
        List<SearchResult> keywordResults = Arrays.asList(
                createSearchResult("doc1", "chunk1", 0.9),
                createSearchResult("doc2", "chunk2", 0.8),
                createSearchResult("doc3", "chunk3", 0.7)
        );

        List<SearchResult> vectorResults = Arrays.asList(
                createSearchResult("doc2", "chunk2", 0.95),
                createSearchResult("doc4", "chunk4", 0.85),
                createSearchResult("doc1", "chunk1", 0.75)
        );

        List<SearchResult> fusedResults = rrfFusionService.fuse(keywordResults, vectorResults, 60);

        assertNotNull(fusedResults);
        assertEquals(4, fusedResults.size());

        SearchResult topResult = fusedResults.get(0);
        assertEquals("doc2", topResult.getDocId());
        assertEquals(1, topResult.getRank());
    }

    @Test
    void testFuse_withEmptyKeywordResults() {
        List<SearchResult> keywordResults = List.of();

        List<SearchResult> vectorResults = Arrays.asList(
                createSearchResult("doc1", "chunk1", 0.9),
                createSearchResult("doc2", "chunk2", 0.8)
        );

        List<SearchResult> fusedResults = rrfFusionService.fuse(keywordResults, vectorResults, 60);

        assertNotNull(fusedResults);
        assertEquals(2, fusedResults.size());
    }

    @Test
    void testFuse_withEmptyVectorResults() {
        List<SearchResult> keywordResults = Arrays.asList(
                createSearchResult("doc1", "chunk1", 0.9),
                createSearchResult("doc2", "chunk2", 0.8)
        );

        List<SearchResult> vectorResults = List.of();

        List<SearchResult> fusedResults = rrfFusionService.fuse(keywordResults, vectorResults, 60);

        assertNotNull(fusedResults);
        assertEquals(2, fusedResults.size());
    }

    @Test
    void testFuse_withBothEmptyResults() {
        List<SearchResult> keywordResults = List.of();
        List<SearchResult> vectorResults = List.of();

        List<SearchResult> fusedResults = rrfFusionService.fuse(keywordResults, vectorResults, 60);

        assertNotNull(fusedResults);
        assertTrue(fusedResults.isEmpty());
    }

    @Test
    void testWeightedFuse_withBothResults() {
        List<SearchResult> keywordResults = Arrays.asList(
                createSearchResult("doc1", "chunk1", 0.9),
                createSearchResult("doc2", "chunk2", 0.8)
        );

        List<SearchResult> vectorResults = Arrays.asList(
                createSearchResult("doc1", "chunk1", 0.95),
                createSearchResult("doc3", "chunk3", 0.85)
        );

        List<SearchResult> fusedResults = rrfFusionService.weightedFuse(keywordResults, vectorResults, 0.3, 0.7);

        assertNotNull(fusedResults);
        assertEquals(3, fusedResults.size());

        for (int i = 0; i < fusedResults.size() - 1; i++) {
            assertTrue(fusedResults.get(i).getScore() >= fusedResults.get(i + 1).getScore());
        }
    }

    private SearchResult createSearchResult(String docId, String chunkId, double score) {
        return SearchResult.builder()
                .docId(docId)
                .chunkId(chunkId)
                .score(score)
                .build();
    }
}
