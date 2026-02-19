package com.graphrag.system.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.graphrag.system.domain.dto.AuditLogCreateDTO;
import com.graphrag.system.domain.dto.AuditLogQueryDTO;
import com.graphrag.system.domain.entity.AuditLog;

import java.util.List;

public interface AuditLogService {
    
    AuditLog createLog(AuditLogCreateDTO dto);
    
    IPage<AuditLog> queryLogs(AuditLogQueryDTO query);
    
    AuditLog getById(String id);
    
    List<AuditLog> getUserRecentLogs(String userId, Integer limit);
    
    Long countByAction(String action);
}
