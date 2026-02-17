package com.graphrag.gateway.security;

import com.graphrag.common.security.jwt.JwtTokenProvider;
import com.graphrag.gateway.service.TokenService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;
    private final TokenService tokenService;

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {
        try {
            String token = resolveToken(request);
            if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
                Long userId = jwtTokenProvider.getUserIdFromToken(token);
                String username = jwtTokenProvider.getUsernameFromToken(token);
                List<String> roles = jwtTokenProvider.getRolesFromToken(token);
                List<String> permissions = jwtTokenProvider.getPermissionsFromToken(token);

                if (userId != null && username != null) {
                    if (tokenService.isAccessTokenValid(userId, token)) {
                        List<SimpleGrantedAuthority> authorities = buildAuthorities(roles, permissions);
                        
                        LoginUser loginUser = new LoginUser();
                        loginUser.setUserId(userId);
                        loginUser.setUsername(username);
                        loginUser.setAuthorities(authorities);

                        Authentication authentication = new UsernamePasswordAuthenticationToken(
                                loginUser, null, authorities
                        );
                        SecurityContextHolder.getContext().setAuthentication(authentication);
                        log.debug("Set authentication for user: {}", username);
                    } else {
                        log.warn("Token has been revoked for user: {}", userId);
                    }
                }
            }
        } catch (Exception e) {
            log.error("Cannot set user authentication: {}", e.getMessage());
            SecurityContextHolder.clearContext();
        }

        filterChain.doFilter(request, response);
    }

    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    private List<SimpleGrantedAuthority> buildAuthorities(List<String> roles, List<String> permissions) {
        List<SimpleGrantedAuthority> authorities = roles.stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                .collect(Collectors.toList());
        
        authorities.addAll(permissions.stream()
                .map(SimpleGrantedAuthority::new)
                .collect(Collectors.toList()));
        
        return authorities;
    }
}
