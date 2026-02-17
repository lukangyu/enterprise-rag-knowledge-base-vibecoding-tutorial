package com.graphrag.gateway.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.graphrag.common.core.domain.ErrorCode;
import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.common.security.dto.*;
import com.graphrag.common.security.entity.User;
import com.graphrag.common.security.entity.UserRole;
import com.graphrag.gateway.mapper.UserMapper;
import com.graphrag.gateway.mapper.UserRoleMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;
    private final PasswordEncoder passwordEncoder;
    private final TokenService tokenService;
    private final UserPermissionCacheService permissionCacheService;

    @Override
    @Transactional
    public User createUser(UserCreateRequest request) {
        User existingUser = userMapper.selectByUsername(request.getUsername());
        if (existingUser != null) {
            throw new BusinessException(ErrorCode.USER_ALREADY_EXISTS);
        }

        User existingEmail = userMapper.selectByEmail(request.getEmail());
        if (existingEmail != null) {
            throw new BusinessException(ErrorCode.USER_ALREADY_EXISTS, "邮箱已被注册");
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setPhone(request.getPhone());
        user.setRealName(request.getRealName());
        user.setGender(request.getGender() != null ? request.getGender() : 0);
        user.setStatus(0);
        user.setDeleted(0);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        userMapper.insert(user);

        if (request.getRoleIds() != null && !request.getRoleIds().isEmpty()) {
            assignRoles(user.getId(), request.getRoleIds());
        }

        log.info("Created user: {}", user.getUsername());
        return user;
    }

    @Override
    @Transactional
    public User updateUser(Long id, UserUpdateRequest request) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        if (StringUtils.hasText(request.getEmail()) && !request.getEmail().equals(user.getEmail())) {
            User existingEmail = userMapper.selectByEmail(request.getEmail());
            if (existingEmail != null) {
                throw new BusinessException(ErrorCode.USER_ALREADY_EXISTS, "邮箱已被注册");
            }
            user.setEmail(request.getEmail());
        }

        if (StringUtils.hasText(request.getPhone())) {
            user.setPhone(request.getPhone());
        }
        if (StringUtils.hasText(request.getRealName())) {
            user.setRealName(request.getRealName());
        }
        if (StringUtils.hasText(request.getAvatar())) {
            user.setAvatar(request.getAvatar());
        }
        if (request.getGender() != null) {
            user.setGender(request.getGender());
        }
        if (request.getStatus() != null) {
            user.setStatus(request.getStatus());
        }
        user.setUpdatedAt(LocalDateTime.now());

        userMapper.updateById(user);

        if (request.getRoleIds() != null) {
            assignRoles(user.getId(), request.getRoleIds());
        }

        permissionCacheService.clearUserPermissionCache(id);
        log.info("Updated user: {}", user.getUsername());
        return user;
    }

    @Override
    @Transactional
    public void deleteUser(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        userMapper.deleteById(id);
        tokenService.removeToken(id);
        permissionCacheService.clearUserPermissionCache(id);

        log.info("Deleted user: {}", user.getUsername());
    }

    @Override
    public User getUserById(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        return user;
    }

    @Override
    public PageResult<User> listUsers(UserQueryRequest request) {
        Page<User> page = new Page<>(request.getPageNum(), request.getPageSize());

        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(StringUtils.hasText(request.getUsername()), User::getUsername, request.getUsername());
        wrapper.like(StringUtils.hasText(request.getEmail()), User::getEmail, request.getEmail());
        wrapper.like(StringUtils.hasText(request.getPhone()), User::getPhone, request.getPhone());
        wrapper.like(StringUtils.hasText(request.getRealName()), User::getRealName, request.getRealName());
        wrapper.eq(request.getStatus() != null, User::getStatus, request.getStatus());
        wrapper.orderByDesc(User::getCreatedAt);

        IPage<User> result = userMapper.selectPage(page, wrapper);

        return PageResult.of(result.getRecords(), result.getTotal(), request.getPageNum().longValue(), request.getPageSize().longValue());
    }

    @Override
    @Transactional
    public void updatePassword(Long id, PasswordUpdateRequest request) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BusinessException(ErrorCode.OLD_PASSWORD_ERROR);
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        tokenService.removeToken(id);
        log.info("Updated password for user: {}", user.getUsername());
    }

    @Override
    @Transactional
    public void assignRoles(Long id, List<Long> roleIds) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        userRoleMapper.deleteByUserId(id);

        if (roleIds != null && !roleIds.isEmpty()) {
            List<UserRole> userRoles = roleIds.stream()
                    .map(roleId -> {
                        UserRole ur = new UserRole();
                        ur.setUserId(id);
                        ur.setRoleId(roleId);
                        ur.setCreatedAt(LocalDateTime.now());
                        return ur;
                    })
                    .collect(Collectors.toList());
            userRoleMapper.batchInsert(userRoles);
        }

        permissionCacheService.clearUserPermissionCache(id);
        log.info("Assigned roles to user {}: {}", user.getUsername(), roleIds);
    }

    @Override
    @Transactional
    public void updateStatus(Long id, Integer status) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        user.setStatus(status);
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        if (status != 0) {
            tokenService.removeToken(id);
        }

        log.info("Updated status for user {}: {}", user.getUsername(), status);
    }

    @Override
    @Transactional
    public void resetPassword(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        String defaultPassword = "123456";
        user.setPassword(passwordEncoder.encode(defaultPassword));
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        tokenService.removeToken(id);
        log.info("Reset password for user: {}", user.getUsername());
    }
}
