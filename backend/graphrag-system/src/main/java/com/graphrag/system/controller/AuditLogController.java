package com.graphrag.system.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.domain.Result;
import com.graphrag.system.domain.dto.AuditLogCreateDTO;
import com.graphrag.system.domain.dto.AuditLogQueryDTO;
import com.graphrag.system.domain.entity.AuditLog;
import com.graphrag.system.service.AuditLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Tag(name = "Audit Log", description = "Audit log management")
@RestController
@RequestMapping("/v1/system/audit-logs")
@RequiredArgsConstructor
public class AuditLogController {
    
    private final AuditLogService auditLogService;
    
    @Operation(summary = "Query audit logs")
    @GetMapping
    public Result<PageResult<AuditLog>> queryLogs(AuditLogQueryDTO query) {
        IPage<AuditLog> page = auditLogService.queryLogs(query);
        PageResult<AuditLog> result = PageResult.of(
            page.getRecords(),
            page.getTotal(),
            page.getCurrent(),
            page.getSize()
        );
        return Result.success(result);
    }
    
    @Operation(summary = "Get audit log by ID")
    @GetMapping("/{id}")
    public Result<AuditLog> getById(@PathVariable String id) {
        AuditLog log = auditLogService.getById(id);
        if (log == null) {
            return Result.error(404, "Audit log not found");
        }
        return Result.success(log);
    }
    
    @Operation(summary = "Create audit log")
    @PostMapping
    public Result<AuditLog> createLog(@Valid @RequestBody AuditLogCreateDTO dto) {
        AuditLog log = auditLogService.createLog(dto);
        return Result.success(log);
    }
    
    @Operation(summary = "Get user recent logs")
    @GetMapping("/user/{userId}/recent")
    public Result<Map<String, Object>> getUserRecentLogs(
        @PathVariable String userId,
        @RequestParam(defaultValue = "10") Integer limit
    ) {
        List<AuditLog> logs = auditLogService.getUserRecentLogs(userId, limit);
        Map<String, Object> result = new HashMap<>();
        result.put("userId", userId);
        result.put("logs", logs);
        return Result.success(result);
    }
    
    @Operation(summary = "Get audit summary")
    @GetMapping("/stats/summary")
    public Result<Map<String, Object>> getSummary(
        @RequestParam(defaultValue = "7") Integer days
    ) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("periodDays", days);
        summary.put("totalLogs", auditLogService.countByAction(null));
        summary.put("loginCount", auditLogService.countByAction("login"));
        summary.put("createCount", auditLogService.countByAction("create"));
        summary.put("updateCount", auditLogService.countByAction("update"));
        summary.put("deleteCount", auditLogService.countByAction("delete"));
        return Result.success(summary);
    }
}
