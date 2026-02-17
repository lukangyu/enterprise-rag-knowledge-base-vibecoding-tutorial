package com.graphrag.document.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.document.dto.DocumentDTO;
import com.graphrag.document.dto.DocumentQueryRequest;
import com.graphrag.document.dto.DocumentUploadRequest;
import com.graphrag.document.dto.DocumentUploadResponse;
import com.graphrag.document.dto.MetadataUpdateRequest;
import com.graphrag.document.dto.ProgressResponse;
import com.graphrag.document.entity.TaskProgress;
import com.graphrag.document.service.DocumentService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(DocumentController.class)
class DocumentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private DocumentService documentService;

    private DocumentDTO testDocumentDTO;
    private DocumentUploadResponse testUploadResponse;
    private ProgressResponse testProgressResponse;

    @BeforeEach
    void setUp() {
        testDocumentDTO = DocumentDTO.builder()
                .id("test-doc-id")
                .title("Test Document")
                .source("test.pdf")
                .docType("PDF")
                .status("COMPLETED")
                .fileSize(1024L)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        testUploadResponse = DocumentUploadResponse.success("test-doc-id");

        TaskProgress taskProgress = new TaskProgress();
        taskProgress.setDocId("test-doc-id");
        taskProgress.setCurrentStage("COMPLETED");
        taskProgress.setProgress(100);
        taskProgress.setRetryCount(0);
        testProgressResponse = ProgressResponse.fromEntity(taskProgress);
    }

    @Test
    @DisplayName("测试上传文档接口")
    void testUploadDocument() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.pdf",
                "application/pdf",
                "test content".getBytes()
        );

        DocumentUploadRequest request = new DocumentUploadRequest();
        request.setTitle("Test Document");
        MockMultipartFile requestPart = new MockMultipartFile(
                "request",
                "",
                "application/json",
                objectMapper.writeValueAsBytes(request)
        );

        when(documentService.uploadDocument(any(), any())).thenReturn(testUploadResponse);

        mockMvc.perform(multipart("/api/v1/documents/upload")
                        .file(file)
                        .file(requestPart))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.docId").value("test-doc-id"))
                .andExpect(jsonPath("$.data.status").value("PENDING"));

        verify(documentService).uploadDocument(any(), any());
    }

    @Test
    @DisplayName("测试获取文档接口")
    void testGetDocument() throws Exception {
        when(documentService.getDocumentById("test-doc-id")).thenReturn(testDocumentDTO);

        mockMvc.perform(get("/api/v1/documents/test-doc-id"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.id").value("test-doc-id"))
                .andExpect(jsonPath("$.data.title").value("Test Document"))
                .andExpect(jsonPath("$.data.status").value("COMPLETED"));

        verify(documentService).getDocumentById("test-doc-id");
    }

    @Test
    @DisplayName("测试获取不存在的文档")
    void testGetDocument_NotFound() throws Exception {
        when(documentService.getDocumentById("non-existent-id"))
                .thenThrow(new BusinessException("文档不存在: non-existent-id"));

        mockMvc.perform(get("/api/v1/documents/non-existent-id"))
                .andExpect(status().isInternalServerError());

        verify(documentService).getDocumentById("non-existent-id");
    }

    @Test
    @DisplayName("测试删除文档接口")
    void testDeleteDocument() throws Exception {
        doNothing().when(documentService).deleteDocument("test-doc-id");

        mockMvc.perform(delete("/api/v1/documents/test-doc-id"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(documentService).deleteDocument("test-doc-id");
    }

    @Test
    @DisplayName("测试文档列表接口")
    void testListDocuments() throws Exception {
        DocumentQueryRequest queryRequest = new DocumentQueryRequest();
        queryRequest.setPageNum(1);
        queryRequest.setPageSize(10);

        PageResult<DocumentDTO> pageResult = PageResult.of(
                List.of(testDocumentDTO),
                1L,
                1L,
                10L
        );

        when(documentService.listDocuments(any(DocumentQueryRequest.class))).thenReturn(pageResult);

        mockMvc.perform(post("/api/v1/documents/list")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(queryRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.list[0].id").value("test-doc-id"));

        verify(documentService).listDocuments(any(DocumentQueryRequest.class));
    }

    @Test
    @DisplayName("测试获取进度接口")
    void testGetProgress() throws Exception {
        when(documentService.getProgress("test-doc-id")).thenReturn(testProgressResponse);

        mockMvc.perform(get("/api/v1/documents/test-doc-id/progress"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.docId").value("test-doc-id"))
                .andExpect(jsonPath("$.data.currentStage").value("COMPLETED"))
                .andExpect(jsonPath("$.data.progress").value(100));

        verify(documentService).getProgress("test-doc-id");
    }

    @Test
    @DisplayName("测试更新元数据接口")
    void testUpdateMetadata() throws Exception {
        MetadataUpdateRequest request = new MetadataUpdateRequest();
        request.setMetadata(Map.of("category", "test"));

        DocumentDTO updatedDTO = DocumentDTO.builder()
                .id("test-doc-id")
                .title("Test Document")
                .metadata("{\"category\":\"test\"}")
                .build();

        when(documentService.updateMetadata(anyString(), any())).thenReturn(updatedDTO);

        mockMvc.perform(put("/api/v1/documents/test-doc-id/metadata")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.id").value("test-doc-id"));

        verify(documentService).updateMetadata(anyString(), any());
    }
}
