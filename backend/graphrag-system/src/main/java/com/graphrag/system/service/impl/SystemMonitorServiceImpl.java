package com.graphrag.system.service.impl;

import com.graphrag.system.client.AIServicesClient;
import com.graphrag.system.service.SystemMonitorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.OperatingSystemMXBean;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class SystemMonitorServiceImpl implements SystemMonitorService {
    
    private final AIServicesClient aiServicesClient;
    
    @Override
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        
        OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        
        status.put("java", Map.of(
            "status", "healthy",
            "cpu_usage", Math.round(osBean.getSystemLoadAverage() * 100) / 100.0,
            "memory_used", memoryBean.getHeapMemoryUsage().getUsed() / (1024 * 1024),
            "memory_max", memoryBean.getHeapMemoryUsage().getMax() / (1024 * 1024),
            "available_processors", osBean.getAvailableProcessors(),
            "timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        ));
        
        return status;
    }
    
    @Override
    public Map<String, Object> getResourceUsage() {
        Map<String, Object> usage = new HashMap<>();
        
        OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        
        double cpuUsage = osBean.getSystemLoadAverage() / osBean.getAvailableProcessors() * 100;
        long memoryUsed = memoryBean.getHeapMemoryUsage().getUsed();
        long memoryMax = memoryBean.getHeapMemoryUsage().getMax();
        double memoryUsage = (double) memoryUsed / memoryMax * 100;
        
        usage.put("cpu_usage", Math.round(cpuUsage * 10) / 10.0);
        usage.put("memory_usage", Math.round(memoryUsage * 10) / 10.0);
        usage.put("memory_used_mb", memoryUsed / (1024 * 1024));
        usage.put("memory_max_mb", memoryMax / (1024 * 1024));
        
        return usage;
    }
    
    @Override
    public Map<String, Object> getStatistics(String period) {
        try {
            return aiServicesClient.getStatistics(period);
        } catch (Exception e) {
            log.error("Failed to get statistics from AI services: {}", e.getMessage());
            Map<String, Object> fallback = new HashMap<>();
            fallback.put("error", "AI services unavailable");
            fallback.put("period", period);
            return fallback;
        }
    }
    
    @Override
    public Map<String, Object> getAggregatedStatus() {
        Map<String, Object> aggregated = new HashMap<>();
        
        Map<String, Object> javaStatus = getSystemStatus();
        aggregated.put("java", javaStatus.get("java"));
        
        try {
            Map<String, Object> pythonStatus = aiServicesClient.getSystemStatus();
            aggregated.put("python", pythonStatus.getOrDefault("data", pythonStatus));
        } catch (Exception e) {
            log.error("Failed to get Python status: {}", e.getMessage());
            aggregated.put("python", Map.of(
                "status", "unavailable",
                "error", e.getMessage()
            ));
        }
        
        boolean allHealthy = "healthy".equals(((Map<?, ?>) javaStatus.get("java")).get("status"));
        try {
            Map<String, Object> pythonData = (Map<String, Object>) aggregated.get("python");
            allHealthy = allHealthy && "healthy".equals(pythonData.get("status"));
        } catch (Exception ignored) {}
        
        aggregated.put("overall", Map.of(
            "status", allHealthy ? "healthy" : "degraded",
            "timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        ));
        
        return aggregated;
    }
}
