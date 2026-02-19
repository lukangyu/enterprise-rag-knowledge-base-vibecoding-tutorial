package com.graphrag.gateway.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class BusinessException extends RuntimeException {
    private final int code;
    private final HttpStatus httpStatus;
    
    public BusinessException(String message) {
        super(message);
        this.code = 400;
        this.httpStatus = HttpStatus.BAD_REQUEST;
    }
    
    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
        this.httpStatus = mapCodeToStatus(code);
    }
    
    public BusinessException(int code, String message, HttpStatus httpStatus) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
    }
    
    public BusinessException(int code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
        this.httpStatus = mapCodeToStatus(code);
    }
    
    private static HttpStatus mapCodeToStatus(int code) {
        return switch (code / 100) {
            case 4 -> HttpStatus.BAD_REQUEST;
            case 5 -> HttpStatus.INTERNAL_SERVER_ERROR;
            default -> HttpStatus.OK;
        };
    }
    
    public static BusinessException notFound(String resource) {
        return new BusinessException(404, resource + " 不存在", HttpStatus.NOT_FOUND);
    }
    
    public static BusinessException unauthorized(String message) {
        return new BusinessException(401, message, HttpStatus.UNAUTHORIZED);
    }
    
    public static BusinessException forbidden(String message) {
        return new BusinessException(403, message, HttpStatus.FORBIDDEN);
    }
    
    public static BusinessException badRequest(String message) {
        return new BusinessException(400, message, HttpStatus.BAD_REQUEST);
    }
    
    public static BusinessException conflict(String message) {
        return new BusinessException(409, message, HttpStatus.CONFLICT);
    }
}
