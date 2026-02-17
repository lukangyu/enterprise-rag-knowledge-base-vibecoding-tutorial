package com.graphrag.common.core.constant;

public class SecurityConstants {

    private SecurityConstants() {
    }

    public static final String TOKEN_PREFIX = "Bearer ";
    public static final String HEADER_AUTHORIZATION = "Authorization";
    public static final String HEADER_API_KEY = "X-API-Key";
    public static final String USER_ID_HEADER = "X-User-Id";
    public static final String USER_NAME_HEADER = "X-User-Name";

    public static final String CLAIM_USER_ID = "userId";
    public static final String CLAIM_USERNAME = "username";
    public static final String CLAIM_ROLES = "roles";
    public static final String CLAIM_PERMISSIONS = "permissions";

    public static final String REDIS_TOKEN_PREFIX = "graphrag:token:";
    public static final String REDIS_USER_PREFIX = "graphrag:user:";
    public static final String REDIS_PERMISSION_PREFIX = "graphrag:permission:";

    public static final long ACCESS_TOKEN_EXPIRE_TIME = 2 * 60 * 60 * 1000L;
    public static final long REFRESH_TOKEN_EXPIRE_TIME = 7 * 24 * 60 * 60 * 1000L;
}
