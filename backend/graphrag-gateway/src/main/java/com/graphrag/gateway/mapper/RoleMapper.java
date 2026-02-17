package com.graphrag.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.common.security.entity.Role;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface RoleMapper extends BaseMapper<Role> {

    @Select("SELECT * FROM roles WHERE role_code = #{roleCode} AND deleted = 0")
    Role selectByRoleCode(@Param("roleCode") String roleCode);

    @Select("""
            SELECT r.* FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = #{userId} AND r.deleted = 0
            """)
    List<Role> selectRolesByUserId(@Param("userId") Long userId);

    @Select("""
            SELECT r.* FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = #{userId}
            """)
    List<Role> selectRolesByUserIdIgnoreDelete(@Param("userId") Long userId);
}
