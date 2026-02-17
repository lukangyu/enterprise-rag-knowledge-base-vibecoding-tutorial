package com.graphrag.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.common.security.entity.RolePermission;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface RolePermissionMapper extends BaseMapper<RolePermission> {

    @Select("SELECT * FROM role_permissions WHERE role_id = #{roleId}")
    List<RolePermission> selectByRoleId(@Param("roleId") Long roleId);

    void deleteByRoleId(@Param("roleId") Long roleId);

    void batchInsert(@Param("list") List<RolePermission> list);
}
