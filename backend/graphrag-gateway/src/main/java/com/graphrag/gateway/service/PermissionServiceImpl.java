package com.graphrag.gateway.service;

import com.graphrag.common.core.domain.ErrorCode;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.common.security.dto.PermissionCreateRequest;
import com.graphrag.common.security.dto.PermissionTreeResponse;
import com.graphrag.common.security.entity.Permission;
import com.graphrag.gateway.mapper.PermissionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class PermissionServiceImpl implements PermissionService {

    private final PermissionMapper permissionMapper;

    @Override
    @Transactional
    public Permission createPermission(PermissionCreateRequest request) {
        Permission existingPermission = permissionMapper.selectByPermissionCode(request.getPermissionCode());
        if (existingPermission != null) {
            throw new BusinessException(ErrorCode.CONFLICT, "权限编码已存在");
        }

        Permission permission = new Permission();
        permission.setPermissionCode(request.getPermissionCode());
        permission.setPermissionName(request.getPermissionName());
        permission.setResourceType(request.getResourceType());
        permission.setResourcePath(request.getResourcePath());
        permission.setParentId(request.getParentId() != null ? request.getParentId() : 0L);
        permission.setDescription(request.getDescription());
        permission.setSortOrder(request.getSortOrder() != null ? request.getSortOrder() : 0);
        permission.setStatus(0);
        permission.setDeleted(0);
        permission.setCreatedAt(LocalDateTime.now());
        permission.setUpdatedAt(LocalDateTime.now());

        permissionMapper.insert(permission);
        log.info("Created permission: {}", permission.getPermissionCode());
        return permission;
    }

    @Override
    @Transactional
    public Permission updatePermission(Long id, PermissionCreateRequest request) {
        Permission permission = permissionMapper.selectById(id);
        if (permission == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "权限不存在");
        }

        if (request.getPermissionCode() != null && !request.getPermissionCode().equals(permission.getPermissionCode())) {
            Permission existingPermission = permissionMapper.selectByPermissionCode(request.getPermissionCode());
            if (existingPermission != null) {
                throw new BusinessException(ErrorCode.CONFLICT, "权限编码已存在");
            }
            permission.setPermissionCode(request.getPermissionCode());
        }

        if (request.getPermissionName() != null) {
            permission.setPermissionName(request.getPermissionName());
        }
        if (request.getResourceType() != null) {
            permission.setResourceType(request.getResourceType());
        }
        if (request.getResourcePath() != null) {
            permission.setResourcePath(request.getResourcePath());
        }
        if (request.getParentId() != null) {
            permission.setParentId(request.getParentId());
        }
        if (request.getDescription() != null) {
            permission.setDescription(request.getDescription());
        }
        if (request.getSortOrder() != null) {
            permission.setSortOrder(request.getSortOrder());
        }
        permission.setUpdatedAt(LocalDateTime.now());

        permissionMapper.updateById(permission);
        log.info("Updated permission: {}", permission.getPermissionCode());
        return permission;
    }

    @Override
    @Transactional
    public void deletePermission(Long id) {
        Permission permission = permissionMapper.selectById(id);
        if (permission == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "权限不存在");
        }

        permissionMapper.deleteById(id);
        log.info("Deleted permission: {}", permission.getPermissionCode());
    }

    @Override
    public Permission getPermissionById(Long id) {
        Permission permission = permissionMapper.selectById(id);
        if (permission == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "权限不存在");
        }
        return permission;
    }

    @Override
    public List<Permission> listPermissions() {
        return permissionMapper.selectAllPermissions();
    }

    @Override
    public List<PermissionTreeResponse> getPermissionTree() {
        List<Permission> allPermissions = permissionMapper.selectAllPermissions();
        
        Map<Long, List<Permission>> parentMap = allPermissions.stream()
                .collect(Collectors.groupingBy(Permission::getParentId));

        List<Permission> rootPermissions = parentMap.getOrDefault(0L, new ArrayList<>());

        return rootPermissions.stream()
                .map(p -> buildTree(p, parentMap))
                .collect(Collectors.toList());
    }

    @Override
    public List<Permission> getPermissionsByRoleId(Long roleId) {
        return permissionMapper.selectPermissionsByRoleId(roleId);
    }

    private PermissionTreeResponse buildTree(Permission permission, Map<Long, List<Permission>> parentMap) {
        PermissionTreeResponse response = PermissionTreeResponse.builder()
                .id(permission.getId())
                .permissionCode(permission.getPermissionCode())
                .permissionName(permission.getPermissionName())
                .resourceType(permission.getResourceType())
                .resourcePath(permission.getResourcePath())
                .parentId(permission.getParentId())
                .description(permission.getDescription())
                .sortOrder(permission.getSortOrder())
                .build();

        List<Permission> children = parentMap.getOrDefault(permission.getId(), new ArrayList<>());
        if (!children.isEmpty()) {
            response.setChildren(children.stream()
                    .map(child -> buildTree(child, parentMap))
                    .collect(Collectors.toList()));
        }

        return response;
    }
}
