package com.graphrag.gateway;

import com.graphrag.common.security.jwt.JwtProperties;
import com.graphrag.common.security.jwt.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class JwtTokenProviderTest {

    @Mock
    private JwtProperties jwtProperties;

    @InjectMocks
    private JwtTokenProvider jwtTokenProvider;

    private static final String SECRET = "graphrag-jwt-secret-key-for-testing-must-be-at-least-256-bits-long";

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(jwtProperties, "secret", SECRET);
        ReflectionTestUtils.setField(jwtProperties, "issuer", "graphrag");
        ReflectionTestUtils.setField(jwtProperties, "accessTokenExpire", 7200000L);
        ReflectionTestUtils.setField(jwtProperties, "refreshTokenExpire", 604800000L);
    }

    @Test
    @DisplayName("生成访问令牌测试")
    void generateAccessToken() {
        Long userId = 1L;
        String username = "testuser";
        List<String> roles = Arrays.asList("admin", "user");
        List<String> permissions = Arrays.asList("system:user:list", "system:user:add");

        String token = jwtTokenProvider.generateAccessToken(userId, username, roles, permissions);

        assertNotNull(token);
        assertTrue(token.length() > 0);
    }

    @Test
    @DisplayName("生成刷新令牌测试")
    void generateRefreshToken() {
        Long userId = 1L;
        String username = "testuser";

        String token = jwtTokenProvider.generateRefreshToken(userId, username);

        assertNotNull(token);
        assertTrue(token.length() > 0);
    }

    @Test
    @DisplayName("验证有效令牌测试")
    void validateValidToken() {
        String token = jwtTokenProvider.generateAccessToken(1L, "testuser", Arrays.asList("user"), Arrays.asList("document:list"));

        boolean isValid = jwtTokenProvider.validateToken(token);

        assertTrue(isValid);
    }

    @Test
    @DisplayName("验证无效令牌测试")
    void validateInvalidToken() {
        String invalidToken = "invalid.token.here";

        boolean isValid = jwtTokenProvider.validateToken(invalidToken);

        assertFalse(isValid);
    }

    @Test
    @DisplayName("从令牌获取用户ID测试")
    void getUserIdFromToken() {
        Long userId = 1L;
        String token = jwtTokenProvider.generateAccessToken(userId, "testuser", Arrays.asList("user"), Arrays.asList("document:list"));

        Long extractedUserId = jwtTokenProvider.getUserIdFromToken(token);

        assertEquals(userId, extractedUserId);
    }

    @Test
    @DisplayName("从令牌获取用户名测试")
    void getUsernameFromToken() {
        String username = "testuser";
        String token = jwtTokenProvider.generateAccessToken(1L, username, Arrays.asList("user"), Arrays.asList("document:list"));

        String extractedUsername = jwtTokenProvider.getUsernameFromToken(token);

        assertEquals(username, extractedUsername);
    }

    @Test
    @DisplayName("从令牌获取角色测试")
    void getRolesFromToken() {
        List<String> roles = Arrays.asList("admin", "user");
        String token = jwtTokenProvider.generateAccessToken(1L, "testuser", roles, Arrays.asList("document:list"));

        List<String> extractedRoles = jwtTokenProvider.getRolesFromToken(token);

        assertEquals(roles, extractedRoles);
    }

    @Test
    @DisplayName("从令牌获取权限测试")
    void getPermissionsFromToken() {
        List<String> permissions = Arrays.asList("system:user:list", "system:user:add");
        String token = jwtTokenProvider.generateAccessToken(1L, "testuser", Arrays.asList("user"), permissions);

        List<String> extractedPermissions = jwtTokenProvider.getPermissionsFromToken(token);

        assertEquals(permissions, extractedPermissions);
    }

    @Test
    @DisplayName("检查刷新令牌类型测试")
    void isRefreshToken() {
        String accessToken = jwtTokenProvider.generateAccessToken(1L, "testuser", Arrays.asList("user"), Arrays.asList("document:list"));
        String refreshToken = jwtTokenProvider.generateRefreshToken(1L, "testuser");

        assertFalse(jwtTokenProvider.isRefreshToken(accessToken));
        assertTrue(jwtTokenProvider.isRefreshToken(refreshToken));
    }
}
