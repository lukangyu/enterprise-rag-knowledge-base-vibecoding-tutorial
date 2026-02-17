package com.graphrag.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.common.security.entity.UserRole;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserRoleMapper extends BaseMapper<UserRole> {

    @Select("SELECT * FROM user_roles WHERE user_id = #{userId}")
    List<UserRole> selectByUserId(@Param("userId") Long userId);

    @Select("SELECT * FROM user_roles WHERE role_id = #{roleId}")
    List<UserRole> selectByRoleId(@Param("roleId") Long roleId);

    void deleteByUserId(@Param("userId") Long userId);

    void batchInsert(@Param("list") List<UserRole> list);
}
