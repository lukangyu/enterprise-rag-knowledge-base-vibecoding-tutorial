package com.graphrag.document.enums;

import java.util.Arrays;

public enum DocumentStatus {
    PENDING("PENDING", "待处理"),
    PARSING("PARSING", "解析中"),
    CHUNKING("CHUNKING", "分块中"),
    EMBEDDING("EMBEDDING", "向量化中"),
    COMPLETED("COMPLETED", "已完成"),
    FAILED("FAILED", "失败");

    private final String code;
    private final String description;

    DocumentStatus(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }

    public static DocumentStatus getByCode(String code) {
        if (code == null) {
            return null;
        }
        return Arrays.stream(values())
                .filter(status -> status.code.equals(code))
                .findFirst()
                .orElse(null);
    }
}
