package com.graphrag.common.core.constant;

public class SystemConstants {

    private SystemConstants() {
    }

    public static final String DEFAULT_PASSWORD = "123456";
    public static final String DEFAULT_AVATAR = "/avatar/default.png";
    public static final String DEFAULT_ROLE = "user";

    public static final Integer STATUS_NORMAL = 0;
    public static final Integer STATUS_DISABLED = 1;
    public static final Integer STATUS_DELETED = 2;

    public static final Integer GENDER_UNKNOWN = 0;
    public static final Integer GENDER_MALE = 1;
    public static final Integer GENDER_FEMALE = 2;

    public static final String SUPER_ADMIN_ROLE = "super_admin";
    public static final String ADMIN_ROLE = "admin";
    public static final String USER_ROLE = "user";

    public static final String TRACE_ID_HEADER = "X-Trace-Id";
    public static final String TRACE_ID_MDC_KEY = "traceId";
}
