package com.graphrag.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.common.security.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    @Select("SELECT * FROM users WHERE username = #{username} AND deleted = 0")
    User selectByUsername(@Param("username") String username);

    @Select("SELECT * FROM users WHERE email = #{email} AND deleted = 0")
    User selectByEmail(@Param("email") String email);

    @Select("SELECT * FROM users WHERE phone = #{phone} AND deleted = 0")
    User selectByPhone(@Param("phone") String phone);

    @Select("""
            SELECT r.* FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = #{userId} AND r.deleted = 0
            """)
    List<com.graphrag.common.security.entity.Role> selectRolesByUserId(@Param("userId") Long userId);

    @Select("""
            SELECT DISTINCT p.* FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            INNER JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = #{userId} AND p.deleted = 0
            """)
    List<com.graphrag.common.security.entity.Permission> selectPermissionsByUserId(@Param("userId") Long userId);

    @Select("""
            SELECT DISTINCT p.permission_code FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            INNER JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = #{userId} AND p.deleted = 0
            """)
    List<String> selectPermissionCodesByUserId(@Param("userId") Long userId);

    @Select("""
            SELECT DISTINCT r.role_code FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = #{userId} AND r.deleted = 0
            """)
    List<String> selectRoleCodesByUserId(@Param("userId") Long userId);
}
