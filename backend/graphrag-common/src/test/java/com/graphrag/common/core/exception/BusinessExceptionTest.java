package com.graphrag.common.core.exception;

import com.graphrag.common.core.domain.ErrorCode;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class BusinessExceptionTest {

    @Test
    @DisplayName("测试业务异常-消息")
    void testBusinessExceptionWithMessage() {
        BusinessException exception = new BusinessException("测试异常");
        
        assertEquals(500, exception.getCode());
        assertEquals("测试异常", exception.getMessage());
    }

    @Test
    @DisplayName("测试业务异常-错误码和消息")
    void testBusinessExceptionWithCodeAndMessage() {
        BusinessException exception = new BusinessException(1001, "自定义错误");
        
        assertEquals(1001, exception.getCode());
        assertEquals("自定义错误", exception.getMessage());
    }

    @Test
    @DisplayName("测试业务异常-错误码枚举")
    void testBusinessExceptionWithErrorCode() {
        BusinessException exception = new BusinessException(ErrorCode.USER_NOT_FOUND);
        
        assertEquals(ErrorCode.USER_NOT_FOUND.getCode(), exception.getCode());
        assertEquals(ErrorCode.USER_NOT_FOUND.getMessage(), exception.getMessage());
    }

    @Test
    @DisplayName("测试静态工厂方法")
    void testStaticFactoryMethods() {
        BusinessException ex1 = BusinessException.of("消息");
        assertEquals(500, ex1.getCode());

        BusinessException ex2 = BusinessException.of(400, "错误");
        assertEquals(400, ex2.getCode());

        BusinessException ex3 = BusinessException.of(ErrorCode.BAD_REQUEST);
        assertEquals(ErrorCode.BAD_REQUEST.getCode(), ex3.getCode());
    }
}
