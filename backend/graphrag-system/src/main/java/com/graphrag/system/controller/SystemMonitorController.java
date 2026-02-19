package com.graphrag.system.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.system.service.SystemMonitorService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Tag(name = "System Monitor", description = "System monitoring and statistics")
@RestController
@RequestMapping("/api/v1/system")
@RequiredArgsConstructor
public class SystemMonitorController {
    
    private final SystemMonitorService systemMonitorService;
    
    @Operation(summary = "Get aggregated system status")
    @GetMapping("/status")
    public Result<Map<String, Object>> getSystemStatus() {
        return Result.success(systemMonitorService.getAggregatedStatus());
    }
    
    @Operation(summary = "Get Java service resource usage")
    @GetMapping("/status/resources")
    public Result<Map<String, Object>> getResourceUsage() {
        return Result.success(systemMonitorService.getResourceUsage());
    }
    
    @Operation(summary = "Get system statistics")
    @GetMapping("/statistics")
    public Result<Map<String, Object>> getStatistics(
        @RequestParam(defaultValue = "7d") String period
    ) {
        return Result.success(systemMonitorService.getStatistics(period));
    }
    
    @Operation(summary = "Health check")
    @GetMapping("/health")
    public Result<Map<String, Object>> healthCheck() {
        Map<String, Object> health = systemMonitorService.getAggregatedStatus();
        boolean healthy = "healthy".equals(((Map<?, ?>) health.get("overall")).get("status"));
        
        if (healthy) {
            return Result.success(Map.of(
                "status", "healthy",
                "timestamp", health.get("timestamp")
            ));
        } else {
            return Result.error(503, "Service degraded");
        }
    }
}
