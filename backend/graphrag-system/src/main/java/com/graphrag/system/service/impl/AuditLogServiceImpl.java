package com.graphrag.system.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.graphrag.system.domain.dto.AuditLogCreateDTO;
import com.graphrag.system.domain.dto.AuditLogQueryDTO;
import com.graphrag.system.domain.entity.AuditLog;
import com.graphrag.system.mapper.AuditLogMapper;
import com.graphrag.system.service.AuditLogService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuditLogServiceImpl implements AuditLogService {
    
    private final AuditLogMapper auditLogMapper;
    
    @Override
    public AuditLog createLog(AuditLogCreateDTO dto) {
        AuditLog auditLog = new AuditLog();
        auditLog.setUserId(dto.getUserId());
        auditLog.setUsername(dto.getUsername());
        auditLog.setAction(dto.getAction());
        auditLog.setResourceType(dto.getResourceType());
        auditLog.setResourceId(dto.getResourceId());
        auditLog.setDetails(dto.getDetails());
        auditLog.setIpAddress(dto.getIpAddress());
        auditLog.setUserAgent(dto.getUserAgent());
        auditLog.setStatus(dto.getStatus() != null ? dto.getStatus() : "success");
        auditLog.setErrorMessage(dto.getErrorMessage());
        auditLog.setCreatedAt(LocalDateTime.now());
        
        auditLogMapper.insert(auditLog);
        
        log.info("Audit log created: user={}, action={}, resource={}/{}", 
            dto.getUsername(), dto.getAction(), dto.getResourceType(), dto.getResourceId());
        
        return auditLog;
    }
    
    @Override
    public IPage<AuditLog> queryLogs(AuditLogQueryDTO query) {
        Page<AuditLog> page = new Page<>(query.getPage(), query.getSize());
        return auditLogMapper.selectPageByQuery(page, query);
    }
    
    @Override
    public AuditLog getById(String id) {
        return auditLogMapper.selectById(id);
    }
    
    @Override
    public List<AuditLog> getUserRecentLogs(String userId, Integer limit) {
        return auditLogMapper.selectByUserId(userId, limit != null ? limit : 10);
    }
    
    @Override
    public Long countByAction(String action) {
        return auditLogMapper.countByAction(action);
    }
}
