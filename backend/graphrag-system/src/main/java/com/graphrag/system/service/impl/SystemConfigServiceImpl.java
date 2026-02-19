package com.graphrag.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.graphrag.system.domain.dto.SystemConfigDTO;
import com.graphrag.system.domain.entity.SystemConfig;
import com.graphrag.system.mapper.SystemConfigMapper;
import com.graphrag.system.service.SystemConfigService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class SystemConfigServiceImpl implements SystemConfigService {
    
    private final SystemConfigMapper systemConfigMapper;
    private final RedisTemplate<String, Object> redisTemplate;
    
    private static final String CONFIG_CACHE_KEY = "system:config:";
    private static final long CONFIG_CACHE_TTL = 600;
    
    @Override
    public Map<String, Object> getAllConfigs() {
        List<SystemConfig> configs = systemConfigMapper.selectList(
            new LambdaQueryWrapper<SystemConfig>()
                .eq(SystemConfig::getStatus, 1)
                .orderByAsc(SystemConfig::getSortOrder)
        );
        
        Map<String, Object> result = new HashMap<>();
        Map<String, Map<String, String>> grouped = new HashMap<>();
        
        for (SystemConfig config : configs) {
            String type = config.getConfigType() != null ? config.getConfigType() : "general";
            grouped.computeIfAbsent(type, k -> new HashMap<String, String>())
                .put(config.getConfigKey(), config.getConfigValue());
        }
        
        result.put("configs", grouped);
        return result;
    }
    
    @Override
    public SystemConfig getByKey(String configKey) {
        String cacheKey = CONFIG_CACHE_KEY + configKey;
        SystemConfig cached = (SystemConfig) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        SystemConfig config = systemConfigMapper.selectByConfigKey(configKey).orElse(null);
        if (config != null) {
            redisTemplate.opsForValue().set(cacheKey, config, CONFIG_CACHE_TTL, TimeUnit.SECONDS);
        }
        
        return config;
    }
    
    @Override
    public List<SystemConfig> getByType(String configType) {
        return systemConfigMapper.selectByConfigType(configType);
    }
    
    @Override
    public SystemConfig createOrUpdate(SystemConfigDTO dto) {
        SystemConfig config = systemConfigMapper.selectByConfigKey(dto.getConfigKey())
            .orElse(new SystemConfig());
        
        config.setConfigKey(dto.getConfigKey());
        config.setConfigValue(dto.getConfigValue());
        config.setConfigType(dto.getConfigType());
        config.setDescription(dto.getDescription());
        config.setSortOrder(dto.getSortOrder());
        config.setStatus(dto.getStatus() != null ? dto.getStatus() : 1);
        
        if (config.getId() == null) {
            config.setCreatedAt(LocalDateTime.now());
            systemConfigMapper.insert(config);
        } else {
            config.setUpdatedAt(LocalDateTime.now());
            systemConfigMapper.updateById(config);
        }
        
        String cacheKey = CONFIG_CACHE_KEY + dto.getConfigKey();
        redisTemplate.delete(cacheKey);
        
        log.info("System config saved: key={}, value={}", dto.getConfigKey(), dto.getConfigValue());
        
        return config;
    }
    
    @Override
    public void deleteByKey(String configKey) {
        systemConfigMapper.delete(
            new LambdaQueryWrapper<SystemConfig>()
                .eq(SystemConfig::getConfigKey, configKey)
        );
        
        String cacheKey = CONFIG_CACHE_KEY + configKey;
        redisTemplate.delete(cacheKey);
        
        log.info("System config deleted: key={}", configKey);
    }
    
    @Override
    public void updateValue(String configKey, String configValue) {
        systemConfigMapper.updateByConfigKey(configKey, configValue);
        
        String cacheKey = CONFIG_CACHE_KEY + configKey;
        redisTemplate.delete(cacheKey);
        
        log.info("System config value updated: key={}", configKey);
    }
}
