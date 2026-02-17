import pytest
from io import BytesIO


class TestHealthAPI:
    def test_health_check(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data


class TestChunkerAPI:
    def test_chunk_text(self, client, sample_text):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": sample_text,
                "doc_id": "test-doc",
                "strategy": "semantic"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_chunks" in data
        assert data["total_chunks"] >= 1

    def test_chunk_with_fixed_strategy(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": "这是一段测试内容，用于验证固定大小分块功能。",
                "strategy": "fixed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_used"] == "fixed"

    def test_chunk_with_auto_strategy(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": "测试内容",
                "doc_type": "pdf",
                "strategy": "auto"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_used"] == "semantic"

    def test_chunk_response_structure(self, client, sample_text):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": sample_text,
                "doc_id": "test-doc-001"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "chunks" in data
        assert "total_chunks" in data
        assert "strategy_used" in data
        assert "chunk_time_ms" in data

        if len(data["chunks"]) > 0:
            chunk = data["chunks"][0]
            assert "chunk_id" in chunk
            assert "content" in chunk
            assert "position" in chunk
            assert "metadata" in chunk

    def test_chunk_with_custom_params(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": "这是一段测试内容，用于验证自定义参数。",
                "chunk_size": 256,
                "overlap_rate": 0.2
            }
        )

        assert response.status_code == 200

    def test_chunk_empty_content(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": ""
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] == 0


class TestAPIValidation:
    def test_missing_content_field(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "doc_id": "test"
            }
        )

        assert response.status_code == 422

    def test_invalid_json(self, client):
        response = client.post(
            "/api/v1/chunk",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_invalid_strategy_value(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": "测试内容",
                "strategy": "invalid_strategy"
            }
        )

        assert response.status_code == 422
