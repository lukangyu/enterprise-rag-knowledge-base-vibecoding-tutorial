package com.graphrag.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.common.security.entity.Permission;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface PermissionMapper extends BaseMapper<Permission> {

    @Select("SELECT * FROM permissions WHERE permission_code = #{permissionCode} AND deleted = 0")
    Permission selectByPermissionCode(@Param("permissionCode") String permissionCode);

    @Select("""
            SELECT DISTINCT p.* FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = #{roleId} AND p.deleted = 0
            ORDER BY p.sort_order
            """)
    List<Permission> selectPermissionsByRoleId(@Param("roleId") Long roleId);

    @Select("""
            SELECT DISTINCT p.* FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            INNER JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = #{userId} AND p.deleted = 0
            ORDER BY p.sort_order
            """)
    List<Permission> selectPermissionsByUserId(@Param("userId") Long userId);

    @Select("SELECT * FROM permissions WHERE deleted = 0 ORDER BY parent_id, sort_order")
    List<Permission> selectAllPermissions();

    @Select("SELECT * FROM permissions WHERE parent_id = #{parentId} AND deleted = 0 ORDER BY sort_order")
    List<Permission> selectByParentId(@Param("parentId") Long parentId);

    @Select("""
            SELECT DISTINCT p.permission_code FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            INNER JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = #{userId} AND p.deleted = 0
            """)
    List<String> selectPermissionCodesByUserId(@Param("userId") Long userId);
}
