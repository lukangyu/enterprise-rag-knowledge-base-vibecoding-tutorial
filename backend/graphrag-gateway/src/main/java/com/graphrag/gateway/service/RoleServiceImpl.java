package com.graphrag.gateway.service;

import com.graphrag.common.core.domain.ErrorCode;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.common.security.dto.RoleCreateRequest;
import com.graphrag.common.security.dto.RoleUpdateRequest;
import com.graphrag.common.security.entity.Role;
import com.graphrag.common.security.entity.RolePermission;
import com.graphrag.gateway.mapper.RoleMapper;
import com.graphrag.gateway.mapper.RolePermissionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class RoleServiceImpl implements RoleService {

    private final RoleMapper roleMapper;
    private final RolePermissionMapper rolePermissionMapper;
    private final UserPermissionCacheService permissionCacheService;

    @Override
    @Transactional
    public Role createRole(RoleCreateRequest request) {
        Role existingRole = roleMapper.selectByRoleCode(request.getRoleCode());
        if (existingRole != null) {
            throw new BusinessException(ErrorCode.CONFLICT, "角色编码已存在");
        }

        Role role = new Role();
        role.setRoleCode(request.getRoleCode());
        role.setRoleName(request.getRoleName());
        role.setDescription(request.getDescription());
        role.setSortOrder(request.getSortOrder() != null ? request.getSortOrder() : 0);
        role.setStatus(0);
        role.setDeleted(0);
        role.setCreatedAt(LocalDateTime.now());
        role.setUpdatedAt(LocalDateTime.now());

        roleMapper.insert(role);
        log.info("Created role: {}", role.getRoleCode());
        return role;
    }

    @Override
    @Transactional
    public Role updateRole(Long id, RoleUpdateRequest request) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "角色不存在");
        }

        if (request.getRoleName() != null) {
            role.setRoleName(request.getRoleName());
        }
        if (request.getDescription() != null) {
            role.setDescription(request.getDescription());
        }
        if (request.getStatus() != null) {
            role.setStatus(request.getStatus());
        }
        if (request.getSortOrder() != null) {
            role.setSortOrder(request.getSortOrder());
        }
        role.setUpdatedAt(LocalDateTime.now());

        roleMapper.updateById(role);

        if (request.getPermissionIds() != null) {
            assignPermissions(id, request.getPermissionIds());
        }

        log.info("Updated role: {}", role.getRoleCode());
        return role;
    }

    @Override
    @Transactional
    public void deleteRole(Long id) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "角色不存在");
        }

        roleMapper.deleteById(id);
        rolePermissionMapper.deleteByRoleId(id);

        log.info("Deleted role: {}", role.getRoleCode());
    }

    @Override
    public Role getRoleById(Long id) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "角色不存在");
        }
        return role;
    }

    @Override
    public List<Role> listRoles() {
        return roleMapper.selectList(null);
    }

    @Override
    @Transactional
    public void assignPermissions(Long id, List<Long> permissionIds) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "角色不存在");
        }

        rolePermissionMapper.deleteByRoleId(id);

        if (permissionIds != null && !permissionIds.isEmpty()) {
            List<RolePermission> rolePermissions = permissionIds.stream()
                    .map(permissionId -> {
                        RolePermission rp = new RolePermission();
                        rp.setRoleId(id);
                        rp.setPermissionId(permissionId);
                        rp.setCreatedAt(LocalDateTime.now());
                        return rp;
                    })
                    .collect(Collectors.toList());
            rolePermissionMapper.batchInsert(rolePermissions);
        }

        log.info("Assigned permissions to role {}: {}", role.getRoleCode(), permissionIds);
    }

    @Override
    public List<Long> getPermissionIds(Long id) {
        List<RolePermission> rolePermissions = rolePermissionMapper.selectByRoleId(id);
        return rolePermissions.stream()
                .map(RolePermission::getPermissionId)
                .collect(Collectors.toList());
    }
}
