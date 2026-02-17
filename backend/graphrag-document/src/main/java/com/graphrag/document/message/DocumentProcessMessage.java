package com.graphrag.document.message;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentProcessMessage implements Serializable {

    private static final long serialVersionUID = 1L;

    private String messageId;

    private String docId;

    private String action;

    private String priority;

    private LocalDateTime timestamp;

    @Builder.Default
    private Map<String, Object> payload = new HashMap<>();

    public static class Action {
        public static final String PARSE = "PARSE";
        public static final String CHUNK = "CHUNK";
        public static final String EMBED = "EMBED";
        public static final String FULL_PROCESS = "FULL_PROCESS";

        private Action() {
        }
    }

    public static class Priority {
        public static final String HIGH = "HIGH";
        public static final String NORMAL = "NORMAL";
        public static final String LOW = "LOW";

        private Priority() {
        }
    }

    public static DocumentProcessMessage createParseMessage(String docId) {
        return DocumentProcessMessage.builder()
                .messageId(UUID.randomUUID().toString())
                .docId(docId)
                .action(Action.PARSE)
                .priority(Priority.NORMAL)
                .timestamp(LocalDateTime.now())
                .build();
    }

    public static DocumentProcessMessage createFullProcessMessage(String docId) {
        return DocumentProcessMessage.builder()
                .messageId(UUID.randomUUID().toString())
                .docId(docId)
                .action(Action.FULL_PROCESS)
                .priority(Priority.NORMAL)
                .timestamp(LocalDateTime.now())
                .build();
    }
}
