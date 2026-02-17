package com.graphrag.gateway.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class TokenService {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final String TOKEN_PREFIX = "graphrag:token:";
    private static final String REFRESH_TOKEN_PREFIX = "graphrag:refresh_token:";
    private static final String USER_TOKEN_PREFIX = "graphrag:user_token:";

    public void storeAccessToken(Long userId, String token, long expiration) {
        String key = TOKEN_PREFIX + userId;
        redisTemplate.opsForValue().set(key, token, expiration, TimeUnit.MILLISECONDS);
        log.debug("Stored access token for user: {}", userId);
    }

    public void storeRefreshToken(Long userId, String token, long expiration) {
        String key = REFRESH_TOKEN_PREFIX + userId;
        redisTemplate.opsForValue().set(key, token, expiration, TimeUnit.MILLISECONDS);
        log.debug("Stored refresh token for user: {}", userId);
    }

    public String getAccessToken(Long userId) {
        String key = TOKEN_PREFIX + userId;
        Object token = redisTemplate.opsForValue().get(key);
        return token != null ? token.toString() : null;
    }

    public String getRefreshToken(Long userId) {
        String key = REFRESH_TOKEN_PREFIX + userId;
        Object token = redisTemplate.opsForValue().get(key);
        return token != null ? token.toString() : null;
    }

    public void removeToken(Long userId) {
        String accessTokenKey = TOKEN_PREFIX + userId;
        String refreshTokenKey = REFRESH_TOKEN_PREFIX + userId;
        redisTemplate.delete(accessTokenKey);
        redisTemplate.delete(refreshTokenKey);
        log.debug("Removed tokens for user: {}", userId);
    }

    public boolean isAccessTokenValid(Long userId, String token) {
        String storedToken = getAccessToken(userId);
        return storedToken != null && storedToken.equals(token);
    }

    public boolean isRefreshTokenValid(Long userId, String token) {
        String storedToken = getRefreshToken(userId);
        return storedToken != null && storedToken.equals(token);
    }

    public void storeUserTokenMapping(String token, Long userId, long expiration) {
        String key = USER_TOKEN_PREFIX + token;
        redisTemplate.opsForValue().set(key, userId, expiration, TimeUnit.MILLISECONDS);
    }

    public Long getUserIdByToken(String token) {
        String key = USER_TOKEN_PREFIX + token;
        Object userId = redisTemplate.opsForValue().get(key);
        if (userId instanceof Integer) {
            return ((Integer) userId).longValue();
        } else if (userId instanceof Long) {
            return (Long) userId;
        }
        return null;
    }

    public void removeTokenMapping(String token) {
        String key = USER_TOKEN_PREFIX + token;
        redisTemplate.delete(key);
    }
}
