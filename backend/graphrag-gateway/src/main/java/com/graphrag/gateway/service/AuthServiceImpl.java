package com.graphrag.gateway.service;

import com.graphrag.common.security.dto.*;
import com.graphrag.common.security.entity.Role;
import com.graphrag.common.security.entity.User;
import com.graphrag.common.security.jwt.JwtProperties;
import com.graphrag.common.security.jwt.JwtTokenProvider;
import com.graphrag.common.core.domain.ErrorCode;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.gateway.mapper.UserMapper;
import com.graphrag.gateway.security.LoginUser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final JwtTokenProvider jwtTokenProvider;
    private final JwtProperties jwtProperties;
    private final TokenService tokenService;
    private final UserPermissionCacheService permissionCacheService;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public LoginResponse login(LoginRequest request) {
        User user = userMapper.selectByUsername(request.getUsername());
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BusinessException(ErrorCode.PASSWORD_ERROR);
        }

        if (user.getStatus() != 0) {
            throw new BusinessException(ErrorCode.ACCOUNT_DISABLED);
        }

        List<String> roleCodes = userMapper.selectRoleCodesByUserId(user.getId());
        List<String> permissions = userMapper.selectPermissionCodesByUserId(user.getId());

        String accessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roleCodes, permissions);
        String refreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), user.getUsername());

        tokenService.storeAccessToken(user.getId(), accessToken, jwtProperties.getAccessTokenExpire());
        tokenService.storeRefreshToken(user.getId(), refreshToken, jwtProperties.getRefreshTokenExpire());

        permissionCacheService.cacheUserRoles(user.getId(), roleCodes);
        permissionCacheService.cacheUserPermissions(user.getId(), permissions);

        updateLoginInfo(user);

        log.info("User logged in: {}", user.getUsername());

        UserInfoResponse userInfo = buildUserInfoResponse(user, roleCodes, permissions);

        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtProperties.getAccessTokenExpire())
                .userInfo(userInfo)
                .build();
    }

    @Override
    @Transactional
    public void register(RegisterRequest request) {
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
        user.setStatus(0);
        user.setDeleted(0);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        userMapper.insert(user);

        log.info("User registered: {}", user.getUsername());
    }

    @Override
    public void logout() {
        LoginUser loginUser = getLoginUser();
        if (loginUser != null) {
            tokenService.removeToken(loginUser.getUserId());
            permissionCacheService.clearUserPermissionCache(loginUser.getUserId());
            log.info("User logged out: {}", loginUser.getUsername());
        }
        SecurityContextHolder.clearContext();
    }

    @Override
    @Transactional
    public LoginResponse refreshToken(RefreshTokenRequest request) {
        String refreshToken = request.getRefreshToken();

        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new BusinessException(ErrorCode.TOKEN_INVALID);
        }

        if (!jwtTokenProvider.isRefreshToken(refreshToken)) {
            throw new BusinessException(ErrorCode.TOKEN_INVALID, "不是有效的刷新令牌");
        }

        Long userId = jwtTokenProvider.getUserIdFromToken(refreshToken);
        if (userId == null) {
            throw new BusinessException(ErrorCode.TOKEN_INVALID);
        }

        if (!tokenService.isRefreshTokenValid(userId, refreshToken)) {
            throw new BusinessException(ErrorCode.REFRESH_TOKEN_EXPIRED);
        }

        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        if (user.getStatus() != 0) {
            throw new BusinessException(ErrorCode.ACCOUNT_DISABLED);
        }

        List<String> roleCodes = userMapper.selectRoleCodesByUserId(user.getId());
        List<String> permissions = userMapper.selectPermissionCodesByUserId(user.getId());

        String newAccessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roleCodes, permissions);
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), user.getUsername());

        tokenService.storeAccessToken(user.getId(), newAccessToken, jwtProperties.getAccessTokenExpire());
        tokenService.storeRefreshToken(user.getId(), newRefreshToken, jwtProperties.getRefreshTokenExpire());

        log.info("Token refreshed for user: {}", user.getUsername());

        UserInfoResponse userInfo = buildUserInfoResponse(user, roleCodes, permissions);

        return LoginResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtProperties.getAccessTokenExpire())
                .userInfo(userInfo)
                .build();
    }

    @Override
    public UserInfoResponse getCurrentUser() {
        LoginUser loginUser = getLoginUser();
        if (loginUser == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }

        User user = userMapper.selectById(loginUser.getUserId());
        if (user == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        List<String> roleCodes = loginUser.getRoleCodes();
        List<String> permissions = loginUser.getPermissions();

        return buildUserInfoResponse(user, roleCodes, permissions);
    }

    @Override
    public LoginUser getLoginUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof LoginUser) {
            return (LoginUser) authentication.getPrincipal();
        }
        return null;
    }

    @Override
    public Long getCurrentUserId() {
        LoginUser loginUser = getLoginUser();
        return loginUser != null ? loginUser.getUserId() : null;
    }

    @Override
    public String getCurrentUsername() {
        LoginUser loginUser = getLoginUser();
        return loginUser != null ? loginUser.getUsername() : null;
    }

    private void updateLoginInfo(User user) {
        user.setLastLoginTime(LocalDateTime.now());
        userMapper.updateById(user);
    }

    private UserInfoResponse buildUserInfoResponse(User user, List<String> roleCodes, List<String> permissions) {
        List<Role> roles = userMapper.selectRolesByUserId(user.getId());
        List<UserInfoResponse.RoleInfo> roleInfos = roles.stream()
                .map(role -> UserInfoResponse.RoleInfo.builder()
                        .id(role.getId())
                        .roleCode(role.getRoleCode())
                        .roleName(role.getRoleName())
                        .build())
                .collect(Collectors.toList());

        return UserInfoResponse.builder()
                .id(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .phone(user.getPhone())
                .realName(user.getRealName())
                .avatar(user.getAvatar())
                .gender(user.getGender())
                .status(user.getStatus())
                .roles(roleInfos)
                .permissions(permissions)
                .lastLoginTime(user.getLastLoginTime())
                .createdAt(user.getCreatedAt())
                .build();
    }
}
