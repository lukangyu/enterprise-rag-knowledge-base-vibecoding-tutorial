package com.graphrag.document.statemachine;

import com.graphrag.document.enums.DocumentStatus;
import org.springframework.stereotype.Component;

import java.util.EnumMap;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;

@Component
public class DocumentStatusMachine {

    private final Map<DocumentStatus, Set<DocumentStatus>> transitionRules;

    public DocumentStatusMachine() {
        this.transitionRules = new EnumMap<>(DocumentStatus.class);
        
        transitionRules.put(DocumentStatus.PENDING, EnumSet.of(DocumentStatus.PARSING));
        transitionRules.put(DocumentStatus.PARSING, EnumSet.of(DocumentStatus.CHUNKING, DocumentStatus.FAILED));
        transitionRules.put(DocumentStatus.CHUNKING, EnumSet.of(DocumentStatus.EMBEDDING, DocumentStatus.FAILED));
        transitionRules.put(DocumentStatus.EMBEDDING, EnumSet.of(DocumentStatus.COMPLETED, DocumentStatus.FAILED));
        transitionRules.put(DocumentStatus.FAILED, EnumSet.of(DocumentStatus.PENDING));
        transitionRules.put(DocumentStatus.COMPLETED, EnumSet.noneOf(DocumentStatus.class));
    }

    public boolean canTransition(DocumentStatus from, DocumentStatus to) {
        if (from == null || to == null) {
            return false;
        }
        Set<DocumentStatus> allowedTargets = transitionRules.get(from);
        return allowedTargets != null && allowedTargets.contains(to);
    }

    public DocumentStatus transition(DocumentStatus from, DocumentStatus to) {
        if (!canTransition(from, to)) {
            throw new IllegalStateException(
                    String.format("Invalid status transition from %s to %s", from, to));
        }
        return to;
    }

    public DocumentStatus getNextStatus(DocumentStatus current, boolean success) {
        if (current == null) {
            return null;
        }
        
        if (success) {
            return switch (current) {
                case PENDING -> DocumentStatus.PARSING;
                case PARSING -> DocumentStatus.CHUNKING;
                case CHUNKING -> DocumentStatus.EMBEDDING;
                case EMBEDDING -> DocumentStatus.COMPLETED;
                case COMPLETED, FAILED -> null;
            };
        } else {
            if (current == DocumentStatus.COMPLETED) {
                return null;
            }
            return DocumentStatus.FAILED;
        }
    }
}
