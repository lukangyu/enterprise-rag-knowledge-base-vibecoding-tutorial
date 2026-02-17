package com.graphrag.document.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
@Slf4j
public class MessageProcessExceptionHandler {

    @ExceptionHandler(MessageProcessException.class)
    public ResponseEntity<Map<String, Object>> handleMessageProcessException(MessageProcessException e) {
        log.error("Message process exception: docId={}, action={}, error={}",
                e.getDocId(), e.getAction(), e.getMessage(), e);
        
        sendAlertNotification(e);
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("errorCode", e.getErrorCode());
        response.put("errorMessage", e.getMessage());
        response.put("docId", e.getDocId());
        response.put("action", e.getAction());
        response.put("timestamp", LocalDateTime.now());
        
        return ResponseEntity.internalServerError().body(response);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgumentException(IllegalArgumentException e) {
        log.error("Illegal argument exception: {}", e.getMessage(), e);
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("errorCode", "INVALID_ARGUMENT");
        response.put("errorMessage", e.getMessage());
        response.put("timestamp", LocalDateTime.now());
        
        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGenericException(Exception e) {
        log.error("Unexpected exception: {}", e.getMessage(), e);
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("errorCode", "INTERNAL_ERROR");
        response.put("errorMessage", "An unexpected error occurred");
        response.put("timestamp", LocalDateTime.now());
        
        return ResponseEntity.internalServerError().body(response);
    }

    private void sendAlertNotification(MessageProcessException e) {
        log.warn("Alert notification: docId={}, action={}, error={}",
                e.getDocId(), e.getAction(), e.getMessage());
    }
}
