package com.graphrag.common.core.constant;

public class CacheConstants {

    private CacheConstants() {
    }

    public static final String CACHE_DOCUMENT = "graphrag:document:";
    public static final String CACHE_USER = "graphrag:user:";
    public static final String CACHE_PERMISSION = "graphrag:permission:";
    public static final String CACHE_EMBEDDING = "graphrag:embedding:";
    public static final String CACHE_SEARCH = "graphrag:search:";

    public static final long CACHE_TTL_SHORT = 5 * 60;
    public static final long CACHE_TTL_MEDIUM = 30 * 60;
    public static final long CACHE_TTL_LONG = 2 * 60 * 60;
    public static final long CACHE_TTL_DAY = 24 * 60 * 60;
}
