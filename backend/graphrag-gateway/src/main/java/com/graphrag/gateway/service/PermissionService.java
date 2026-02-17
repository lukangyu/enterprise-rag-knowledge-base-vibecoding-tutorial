package com.graphrag.gateway.service;

import com.graphrag.common.security.dto.PermissionCreateRequest;
import com.graphrag.common.security.dto.PermissionTreeResponse;
import com.graphrag.common.security.entity.Permission;

import java.util.List;

public interface PermissionService {

    Permission createPermission(PermissionCreateRequest request);

    Permission updatePermission(Long id, PermissionCreateRequest request);

    void deletePermission(Long id);

    Permission getPermissionById(Long id);

    List<Permission> listPermissions();

    List<PermissionTreeResponse> getPermissionTree();

    List<Permission> getPermissionsByRoleId(Long roleId);
}
