package com.graphrag.document.consumer;

import com.graphrag.common.mq.kafka.KafkaTopicConstants;
import com.graphrag.document.message.DocumentProcessMessage;
import com.graphrag.document.service.DocumentProcessService;
import com.graphrag.document.service.DocumentRetryService;
import com.graphrag.document.service.TaskStatusManager;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class DocumentMessageConsumer {

    private final DocumentProcessService documentProcessService;
    private final TaskStatusManager taskStatusManager;
    private final DocumentRetryService documentRetryService;

    public DocumentMessageConsumer(
            DocumentProcessService documentProcessService,
            TaskStatusManager taskStatusManager,
            DocumentRetryService documentRetryService) {
        this.documentProcessService = documentProcessService;
        this.taskStatusManager = taskStatusManager;
        this.documentRetryService = documentRetryService;
    }

    @KafkaListener(
            topics = KafkaTopicConstants.DOCUMENT_PROCESS,
            groupId = "graphrag-document-processor",
            containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeDocumentProcessMessage(
            @Payload DocumentProcessMessage message,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        
        log.info("Received document process message: messageId={}, docId={}, action={}, topic={}, partition={}, offset={}",
                message.getMessageId(), message.getDocId(), message.getAction(), topic, partition, offset);
        
        try {
            if (!taskStatusManager.acquireLock(message.getDocId(), 300)) {
                log.warn("Failed to acquire lock for docId: {}, message will be reprocessed", message.getDocId());
                return;
            }
            
            processMessage(message);
            
            taskStatusManager.releaseLock(message.getDocId());
            acknowledgment.acknowledge();
            
            log.info("Document process message completed: messageId={}, docId={}", 
                    message.getMessageId(), message.getDocId());
        } catch (Exception e) {
            log.error("Error processing document message: messageId={}, docId={}, error={}",
                    message.getMessageId(), message.getDocId(), e.getMessage(), e);
            
            taskStatusManager.releaseLock(message.getDocId());
            
            if (documentRetryService.shouldRetry(message.getDocId())) {
                documentRetryService.scheduleRetry(message.getDocId(), message.getAction());
                acknowledgment.acknowledge();
                log.info("Message scheduled for retry: messageId={}, docId={}",
                        message.getMessageId(), message.getDocId());
            } else {
                log.error("Max retries exceeded for message: messageId={}, docId={}",
                        message.getMessageId(), message.getDocId());
                taskStatusManager.markFailed(message.getDocId(), "Max retries exceeded: " + e.getMessage());
                acknowledgment.acknowledge();
            }
        }
    }

    private void processMessage(DocumentProcessMessage message) {
        String action = message.getAction();
        String docId = message.getDocId();
        
        log.info("Processing message action: {}, docId: {}", action, docId);
        
        switch (action) {
            case DocumentProcessMessage.Action.FULL_PROCESS -> {
                documentProcessService.processDocument(docId);
            }
            case DocumentProcessMessage.Action.PARSE -> {
                documentProcessService.parseDocument(docId);
            }
            case DocumentProcessMessage.Action.CHUNK -> {
                documentProcessService.chunkDocument(docId);
            }
            case DocumentProcessMessage.Action.EMBED -> {
                documentProcessService.embedDocument(docId);
            }
            default -> {
                log.warn("Unknown action type: {} for docId: {}", action, docId);
                throw new IllegalArgumentException("Unknown action type: " + action);
            }
        }
    }
}
