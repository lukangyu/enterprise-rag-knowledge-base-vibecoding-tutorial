package com.graphrag.system.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.Map;

@FeignClient(name = "ai-services", url = "${ai-services.url:http://localhost:8000}")
public interface AIServicesClient {
    
    @GetMapping("/system/status")
    Map<String, Object> getSystemStatus();
    
    @GetMapping("/system/status/resources")
    Map<String, Object> getResourceUsage();
    
    @GetMapping("/system/statistics")
    Map<String, Object> getStatistics(@RequestParam(value = "period", defaultValue = "7d") String period);
    
    @GetMapping("/system/health")
    Map<String, Object> healthCheck();
}
