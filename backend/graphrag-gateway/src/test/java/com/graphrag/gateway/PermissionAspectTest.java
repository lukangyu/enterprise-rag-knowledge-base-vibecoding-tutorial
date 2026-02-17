package com.graphrag.gateway;

import com.graphrag.common.security.annotation.RequirePermission;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.gateway.security.LoginUser;
import com.graphrag.gateway.security.PermissionAspect;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.context.SecurityContextImpl;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PermissionAspectTest {

    @Mock
    private ProceedingJoinPoint joinPoint;

    @Mock
    private MethodSignature methodSignature;

    @InjectMocks
    private PermissionAspect permissionAspect;

    private LoginUser loginUser;

    @BeforeEach
    void setUp() {
        loginUser = new LoginUser();
        loginUser.setUserId(1L);
        loginUser.setUsername("testuser");

        List<SimpleGrantedAuthority> authorities = Arrays.asList(
                new SimpleGrantedAuthority("ROLE_user"),
                new SimpleGrantedAuthority("document:list"),
                new SimpleGrantedAuthority("document:upload")
        );
        loginUser.setAuthorities(authorities);
    }

    @Test
    @DisplayName("权限校验通过测试 - AND逻辑")
    void checkPermissionAndLogicSuccess() throws Throwable {
        SecurityContext context = new SecurityContextImpl();
        context.setAuthentication(new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities()));
        SecurityContextHolder.setContext(context);

        RequirePermission annotation = mockAnnotation(new String[]{"document:list", "document:upload"}, RequirePermission.Logical.AND);
        Method mockMethod = TestClass.class.getMethod("testMethod");
        when(joinPoint.getSignature()).thenReturn(methodSignature);
        when(methodSignature.getMethod()).thenReturn(mockMethod);
        when(joinPoint.proceed()).thenReturn("success");

        Object result = permissionAspect.checkPermission(joinPoint);

        assertEquals("success", result);
        verify(joinPoint).proceed();
    }

    @Test
    @DisplayName("权限校验失败测试 - AND逻辑")
    void checkPermissionAndLogicFail() throws Throwable {
        SecurityContext context = new SecurityContextImpl();
        context.setAuthentication(new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities()));
        SecurityContextHolder.setContext(context);

        RequirePermission annotation = mockAnnotation(new String[]{"document:list", "system:user:delete"}, RequirePermission.Logical.AND);
        Method mockMethod = TestClass.class.getMethod("testMethod");
        when(joinPoint.getSignature()).thenReturn(methodSignature);
        when(methodSignature.getMethod()).thenReturn(mockMethod);

        assertThrows(BusinessException.class, () -> {
            permissionAspect.checkPermission(joinPoint);
        });
    }

    @Test
    @DisplayName("权限校验通过测试 - OR逻辑")
    void checkPermissionOrLogicSuccess() throws Throwable {
        SecurityContext context = new SecurityContextImpl();
        context.setAuthentication(new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities()));
        SecurityContextHolder.setContext(context);

        RequirePermission annotation = mockAnnotation(new String[]{"document:list", "system:user:delete"}, RequirePermission.Logical.OR);
        Method mockMethod = TestClass.class.getMethod("testMethod");
        when(joinPoint.getSignature()).thenReturn(methodSignature);
        when(methodSignature.getMethod()).thenReturn(mockMethod);
        when(joinPoint.proceed()).thenReturn("success");

        Object result = permissionAspect.checkPermission(joinPoint);

        assertEquals("success", result);
        verify(joinPoint).proceed();
    }

    @Test
    @DisplayName("未登录权限校验测试")
    void checkPermissionWithoutLogin() throws Throwable {
        SecurityContextHolder.clearContext();

        Method mockMethod = TestClass.class.getMethod("testMethod");
        when(joinPoint.getSignature()).thenReturn(methodSignature);
        when(methodSignature.getMethod()).thenReturn(mockMethod);

        assertThrows(BusinessException.class, () -> {
            permissionAspect.checkPermission(joinPoint);
        });
    }

    private RequirePermission mockAnnotation(String[] value, RequirePermission.Logical logical) {
        return new RequirePermission() {
            @Override
            public String[] value() {
                return value;
            }

            @Override
            public Logical logical() {
                return logical;
            }

            @Override
            public Class<? extends java.lang.annotation.Annotation> annotationType() {
                return RequirePermission.class;
            }
        };
    }

    static class TestClass {
        public void testMethod() {
        }
    }
}
