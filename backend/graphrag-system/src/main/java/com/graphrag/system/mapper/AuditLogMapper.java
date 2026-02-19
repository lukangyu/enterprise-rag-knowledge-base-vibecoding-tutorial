package com.graphrag.system.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.graphrag.system.domain.entity.AuditLog;
import com.graphrag.system.domain.dto.AuditLogQueryDTO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface AuditLogMapper extends BaseMapper<AuditLog> {
    
    IPage<AuditLog> selectPageByQuery(Page<AuditLog> page, @Param("query") AuditLogQueryDTO query);
    
    List<AuditLog> selectByUserId(@Param("userId") String userId, @Param("limit") Integer limit);
    
    Long countByAction(@Param("action") String action);
}
