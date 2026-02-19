package com.graphrag.system.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.system.domain.dto.SystemConfigDTO;
import com.graphrag.system.domain.entity.SystemConfig;
import com.graphrag.system.service.SystemConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(name = "System Config", description = "System configuration management")
@RestController
@RequestMapping("/v1/system/config")
@RequiredArgsConstructor
public class SystemConfigController {
    
    private final SystemConfigService systemConfigService;
    
    @Operation(summary = "Get all system configs")
    @GetMapping
    public Result<Map<String, Object>> getAllConfigs() {
        return Result.success(systemConfigService.getAllConfigs());
    }
    
    @Operation(summary = "Get config by key")
    @GetMapping("/{key}")
    public Result<SystemConfig> getByKey(@PathVariable("key") String configKey) {
        SystemConfig config = systemConfigService.getByKey(configKey);
        if (config == null) {
            return Result.error(404, "Config not found");
        }
        return Result.success(config);
    }
    
    @Operation(summary = "Get configs by type")
    @GetMapping("/type/{type}")
    public Result<List<SystemConfig>> getByType(@PathVariable String type) {
        return Result.success(systemConfigService.getByType(type));
    }
    
    @Operation(summary = "Create or update config")
    @PutMapping
    public Result<SystemConfig> createOrUpdate(@Valid @RequestBody SystemConfigDTO dto) {
        SystemConfig config = systemConfigService.createOrUpdate(dto);
        return Result.success(config);
    }
    
    @Operation(summary = "Update config value")
    @PatchMapping("/{key}")
    public Result<Void> updateValue(
        @PathVariable("key") String configKey,
        @RequestBody Map<String, String> body
    ) {
        String value = body.get("value");
        if (value == null) {
            return Result.error(400, "Value is required");
        }
        systemConfigService.updateValue(configKey, value);
        return Result.success();
    }
    
    @Operation(summary = "Delete config")
    @DeleteMapping("/{key}")
    public Result<Void> deleteByKey(@PathVariable("key") String configKey) {
        systemConfigService.deleteByKey(configKey);
        return Result.success();
    }
}
