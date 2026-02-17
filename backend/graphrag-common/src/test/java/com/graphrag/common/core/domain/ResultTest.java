package com.graphrag.common.core.domain;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ResultTest {

    @Test
    @DisplayName("测试成功响应")
    void testSuccess() {
        Result<String> result = Result.success("test data");
        
        assertTrue(result.isSuccess());
        assertEquals(200, result.getCode());
        assertEquals("操作成功", result.getMessage());
        assertEquals("test data", result.getData());
        assertNotNull(result.getTimestamp());
    }

    @Test
    @DisplayName("测试成功响应-自定义消息")
    void testSuccessWithMessage() {
        Result<String> result = Result.success("test data", "自定义成功消息");
        
        assertTrue(result.isSuccess());
        assertEquals(200, result.getCode());
        assertEquals("自定义成功消息", result.getMessage());
    }

    @Test
    @DisplayName("测试错误响应")
    void testError() {
        Result<Void> result = Result.error(400, "参数错误");
        
        assertFalse(result.isSuccess());
        assertEquals(400, result.getCode());
        assertEquals("参数错误", result.getMessage());
        assertNull(result.getData());
    }

    @Test
    @DisplayName("测试错误响应-错误码枚举")
    void testErrorWithErrorCode() {
        Result<Void> result = Result.error(ErrorCode.BAD_REQUEST);
        
        assertEquals(ErrorCode.BAD_REQUEST.getCode(), result.getCode());
        assertEquals(ErrorCode.BAD_REQUEST.getMessage(), result.getMessage());
    }
}
