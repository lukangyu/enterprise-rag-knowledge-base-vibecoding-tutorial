import pytest
from services.search.rrf_fusion import RRFFusion


class TestRRFFusion:
    
    @pytest.fixture
    def rrf_fusion(self):
        return RRFFusion(k=60)
    
    def test_fuse_with_both_results(self, rrf_fusion):
        keyword_results = [
            {"doc_id": "doc1", "chunk_id": "chunk1", "_score": 0.9},
            {"doc_id": "doc2", "chunk_id": "chunk2", "_score": 0.8},
            {"doc_id": "doc3", "chunk_id": "chunk3", "_score": 0.7},
        ]
        
        vector_results = [
            {"doc_id": "doc2", "chunk_id": "chunk2", "score": 0.95},
            {"doc_id": "doc4", "chunk_id": "chunk4", "score": 0.85},
            {"doc_id": "doc1", "chunk_id": "chunk1", "score": 0.75},
        ]
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        assert len(fused_results) == 4
        assert fused_results[0]["doc_id"] == "doc2"
        assert fused_results[0]["rank"] == 1
    
    def test_fuse_with_empty_keyword_results(self, rrf_fusion):
        keyword_results = []
        
        vector_results = [
            {"doc_id": "doc1", "chunk_id": "chunk1", "score": 0.9},
            {"doc_id": "doc2", "chunk_id": "chunk2", "score": 0.8},
        ]
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        assert len(fused_results) == 2
    
    def test_fuse_with_empty_vector_results(self, rrf_fusion):
        keyword_results = [
            {"doc_id": "doc1", "chunk_id": "chunk1", "_score": 0.9},
            {"doc_id": "doc2", "chunk_id": "chunk2", "_score": 0.8},
        ]
        
        vector_results = []
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        assert len(fused_results) == 2
    
    def test_fuse_with_both_empty_results(self, rrf_fusion):
        keyword_results = []
        vector_results = []
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        assert len(fused_results) == 0
    
    def test_fuse_with_custom_k(self, rrf_fusion):
        keyword_results = [
            {"doc_id": "doc1", "_score": 0.9},
        ]
        
        vector_results = [
            {"doc_id": "doc1", "score": 0.95},
        ]
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results, k=10)
        
        assert len(fused_results) == 1
        assert fused_results[0]["doc_id"] == "doc1"
    
    def test_weighted_fuse(self, rrf_fusion):
        keyword_results = [
            {"doc_id": "doc1", "_score": 0.9},
            {"doc_id": "doc2", "_score": 0.8},
        ]
        
        vector_results = [
            {"doc_id": "doc1", "score": 0.95},
            {"doc_id": "doc3", "score": 0.85},
        ]
        
        fused_results = rrf_fusion.weighted_fuse(
            keyword_results, 
            vector_results, 
            keyword_weight=0.3, 
            vector_weight=0.7
        )
        
        assert len(fused_results) == 3
        
        for i in range(len(fused_results) - 1):
            assert fused_results[i]["weighted_score"] >= fused_results[i + 1]["weighted_score"]
    
    def test_fuse_scores_decreasing(self, rrf_fusion):
        keyword_results = [
            {"doc_id": f"doc{i}", "_score": 0.9 - i * 0.1}
            for i in range(5)
        ]
        
        vector_results = [
            {"doc_id": f"doc{i}", "score": 0.95 - i * 0.1}
            for i in range(5)
        ]
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        for i in range(len(fused_results) - 1):
            assert fused_results[i]["rrf_score"] >= fused_results[i + 1]["rrf_score"]
