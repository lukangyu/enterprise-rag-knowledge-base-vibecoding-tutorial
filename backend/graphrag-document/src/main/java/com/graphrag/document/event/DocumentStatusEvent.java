package com.graphrag.document.event;

import com.graphrag.document.enums.DocumentStatus;
import org.springframework.context.ApplicationEvent;

import java.time.LocalDateTime;

public class DocumentStatusEvent extends ApplicationEvent {

    private String docId;
    private DocumentStatus fromStatus;
    private DocumentStatus toStatus;
    private LocalDateTime eventTime;
    private String reason;

    public DocumentStatusEvent(Object source, String docId, DocumentStatus fromStatus,
                               DocumentStatus toStatus, LocalDateTime eventTime, String reason) {
        super(source);
        this.docId = docId;
        this.fromStatus = fromStatus;
        this.toStatus = toStatus;
        this.eventTime = eventTime;
        this.reason = reason;
    }

    public String getDocId() {
        return docId;
    }

    public void setDocId(String docId) {
        this.docId = docId;
    }

    public DocumentStatus getFromStatus() {
        return fromStatus;
    }

    public void setFromStatus(DocumentStatus fromStatus) {
        this.fromStatus = fromStatus;
    }

    public DocumentStatus getToStatus() {
        return toStatus;
    }

    public void setToStatus(DocumentStatus toStatus) {
        this.toStatus = toStatus;
    }

    public LocalDateTime getEventTime() {
        return eventTime;
    }

    public void setEventTime(LocalDateTime eventTime) {
        this.eventTime = eventTime;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
