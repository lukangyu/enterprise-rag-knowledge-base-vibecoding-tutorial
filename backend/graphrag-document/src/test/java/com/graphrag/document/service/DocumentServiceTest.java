package com.graphrag.document.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.common.storage.service.MinioService;
import com.graphrag.document.dto.DocumentDTO;
import com.graphrag.document.dto.DocumentUploadRequest;
import com.graphrag.document.dto.DocumentUploadResponse;
import com.graphrag.document.entity.Document;
import com.graphrag.document.entity.TaskProgress;
import com.graphrag.document.enums.DocumentStatus;
import com.graphrag.document.mapper.DocumentChunkMapper;
import com.graphrag.document.mapper.DocumentMapper;
import com.graphrag.document.mapper.TaskProgressMapper;
import com.graphrag.document.producer.DocumentMessageProducer;
import com.graphrag.document.service.impl.DocumentServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DocumentServiceTest {

    @Mock
    private DocumentMapper documentMapper;

    @Mock
    private MinioService minioService;

    @Mock
    private DocumentMessageProducer documentMessageProducer;

    @Mock
    private TaskStatusManager taskStatusManager;

    @Mock
    private TaskProgressMapper taskProgressMapper;

    @Mock
    private DocumentChunkMapper documentChunkMapper;

    private ObjectMapper objectMapper;

    private DocumentServiceImpl documentService;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        documentService = new DocumentServiceImpl(
                documentMapper,
                minioService,
                documentMessageProducer,
                taskStatusManager,
                objectMapper,
                taskProgressMapper,
                documentChunkMapper
        );
    }

    @Test
    @DisplayName("测试成功上传文档")
    void testUploadDocument_Success() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.pdf",
                "application/pdf",
                "test content".getBytes()
        );

        DocumentUploadRequest request = new DocumentUploadRequest();
        request.setTitle("Test Document");
        request.setCategory("test");

        when(documentMapper.findByContentHash(anyString())).thenReturn(Optional.empty());
        when(minioService.uploadFile(any())).thenReturn("documents/test.pdf");
        doNothing().when(documentMapper).insert(any(Document.class));
        when(taskStatusManager.initProgress(anyString())).thenReturn(new TaskProgress());
        when(documentMessageProducer.sendFullProcessMessage(anyString()))
                .thenReturn(CompletableFuture.completedFuture(null));

        DocumentUploadResponse response = documentService.uploadDocument(file, request);

        assertNotNull(response);
        assertNotNull(response.getDocId());
        assertEquals("PENDING", response.getStatus());
        verify(documentMapper).insert(any(Document.class));
        verify(taskStatusManager).initProgress(anyString());
        verify(documentMessageProducer).sendFullProcessMessage(anyString());
    }

    @Test
    @DisplayName("测试无效文件类型")
    void testUploadDocument_InvalidFileType() {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.xyz",
                "application/octet-stream",
                "test content".getBytes()
        );

        DocumentUploadRequest request = new DocumentUploadRequest();
        request.setTitle("Test Document");

        assertThrows(BusinessException.class, () -> {
            documentService.uploadDocument(file, request);
        });

        verify(documentMapper, never()).insert(any());
    }

    @Test
    @DisplayName("测试重复内容文档")
    void testUploadDocument_DuplicateContent() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.pdf",
                "application/pdf",
                "test content".getBytes()
        );

        DocumentUploadRequest request = new DocumentUploadRequest();
        request.setTitle("Test Document");

        Document existingDocument = new Document();
        existingDocument.setId("existing-doc-id");
        existingDocument.setTitle("Existing Document");
        existingDocument.setStatus(DocumentStatus.PENDING.getCode());

        when(documentMapper.findByContentHash(anyString())).thenReturn(Optional.of(existingDocument));

        DocumentUploadResponse response = documentService.uploadDocument(file, request);

        assertNotNull(response);
        assertEquals("existing-doc-id", response.getDocId());
        assertEquals("PENDING", response.getStatus());
        verify(minioService, never()).uploadFile(any());
        verify(documentMapper, never()).insert(any());
    }

    @Test
    @DisplayName("测试成功获取文档")
    void testGetDocumentById_Success() {
        String docId = "test-doc-id";
        Document document = new Document();
        document.setId(docId);
        document.setTitle("Test Document");
        document.setStatus(DocumentStatus.COMPLETED.getCode());

        when(documentMapper.findById(docId)).thenReturn(Optional.of(document));

        DocumentDTO result = documentService.getDocumentById(docId);

        assertNotNull(result);
        assertEquals(docId, result.getId());
        assertEquals("Test Document", result.getTitle());
    }

    @Test
    @DisplayName("测试获取不存在的文档")
    void testGetDocumentById_NotFound() {
        String docId = "non-existent-id";
        when(documentMapper.findById(docId)).thenReturn(Optional.empty());

        assertThrows(BusinessException.class, () -> {
            documentService.getDocumentById(docId);
        });
    }

    @Test
    @DisplayName("测试成功删除文档")
    void testDeleteDocument_Success() {
        String docId = "test-doc-id";
        Document document = new Document();
        document.setId(docId);
        document.setFilePath("documents/test.pdf");

        when(documentMapper.findById(docId)).thenReturn(Optional.of(document));
        doNothing().when(minioService).deleteFile(anyString());
        doNothing().when(documentChunkMapper).deleteByDocId(docId);
        doNothing().when(taskProgressMapper).deleteByDocId(docId);
        doNothing().when(documentMapper).deleteById(docId);

        assertDoesNotThrow(() -> {
            documentService.deleteDocument(docId);
        });

        verify(minioService).deleteFile("documents/test.pdf");
        verify(documentChunkMapper).deleteByDocId(docId);
        verify(taskProgressMapper).deleteByDocId(docId);
        verify(documentMapper).deleteById(docId);
    }

    @Test
    @DisplayName("测试成功更新元数据")
    void testUpdateMetadata_Success() throws Exception {
        String docId = "test-doc-id";
        Document document = new Document();
        document.setId(docId);
        document.setTitle("Test Document");
        document.setMetadata("{}");

        when(documentMapper.findById(docId)).thenReturn(Optional.of(document));
        doNothing().when(documentMapper).updateById(any(Document.class));

        Map<String, Object> metadata = Map.of("key", "value", "category", "test");
        DocumentDTO result = documentService.updateMetadata(docId, metadata);

        assertNotNull(result);
        verify(documentMapper).updateById(any(Document.class));
    }

    @Test
    @DisplayName("测试更新不存在文档的元数据")
    void testUpdateMetadata_DocumentNotFound() {
        String docId = "non-existent-id";
        when(documentMapper.findById(docId)).thenReturn(Optional.empty());

        Map<String, Object> metadata = Map.of("key", "value");

        assertThrows(BusinessException.class, () -> {
            documentService.updateMetadata(docId, metadata);
        });
    }
}
