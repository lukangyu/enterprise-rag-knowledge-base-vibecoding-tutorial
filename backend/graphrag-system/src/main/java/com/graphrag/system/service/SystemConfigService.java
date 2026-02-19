package com.graphrag.system.service;

import com.graphrag.system.domain.dto.SystemConfigDTO;
import com.graphrag.system.domain.entity.SystemConfig;

import java.util.List;
import java.util.Map;

public interface SystemConfigService {
    
    Map<String, Object> getAllConfigs();
    
    SystemConfig getByKey(String configKey);
    
    List<SystemConfig> getByType(String configType);
    
    SystemConfig createOrUpdate(SystemConfigDTO dto);
    
    void deleteByKey(String configKey);
    
    void updateValue(String configKey, String configValue);
}
