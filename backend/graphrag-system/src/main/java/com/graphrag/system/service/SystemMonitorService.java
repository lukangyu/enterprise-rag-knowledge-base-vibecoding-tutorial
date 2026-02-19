package com.graphrag.system.service;

import java.util.Map;

public interface SystemMonitorService {
    
    Map<String, Object> getSystemStatus();
    
    Map<String, Object> getResourceUsage();
    
    Map<String, Object> getStatistics(String period);
    
    Map<String, Object> getAggregatedStatus();
}
