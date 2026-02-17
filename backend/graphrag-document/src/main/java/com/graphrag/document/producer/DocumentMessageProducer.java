package com.graphrag.document.producer;

import com.graphrag.common.mq.kafka.KafkaTopicConstants;
import com.graphrag.document.message.DocumentProcessMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
@Slf4j
public class DocumentMessageProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public DocumentMessageProducer(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public CompletableFuture<Void> sendProcessMessage(DocumentProcessMessage message) {
        log.info("Sending document process message: messageId={}, docId={}, action={}",
                message.getMessageId(), message.getDocId(), message.getAction());

        CompletableFuture<Void> result = new CompletableFuture<>();

        kafkaTemplate.send(KafkaTopicConstants.DOCUMENT_PROCESS, message.getDocId(), message)
                .whenComplete((sendResult, ex) -> {
                    if (ex != null) {
                        log.error("Failed to send document process message: messageId={}, docId={}, error={}",
                                message.getMessageId(), message.getDocId(), ex.getMessage(), ex);
                        result.completeExceptionally(ex);
                    } else {
                        log.info("Successfully sent document process message: messageId={}, docId={}, partition={}, offset={}",
                                message.getMessageId(), message.getDocId(),
                                sendResult.getRecordMetadata().partition(),
                                sendResult.getRecordMetadata().offset());
                        result.complete(null);
                    }
                });

        return result;
    }

    public CompletableFuture<Void> sendParseMessage(String docId) {
        DocumentProcessMessage message = DocumentProcessMessage.createParseMessage(docId);
        return sendProcessMessage(message);
    }

    public CompletableFuture<Void> sendFullProcessMessage(String docId) {
        DocumentProcessMessage message = DocumentProcessMessage.createFullProcessMessage(docId);
        return sendProcessMessage(message);
    }
}
