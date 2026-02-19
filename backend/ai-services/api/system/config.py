from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
import json
from pathlib import Path

from models.system_models import SystemConfig, ConfigUpdate, ConfigCategory
from config.settings import settings

router = APIRouter(prefix="/system", tags=["系统配置"])
logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "config" / "dynamic_config.json"


class ConfigManager:
    _instance = None
    _config: Optional[SystemConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = SystemConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
                self._config = SystemConfig()
        else:
            self._config = SystemConfig()
    
    def _save_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config.model_dump(), f, ensure_ascii=False, indent=2)
    
    def get_config(self) -> SystemConfig:
        return self._config
    
    def get_category_config(self, category: str) -> Dict[str, Any]:
        return getattr(self._config, category, {}).copy()
    
    def update_config(self, category: str, key: str, value: Any) -> bool:
        if not hasattr(self._config, category):
            return False
        
        category_config = getattr(self._config, category)
        if isinstance(category_config, dict):
            category_config[key] = value
            self._save_config()
            return True
        return False
    
    def update_category(self, category: str, config: Dict[str, Any]) -> bool:
        if not hasattr(self._config, category):
            return False
        
        setattr(self._config, category, config)
        self._save_config()
        return True


config_manager = ConfigManager()


@router.get("/config")
async def get_system_config() -> Dict[str, Any]:
    """获取系统配置"""
    config = config_manager.get_config()
    return {
        "code": 200,
        "message": "success",
        "data": config.model_dump()
    }


@router.get("/config/{category}")
async def get_category_config(category: str) -> Dict[str, Any]:
    """获取指定分类的配置"""
    if category not in [c.value for c in ConfigCategory]:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    config = config_manager.get_category_config(category)
    return {
        "code": 200,
        "message": "success",
        "data": config
    }


@router.put("/config")
async def update_system_config(config: SystemConfig) -> Dict[str, Any]:
    """更新系统配置"""
    config_manager._config = config
    config_manager._save_config()
    
    logger.info(f"System config updated")
    
    return {
        "code": 200,
        "message": "Config updated successfully",
        "data": {"updated_at": "now"}
    }


@router.patch("/config")
async def patch_config(update: ConfigUpdate) -> Dict[str, Any]:
    """部分更新配置"""
    success = config_manager.update_config(
        update.category.value,
        update.key,
        update.value
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update config")
    
    logger.info(f"Config updated: {update.category.value}.{update.key} = {update.value}")
    
    return {
        "code": 200,
        "message": "Config updated successfully",
        "data": {
            "category": update.category.value,
            "key": update.key,
            "value": update.value
        }
    }


@router.post("/config/reset")
async def reset_config() -> Dict[str, Any]:
    """重置配置为默认值"""
    config_manager._config = SystemConfig()
    config_manager._save_config()
    
    logger.info("System config reset to default")
    
    return {
        "code": 200,
        "message": "Config reset to default",
        "data": config_manager._config.model_dump()
    }
