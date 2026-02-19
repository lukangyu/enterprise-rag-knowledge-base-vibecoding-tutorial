package com.graphrag.gateway.controller;

import com.graphrag.common.core.domain.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Tag(name = "健康检查", description = "系统健康检查接口")
@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

    @Operation(summary = "健康检查", description = "检查服务是否正常运行")
    @GetMapping
    public Result<Map<String, Object>> health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "UP");
        data.put("service", "graphrag-gateway");
        data.put("timestamp", LocalDateTime.now());
        data.put("version", "1.0.0-SNAPSHOT");
        return Result.success(data);
    }

    @Operation(summary = "就绪检查", description = "检查服务是否就绪")
    @GetMapping("/ready")
    public Result<Map<String, Object>> ready() {
        Map<String, Object> data = new HashMap<>();
        data.put("ready", true);
        data.put("timestamp", LocalDateTime.now());
        return Result.success(data);
    }

    @Operation(summary = "存活检查", description = "检查服务是否存活")
    @GetMapping("/live")
    public Result<Map<String, Object>> live() {
        Map<String, Object> data = new HashMap<>();
        data.put("alive", true);
        data.put("timestamp", LocalDateTime.now());
        return Result.success(data);
    }
}
