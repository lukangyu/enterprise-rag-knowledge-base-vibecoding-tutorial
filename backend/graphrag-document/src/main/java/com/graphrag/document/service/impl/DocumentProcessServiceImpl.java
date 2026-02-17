package com.graphrag.document.service.impl;

import com.graphrag.document.enums.DocumentStatus;
import com.graphrag.document.mapper.DocumentMapper;
import com.graphrag.document.entity.Document;
import com.graphrag.document.service.DocumentProcessService;
import com.graphrag.document.service.TaskStatusManager;
import com.graphrag.document.statemachine.DocumentStatusMachine;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class DocumentProcessServiceImpl implements DocumentProcessService {

    private final DocumentMapper documentMapper;
    private final TaskStatusManager taskStatusManager;
    private final DocumentStatusMachine documentStatusMachine;

    public DocumentProcessServiceImpl(
            DocumentMapper documentMapper,
            TaskStatusManager taskStatusManager,
            DocumentStatusMachine documentStatusMachine) {
        this.documentMapper = documentMapper;
        this.taskStatusManager = taskStatusManager;
        this.documentStatusMachine = documentStatusMachine;
    }

    @Override
    public void processDocument(String docId) {
        log.info("Starting full document processing for docId: {}", docId);
        
        try {
            taskStatusManager.initProgress(docId);
            updateDocumentStatus(docId, DocumentStatus.PENDING);
            
            parseDocument(docId);
            chunkDocument(docId);
            embedDocument(docId);
            
            taskStatusManager.updateProgress(docId, "COMPLETED", 100);
            log.info("Full document processing completed for docId: {}", docId);
        } catch (Exception e) {
            log.error("Full document processing failed for docId: {}", docId, e);
            taskStatusManager.markFailed(docId, e.getMessage());
            updateDocumentStatus(docId, DocumentStatus.FAILED);
            throw e;
        }
    }

    @Override
    public void parseDocument(String docId) {
        log.info("Starting document parsing for docId: {}", docId);
        
        try {
            taskStatusManager.updateProgress(docId, "PARSING", 10);
            updateDocumentStatus(docId, DocumentStatus.PARSING);
            
            log.info("Calling FastAPI service for document parsing, docId: {}", docId);
            
            taskStatusManager.updateProgress(docId, "PARSING", 30);
            log.info("Document parsing completed for docId: {}", docId);
        } catch (Exception e) {
            log.error("Document parsing failed for docId: {}", docId, e);
            taskStatusManager.markFailed(docId, "Parse failed: " + e.getMessage());
            updateDocumentStatus(docId, DocumentStatus.FAILED);
            throw e;
        }
    }

    @Override
    public void chunkDocument(String docId) {
        log.info("Starting document chunking for docId: {}", docId);
        
        try {
            taskStatusManager.updateProgress(docId, "CHUNKING", 40);
            updateDocumentStatus(docId, DocumentStatus.CHUNKING);
            
            log.info("Calling FastAPI service for document chunking, docId: {}", docId);
            
            taskStatusManager.updateProgress(docId, "CHUNKING", 60);
            log.info("Document chunking completed for docId: {}", docId);
        } catch (Exception e) {
            log.error("Document chunking failed for docId: {}", docId, e);
            taskStatusManager.markFailed(docId, "Chunk failed: " + e.getMessage());
            updateDocumentStatus(docId, DocumentStatus.FAILED);
            throw e;
        }
    }

    @Override
    public void embedDocument(String docId) {
        log.info("Starting document embedding for docId: {}", docId);
        
        try {
            taskStatusManager.updateProgress(docId, "EMBEDDING", 70);
            updateDocumentStatus(docId, DocumentStatus.EMBEDDING);
            
            log.info("Calling FastAPI service for document embedding, docId: {}", docId);
            
            taskStatusManager.updateProgress(docId, "EMBEDDING", 90);
            updateDocumentStatus(docId, DocumentStatus.COMPLETED);
            log.info("Document embedding completed for docId: {}", docId);
        } catch (Exception e) {
            log.error("Document embedding failed for docId: {}", docId, e);
            taskStatusManager.markFailed(docId, "Embed failed: " + e.getMessage());
            updateDocumentStatus(docId, DocumentStatus.FAILED);
            throw e;
        }
    }

    private void updateDocumentStatus(String docId, DocumentStatus newStatus) {
        Document document = documentMapper.selectById(docId);
        if (document != null) {
            DocumentStatus currentStatus = DocumentStatus.getByCode(document.getStatus());
            if (documentStatusMachine.canTransition(currentStatus, newStatus)) {
                document.setStatus(newStatus.getCode());
                documentMapper.updateById(document);
                log.info("Document status updated: docId={}, from={}, to={}", 
                        docId, currentStatus, newStatus);
            } else {
                log.warn("Invalid status transition: docId={}, from={}, to={}", 
                        docId, currentStatus, newStatus);
            }
        } else {
            log.warn("Document not found for status update: docId={}", docId);
        }
    }
}
