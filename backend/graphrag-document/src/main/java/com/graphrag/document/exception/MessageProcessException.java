package com.graphrag.document.exception;

public class MessageProcessException extends RuntimeException {

    private final String errorCode;
    private final String docId;
    private final String action;

    public MessageProcessException(String message) {
        super(message);
        this.errorCode = "MESSAGE_PROCESS_ERROR";
        this.docId = null;
        this.action = null;
    }

    public MessageProcessException(String message, String docId, String action) {
        super(message);
        this.errorCode = "MESSAGE_PROCESS_ERROR";
        this.docId = docId;
        this.action = action;
    }

    public MessageProcessException(String message, String errorCode, String docId, String action) {
        super(message);
        this.errorCode = errorCode;
        this.docId = docId;
        this.action = action;
    }

    public MessageProcessException(String message, Throwable cause) {
        super(message, cause);
        this.errorCode = "MESSAGE_PROCESS_ERROR";
        this.docId = null;
        this.action = null;
    }

    public MessageProcessException(String message, Throwable cause, String docId, String action) {
        super(message, cause);
        this.errorCode = "MESSAGE_PROCESS_ERROR";
        this.docId = docId;
        this.action = action;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public String getDocId() {
        return docId;
    }

    public String getAction() {
        return action;
    }
}
