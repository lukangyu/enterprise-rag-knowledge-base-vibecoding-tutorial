package com.graphrag.document.service;

import com.graphrag.common.core.domain.PageResult;
import com.graphrag.document.dto.DocumentDTO;
import com.graphrag.document.dto.DocumentQueryRequest;
import com.graphrag.document.dto.DocumentUploadRequest;
import com.graphrag.document.dto.DocumentUploadResponse;
import com.graphrag.document.dto.ProgressResponse;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

public interface DocumentService {

    DocumentUploadResponse uploadDocument(MultipartFile file, DocumentUploadRequest request);

    DocumentDTO getDocumentById(String id);

    DocumentDTO updateMetadata(String id, Map<String, Object> metadata);

    void deleteDocument(String id);

    PageResult<DocumentDTO> listDocuments(DocumentQueryRequest request);

    ProgressResponse getProgress(String id);
}
