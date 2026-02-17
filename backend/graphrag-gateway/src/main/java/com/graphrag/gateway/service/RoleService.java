package com.graphrag.gateway.service;

import com.graphrag.common.security.entity.Role;

import java.util.List;

public interface RoleService {

    Role createRole(com.graphrag.common.security.dto.RoleCreateRequest request);

    Role updateRole(Long id, com.graphrag.common.security.dto.RoleUpdateRequest request);

    void deleteRole(Long id);

    Role getRoleById(Long id);

    List<Role> listRoles();

    void assignPermissions(Long id, List<Long> permissionIds);

    List<Long> getPermissionIds(Long id);
}
