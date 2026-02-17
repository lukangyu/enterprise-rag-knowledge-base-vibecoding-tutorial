package com.graphrag.document.controller;

import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.domain.Result;
import com.graphrag.document.dto.DocumentDTO;
import com.graphrag.document.dto.DocumentQueryRequest;
import com.graphrag.document.dto.DocumentUploadRequest;
import com.graphrag.document.dto.DocumentUploadResponse;
import com.graphrag.document.dto.MetadataUpdateRequest;
import com.graphrag.document.dto.ProgressResponse;
import com.graphrag.document.service.DocumentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/documents")
@Tag(name = "文档管理", description = "文档上传、查询、删除等接口")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "上传文档", description = "上传文档文件并触发处理流程")
    public Result<DocumentUploadResponse> uploadDocument(
            @Parameter(description = "文档文件") @RequestPart("file") MultipartFile file,
            @Parameter(description = "上传请求") @Valid @RequestPart("request") DocumentUploadRequest request) {
        DocumentUploadResponse response = documentService.uploadDocument(file, request);
        return Result.success(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文档详情", description = "根据文档ID获取文档详细信息")
    public Result<DocumentDTO> getDocument(
            @Parameter(description = "文档ID") @PathVariable String id) {
        DocumentDTO document = documentService.getDocumentById(id);
        return Result.success(document);
    }

    @PutMapping("/{id}/metadata")
    @Operation(summary = "更新文档元数据", description = "更新指定文档的元数据信息")
    public Result<DocumentDTO> updateMetadata(
            @Parameter(description = "文档ID") @PathVariable String id,
            @Parameter(description = "元数据更新请求") @RequestBody MetadataUpdateRequest request) {
        DocumentDTO document = documentService.updateMetadata(id, request.getMetadata());
        return Result.success(document);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文档", description = "删除指定文档及其关联文件")
    public Result<Void> deleteDocument(
            @Parameter(description = "文档ID") @PathVariable String id) {
        documentService.deleteDocument(id);
        return Result.success();
    }

    @PostMapping("/list")
    @Operation(summary = "查询文档列表", description = "分页查询文档列表")
    public Result<PageResult<DocumentDTO>> listDocuments(
            @Parameter(description = "查询条件") @RequestBody DocumentQueryRequest request) {
        PageResult<DocumentDTO> result = documentService.listDocuments(request);
        return Result.success(result);
    }

    @GetMapping("/{id}/progress")
    @Operation(summary = "获取文档处理进度", description = "根据文档ID获取文档处理进度信息")
    public Result<ProgressResponse> getProgress(
            @Parameter(description = "文档ID") @PathVariable String id) {
        ProgressResponse progress = documentService.getProgress(id);
        return Result.success(progress);
    }
}
