package com.graphrag.gateway.exception;

import com.graphrag.common.core.domain.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.NoHandlerFoundException;

import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Result<Void>> handleBusinessException(BusinessException e) {
        log.warn("Business exception: code={}, message={}", e.getCode(), e.getMessage());
        return ResponseEntity
            .status(e.getHttpStatus())
            .body(Result.error(e.getCode(), e.getMessage()));
    }
    
    @ExceptionHandler(ProxyException.class)
    public ResponseEntity<Result<Void>> handleProxyException(ProxyException e) {
        log.error("Proxy exception: {}", e.getMessage(), e);
        return ResponseEntity
            .status(HttpStatus.BAD_GATEWAY)
            .body(Result.error(502, "服务代理错误: " + e.getMessage()));
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Result<Void>> handleValidationException(MethodArgumentNotValidException e) {
        String errors = e.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));
        log.warn("Validation failed: {}", errors);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(Result.error(400, "参数验证失败: " + errors));
    }
    
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Result<Void>> handleMissingParameter(MissingServletRequestParameterException e) {
        log.warn("Missing required parameter: {}", e.getParameterName());
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(Result.error(400, "缺少必需参数: " + e.getParameterName()));
    }
    
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<Result<Void>> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        log.warn("Parameter type mismatch: {} - {}", e.getName(), e.getMessage());
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(Result.error(400, "参数类型错误: " + e.getName()));
    }
    
    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<Result<Void>> handleNotFound(NoHandlerFoundException e) {
        log.warn("No handler found: {} {}", e.getHttpMethod(), e.getRequestURL());
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(Result.error(404, "请求的资源不存在: " + e.getRequestURL()));
    }
    
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Result<Void>> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("Illegal argument: {}", e.getMessage());
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(Result.error(400, e.getMessage()));
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Result<Void>> handleGenericException(Exception e) {
        log.error("Unexpected error occurred", e);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Result.error(500, "服务器内部错误，请稍后重试"));
    }
}
