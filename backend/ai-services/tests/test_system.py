import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from api.system.config import ConfigManager
from api.system.status import HealthCheckService, get_uptime
from api.system.audit import AuditService
from api.system.statistics import StatisticsService
from models.system_models import (
    SystemConfig, AuditLogCreate, AuditLogQuery,
    DocumentStats, KGStats, UserStats
)


class TestConfigManager:
    @pytest.fixture
    def config_manager(self):
        return ConfigManager()
    
    def test_get_config(self, config_manager):
        config = config_manager.get_config()
        assert isinstance(config, SystemConfig)
        assert config.general is not None
        assert config.search is not None
    
    def test_get_category_config(self, config_manager):
        general_config = config_manager.get_category_config("general")
        assert isinstance(general_config, dict)
        assert "site_name" in general_config
    
    def test_update_config(self, config_manager):
        success = config_manager.update_config(
            "general",
            "site_name",
            "Test Site"
        )
        assert success is True
        
        config = config_manager.get_config()
        assert config.general["site_name"] == "Test Site"


class TestHealthCheckService:
    @pytest.fixture
    def health_service(self):
        return HealthCheckService()
    
    def test_increment_query_count(self, health_service):
        initial = health_service.get_query_count()
        health_service.increment_query_count()
        assert health_service.get_query_count() == initial + 1
    
    def test_reset_query_count(self, health_service):
        health_service.increment_query_count()
        health_service.reset_query_count()
        assert health_service.get_query_count() == 0
    
    def test_get_uptime(self):
        uptime = get_uptime()
        assert "d" in uptime
        assert "h" in uptime
        assert "m" in uptime


class TestAuditService:
    @pytest.fixture
    def audit_service(self):
        return AuditService()
    
    def test_create_log(self, audit_service):
        log_create = AuditLogCreate(
            user_id="user_001",
            username="test_user",
            action="login",
            resource_type="auth",
            ip_address="127.0.0.1"
        )
        
        log = audit_service.create_log(log_create)
        
        assert log.id.startswith("log_")
        assert log.user_id == "user_001"
        assert log.action == "login"
        assert log.created_at is not None
    
    def test_query_logs(self, audit_service):
        log_create = AuditLogCreate(
            user_id="user_001",
            username="test_user",
            action="login",
            resource_type="auth",
            ip_address="127.0.0.1"
        )
        audit_service.create_log(log_create)
        
        query = AuditLogQuery(page=1, size=10)
        logs, total = audit_service.query_logs(query)
        
        assert total >= 1
        assert len(logs) >= 1
    
    def test_query_logs_with_filter(self, audit_service):
        log_create = AuditLogCreate(
            user_id="user_001",
            username="test_user",
            action="create",
            resource_type="document",
            ip_address="127.0.0.1"
        )
        audit_service.create_log(log_create)
        
        query = AuditLogQuery(page=1, size=10, action="create")
        logs, total = audit_service.query_logs(query)
        
        assert total >= 1
        for log in logs:
            assert log.action == "create"
    
    def test_get_user_recent_logs(self, audit_service):
        log_create = AuditLogCreate(
            user_id="user_001",
            username="test_user",
            action="login",
            resource_type="auth",
            ip_address="127.0.0.1"
        )
        audit_service.create_log(log_create)
        
        logs = audit_service.get_user_recent_logs("user_001", limit=5)
        
        assert len(logs) >= 1
        for log in logs:
            assert log.user_id == "user_001"


class TestStatisticsService:
    @pytest.fixture
    def stats_service(self):
        return StatisticsService()
    
    def test_record_query(self, stats_service):
        stats_service.record_query(response_time_ms=100.0, satisfaction=4.5)
        
        query_stats = stats_service.get_query_stats(days=1)
        assert query_stats.total_queries >= 1
    
    def test_update_document_stats(self, stats_service):
        doc_stats = DocumentStats(
            total=100,
            new_this_period=10,
            by_type={"pdf": 50, "docx": 50},
            by_status={"published": 90, "processing": 10}
        )
        
        stats_service.update_document_stats(doc_stats)
        
        assert stats_service._document_stats.total == 100
    
    def test_update_kg_stats(self, stats_service):
        kg_stats = KGStats(
            total_entities=1000,
            total_relations=5000,
            entity_types={"Person": 500, "Organization": 300},
            relation_types={"BELONGS_TO": 2000}
        )
        
        stats_service.update_kg_stats(kg_stats)
        
        assert stats_service._kg_stats.total_entities == 1000
    
    def test_get_query_stats_empty(self, stats_service):
        stats_service._query_history = []
        
        query_stats = stats_service.get_query_stats(days=7)
        
        assert query_stats.total_queries == 0
        assert query_stats.avg_response_time_ms == 0.0


class TestSystemModels:
    def test_system_config_defaults(self):
        config = SystemConfig()
        
        assert config.general["site_name"] == "GraphRAG知识库系统"
        assert config.search["default_top_k"] == 10
        assert config.llm["default_model"] == "qwen2.5-max"
    
    def test_audit_log_create(self):
        log_create = AuditLogCreate(
            user_id="user_001",
            username="test_user",
            action="create",
            resource_type="document",
            resource_id="doc_001",
            ip_address="127.0.0.1"
        )
        
        assert log_create.user_id == "user_001"
        assert log_create.action == "create"
        assert log_create.resource_id == "doc_001"
    
    def test_audit_log_query_defaults(self):
        query = AuditLogQuery()
        
        assert query.page == 1
        assert query.size == 20
        assert query.action is None
