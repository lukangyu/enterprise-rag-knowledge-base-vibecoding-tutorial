package com.graphrag.common.security.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtTokenProvider {

    private final JwtProperties jwtProperties;

    private SecretKey getSigningKey() {
        byte[] keyBytes = jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public String generateAccessToken(Long userId, String username, List<String> roles, List<String> permissions) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        claims.put("roles", roles);
        claims.put("permissions", permissions);
        return createToken(claims, username, jwtProperties.getAccessTokenExpire());
    }

    public String generateRefreshToken(Long userId, String username) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        claims.put("type", "refresh");
        return createToken(claims, username, jwtProperties.getRefreshTokenExpire());
    }

    private String createToken(Map<String, Object> claims, String subject, Long expiration) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration);

        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .issuer(jwtProperties.getIssuer())
                .issuedAt(now)
                .expiration(expiryDate)
                .signWith(getSigningKey())
                .compact();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token);
            return true;
        } catch (SignatureException ex) {
            log.error("Invalid JWT signature: {}", ex.getMessage());
        } catch (MalformedJwtException ex) {
            log.error("Invalid JWT token: {}", ex.getMessage());
        } catch (ExpiredJwtException ex) {
            log.error("Expired JWT token: {}", ex.getMessage());
        } catch (UnsupportedJwtException ex) {
            log.error("Unsupported JWT token: {}", ex.getMessage());
        } catch (IllegalArgumentException ex) {
            log.error("JWT claims string is empty: {}", ex.getMessage());
        }
        return false;
    }

    public Claims parseToken(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (Exception e) {
            log.error("Failed to parse JWT token: {}", e.getMessage());
            return null;
        }
    }

    public Long getUserIdFromToken(String token) {
        Claims claims = parseToken(token);
        if (claims != null) {
            Object userId = claims.get("userId");
            if (userId instanceof Integer) {
                return ((Integer) userId).longValue();
            } else if (userId instanceof Long) {
                return (Long) userId;
            }
        }
        return null;
    }

    public String getUsernameFromToken(String token) {
        Claims claims = parseToken(token);
        return claims != null ? claims.getSubject() : null;
    }

    @SuppressWarnings("unchecked")
    public List<String> getRolesFromToken(String token) {
        Claims claims = parseToken(token);
        if (claims != null) {
            Object roles = claims.get("roles");
            if (roles instanceof List) {
                return (List<String>) roles;
            }
        }
        return List.of();
    }

    @SuppressWarnings("unchecked")
    public List<String> getPermissionsFromToken(String token) {
        Claims claims = parseToken(token);
        if (claims != null) {
            Object permissions = claims.get("permissions");
            if (permissions instanceof List) {
                return (List<String>) permissions;
            }
        }
        return List.of();
    }

    public boolean isTokenExpired(String token) {
        try {
            Claims claims = parseToken(token);
            if (claims != null) {
                return claims.getExpiration().before(new Date());
            }
        } catch (Exception e) {
            log.error("Failed to check token expiration: {}", e.getMessage());
        }
        return true;
    }

    public long getExpirationTime(String token) {
        Claims claims = parseToken(token);
        if (claims != null) {
            return claims.getExpiration().getTime() - System.currentTimeMillis();
        }
        return 0;
    }

    public boolean isRefreshToken(String token) {
        Claims claims = parseToken(token);
        if (claims != null) {
            Object type = claims.get("type");
            return "refresh".equals(type);
        }
        return false;
    }
}
