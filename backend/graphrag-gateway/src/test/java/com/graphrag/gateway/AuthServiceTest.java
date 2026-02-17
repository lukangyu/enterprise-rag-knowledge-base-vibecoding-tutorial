package com.graphrag.gateway;

import com.graphrag.common.security.dto.LoginRequest;
import com.graphrag.common.security.dto.LoginResponse;
import com.graphrag.common.security.entity.User;
import com.graphrag.common.security.jwt.JwtProperties;
import com.graphrag.common.security.jwt.JwtTokenProvider;
import com.graphrag.gateway.mapper.UserMapper;
import com.graphrag.gateway.service.AuthService;
import com.graphrag.gateway.service.TokenService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserMapper userMapper;

    @Mock
    private JwtTokenProvider jwtTokenProvider;

    @Mock
    private JwtProperties jwtProperties;

    @Mock
    private TokenService tokenService;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private com.graphrag.gateway.service.AuthServiceImpl authService;

    private User testUser;
    private LoginRequest loginRequest;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setUsername("testuser");
        testUser.setPassword("encodedPassword");
        testUser.setEmail("test@example.com");
        testUser.setStatus(0);

        loginRequest = new LoginRequest();
        loginRequest.setUsername("testuser");
        loginRequest.setPassword("password123");

        ReflectionTestUtils.setField(jwtProperties, "accessTokenExpire", 7200000L);
        ReflectionTestUtils.setField(jwtProperties, "refreshTokenExpire", 604800000L);
    }

    @Test
    @DisplayName("登录成功测试")
    void loginSuccess() {
        when(userMapper.selectByUsername("testuser")).thenReturn(testUser);
        when(passwordEncoder.matches("password123", "encodedPassword")).thenReturn(true);
        when(userMapper.selectRoleCodesByUserId(1L)).thenReturn(Arrays.asList("user"));
        when(userMapper.selectPermissionCodesByUserId(1L)).thenReturn(Arrays.asList("document:list"));
        when(jwtTokenProvider.generateAccessToken(anyLong(), anyString(), anyList(), anyList())).thenReturn("accessToken");
        when(jwtTokenProvider.generateRefreshToken(anyLong(), anyString())).thenReturn("refreshToken");

        LoginResponse response = authService.login(loginRequest);

        assertNotNull(response);
        assertEquals("accessToken", response.getAccessToken());
        assertEquals("refreshToken", response.getRefreshToken());
        assertEquals("Bearer", response.getTokenType());

        verify(tokenService).storeAccessToken(1L, "accessToken", 7200000L);
        verify(tokenService).storeRefreshToken(1L, "refreshToken", 604800000L);
    }

    @Test
    @DisplayName("用户不存在登录失败测试")
    void loginFailUserNotFound() {
        when(userMapper.selectByUsername("testuser")).thenReturn(null);

        assertThrows(com.graphrag.common.core.exception.BusinessException.class, () -> {
            authService.login(loginRequest);
        });
    }

    @Test
    @DisplayName("密码错误登录失败测试")
    void loginFailWrongPassword() {
        when(userMapper.selectByUsername("testuser")).thenReturn(testUser);
        when(passwordEncoder.matches("password123", "encodedPassword")).thenReturn(false);

        assertThrows(com.graphrag.common.core.exception.BusinessException.class, () -> {
            authService.login(loginRequest);
        });
    }

    @Test
    @DisplayName("账号禁用登录失败测试")
    void loginFailAccountDisabled() {
        testUser.setStatus(1);
        when(userMapper.selectByUsername("testuser")).thenReturn(testUser);
        when(passwordEncoder.matches("password123", "encodedPassword")).thenReturn(true);

        assertThrows(com.graphrag.common.core.exception.BusinessException.class, () -> {
            authService.login(loginRequest);
        });
    }
}
