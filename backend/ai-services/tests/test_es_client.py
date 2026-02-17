import pytest
from unittest.mock import Mock, patch, MagicMock


class TestElasticsearchClient:
    
    @pytest.fixture
    def mock_es_client(self):
        with patch('services.embedding.es_client.Elasticsearch') as mock_es:
            mock_instance = MagicMock()
            mock_es.return_value = mock_instance
            yield mock_instance
    
    def test_search_returns_results(self, mock_es_client):
        from services.embedding.es_client import ElasticsearchClient
        
        mock_es_client.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "doc1_chunk1",
                        "_score": 0.95,
                        "_source": {
                            "doc_id": "doc1",
                            "chunk_id": "chunk1",
                            "content": "test content"
                        }
                    }
                ]
            }
        }
        
        with patch('services.embedding.es_client.settings') as mock_settings:
            mock_settings.ES_HOST = "localhost"
            mock_settings.ES_PORT = 9200
            mock_settings.ES_SCHEME = "http"
            mock_settings.ES_INDEX = "doc_index"
            mock_settings.ES_USERNAME = None
            mock_settings.ES_PASSWORD = None
            
            client = ElasticsearchClient()
            results = client.search("test query", top_k=10)
            
            assert len(results) == 1
            assert results[0]["doc_id"] == "doc1"
            assert results[0]["_score"] == 0.95
    
    def test_index_document(self, mock_es_client):
        from services.embedding.es_client import ElasticsearchClient
        
        mock_es_client.index.return_value = {"result": "created", "_id": "doc1_chunk1"}
        
        with patch('services.embedding.es_client.settings') as mock_settings:
            mock_settings.ES_HOST = "localhost"
            mock_settings.ES_PORT = 9200
            mock_settings.ES_SCHEME = "http"
            mock_settings.ES_INDEX = "doc_index"
            mock_settings.ES_USERNAME = None
            mock_settings.ES_PASSWORD = None
            
            client = ElasticsearchClient()
            response = client.index_document(
                doc_id="doc1",
                chunk_id="chunk1",
                content="test content"
            )
            
            assert response["result"] == "created"
            mock_es_client.index.assert_called_once()
    
    def test_delete_document(self, mock_es_client):
        from services.embedding.es_client import ElasticsearchClient
        
        mock_es_client.delete_by_query.return_value = {"deleted": 5}
        
        with patch('services.embedding.es_client.settings') as mock_settings:
            mock_settings.ES_HOST = "localhost"
            mock_settings.ES_PORT = 9200
            mock_settings.ES_SCHEME = "http"
            mock_settings.ES_INDEX = "doc_index"
            mock_settings.ES_USERNAME = None
            mock_settings.ES_PASSWORD = None
            
            client = ElasticsearchClient()
            result = client.delete_document("doc1")
            
            assert result is True
            mock_es_client.delete_by_query.assert_called_once()
    
    def test_bulk_index(self, mock_es_client):
        from services.embedding.es_client import ElasticsearchClient
        
        with patch('services.embedding.es_client.bulk') as mock_bulk:
            mock_bulk.return_value = (3, [])
            
            with patch('services.embedding.es_client.settings') as mock_settings:
                mock_settings.ES_HOST = "localhost"
                mock_settings.ES_PORT = 9200
                mock_settings.ES_SCHEME = "http"
                mock_settings.ES_INDEX = "doc_index"
                mock_settings.ES_USERNAME = None
                mock_settings.ES_PASSWORD = None
                
                client = ElasticsearchClient()
                
                documents = [
                    {"doc_id": "doc1", "chunk_id": "chunk1", "content": "content1"},
                    {"doc_id": "doc1", "chunk_id": "chunk2", "content": "content2"},
                    {"doc_id": "doc1", "chunk_id": "chunk3", "content": "content3"},
                ]
                
                success_count = client.bulk_index(documents)
                
                assert success_count == 3
