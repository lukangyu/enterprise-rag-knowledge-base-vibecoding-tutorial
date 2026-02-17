package com.graphrag.gateway.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserPermissionCacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final String USER_PERMISSION_PREFIX = "graphrag:user_permission:";
    private static final String USER_ROLE_PREFIX = "graphrag:user_role:";
    private static final long CACHE_TTL = 30 * 60;

    public void cacheUserPermissions(Long userId, List<String> permissions) {
        String key = USER_PERMISSION_PREFIX + userId;
        redisTemplate.opsForValue().set(key, permissions, CACHE_TTL, TimeUnit.SECONDS);
        log.debug("Cached permissions for user: {}", userId);
    }

    @SuppressWarnings("unchecked")
    public List<String> getUserPermissions(Long userId) {
        String key = USER_PERMISSION_PREFIX + userId;
        Object cached = redisTemplate.opsForValue().get(key);
        if (cached instanceof List) {
            return (List<String>) cached;
        }
        return null;
    }

    public void cacheUserRoles(Long userId, List<String> roles) {
        String key = USER_ROLE_PREFIX + userId;
        redisTemplate.opsForValue().set(key, roles, CACHE_TTL, TimeUnit.SECONDS);
        log.debug("Cached roles for user: {}", userId);
    }

    @SuppressWarnings("unchecked")
    public List<String> getUserRoles(Long userId) {
        String key = USER_ROLE_PREFIX + userId;
        Object cached = redisTemplate.opsForValue().get(key);
        if (cached instanceof List) {
            return (List<String>) cached;
        }
        return null;
    }

    public void clearUserPermissionCache(Long userId) {
        String permissionKey = USER_PERMISSION_PREFIX + userId;
        String roleKey = USER_ROLE_PREFIX + userId;
        redisTemplate.delete(permissionKey);
        redisTemplate.delete(roleKey);
        log.debug("Cleared permission cache for user: {}", userId);
    }

    public void refreshUserPermissionCache(Long userId, List<String> roles, List<String> permissions) {
        clearUserPermissionCache(userId);
        cacheUserRoles(userId, roles);
        cacheUserPermissions(userId, permissions);
        log.debug("Refreshed permission cache for user: {}", userId);
    }
}
