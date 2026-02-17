package com.graphrag.gateway.security;

import com.graphrag.common.security.annotation.RequirePermission;
import com.graphrag.common.security.annotation.RequireRole;
import com.graphrag.common.core.domain.ErrorCode;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.gateway.security.LoginUser;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@Aspect
@Component
public class PermissionAspect {

    @Around("@annotation(com.graphrag.common.security.annotation.RequirePermission)")
    public Object checkPermission(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        Method method = signature.getMethod();
        RequirePermission annotation = method.getAnnotation(RequirePermission.class);

        if (annotation == null) {
            return joinPoint.proceed();
        }

        LoginUser loginUser = getLoginUser();
        if (loginUser == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }

        String[] requiredPermissions = annotation.value();
        if (requiredPermissions.length == 0) {
            return joinPoint.proceed();
        }

        Set<String> userPermissions = loginUser.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toSet());

        boolean hasPermission;
        if (annotation.logical() == RequirePermission.Logical.AND) {
            hasPermission = Arrays.stream(requiredPermissions)
                    .allMatch(userPermissions::contains);
        } else {
            hasPermission = Arrays.stream(requiredPermissions)
                    .anyMatch(userPermissions::contains);
        }

        if (!hasPermission) {
            log.warn("User {} lacks required permissions: {}", loginUser.getUsername(), Arrays.toString(requiredPermissions));
            throw new BusinessException(ErrorCode.FORBIDDEN);
        }

        return joinPoint.proceed();
    }

    @Around("@annotation(com.graphrag.common.security.annotation.RequireRole)")
    public Object checkRole(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        Method method = signature.getMethod();
        RequireRole annotation = method.getAnnotation(RequireRole.class);

        if (annotation == null) {
            return joinPoint.proceed();
        }

        LoginUser loginUser = getLoginUser();
        if (loginUser == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }

        String[] requiredRoles = annotation.value();
        if (requiredRoles.length == 0) {
            return joinPoint.proceed();
        }

        Set<String> userRoles = loginUser.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .filter(auth -> auth.startsWith("ROLE_"))
                .map(auth -> auth.substring(5))
                .collect(Collectors.toSet());

        boolean hasRole;
        if (annotation.logical() == RequirePermission.Logical.AND) {
            hasRole = Arrays.stream(requiredRoles)
                    .allMatch(userRoles::contains);
        } else {
            hasRole = Arrays.stream(requiredRoles)
                    .anyMatch(userRoles::contains);
        }

        if (!hasRole) {
            log.warn("User {} lacks required roles: {}", loginUser.getUsername(), Arrays.toString(requiredRoles));
            throw new BusinessException(ErrorCode.FORBIDDEN);
        }

        return joinPoint.proceed();
    }

    private LoginUser getLoginUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof LoginUser) {
            return (LoginUser) authentication.getPrincipal();
        }
        return null;
    }
}
