package com.graphrag.document.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.exception.BusinessException;
import com.graphrag.common.storage.service.MinioService;
import com.graphrag.document.dto.DocumentDTO;
import com.graphrag.document.dto.DocumentQueryRequest;
import com.graphrag.document.dto.DocumentUploadRequest;
import com.graphrag.document.dto.DocumentUploadResponse;
import com.graphrag.document.dto.ProgressResponse;
import com.graphrag.document.entity.Document;
import com.graphrag.document.entity.TaskProgress;
import com.graphrag.document.enums.DocumentStatus;
import com.graphrag.document.enums.DocumentType;
import com.graphrag.document.mapper.DocumentChunkMapper;
import com.graphrag.document.mapper.DocumentMapper;
import com.graphrag.document.mapper.TaskProgressMapper;
import com.graphrag.document.producer.DocumentMessageProducer;
import com.graphrag.document.service.DocumentService;
import com.graphrag.document.service.TaskStatusManager;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@Slf4j
public class DocumentServiceImpl implements DocumentService {

    private static final long MAX_FILE_SIZE = 100 * 1024 * 1024;

    private final DocumentMapper documentMapper;
    private final MinioService minioService;
    private final DocumentMessageProducer documentMessageProducer;
    private final TaskStatusManager taskStatusManager;
    private final ObjectMapper objectMapper;
    private final TaskProgressMapper taskProgressMapper;
    private final DocumentChunkMapper documentChunkMapper;

    public DocumentServiceImpl(DocumentMapper documentMapper,
                               MinioService minioService,
                               DocumentMessageProducer documentMessageProducer,
                               TaskStatusManager taskStatusManager,
                               ObjectMapper objectMapper,
                               TaskProgressMapper taskProgressMapper,
                               DocumentChunkMapper documentChunkMapper) {
        this.documentMapper = documentMapper;
        this.minioService = minioService;
        this.documentMessageProducer = documentMessageProducer;
        this.taskStatusManager = taskStatusManager;
        this.objectMapper = objectMapper;
        this.taskProgressMapper = taskProgressMapper;
        this.documentChunkMapper = documentChunkMapper;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DocumentUploadResponse uploadDocument(MultipartFile file, DocumentUploadRequest request) {
        validateFile(file);

        String originalFilename = file.getOriginalFilename();
        String extension = getFileExtension(originalFilename);
        DocumentType documentType = validateDocumentType(extension, file.getContentType());

        String contentHash = calculateContentHash(file);

        Optional<Document> existingDoc = documentMapper.findByContentHash(contentHash);
        if (existingDoc.isPresent()) {
            log.info("Document with same content hash already exists: docId={}", existingDoc.get().getId());
            return DocumentUploadResponse.success(existingDoc.get().getId());
        }

        String filePath;
        try {
            filePath = minioService.uploadFile(file);
        } catch (Exception e) {
            log.error("Failed to upload file to MinIO: {}", e.getMessage(), e);
            throw new BusinessException("文件上传失败: " + e.getMessage());
        }

        Document document = new Document();
        document.setTitle(request.getTitle());
        document.setSource(originalFilename);
        document.setDocType(documentType.name());
        document.setFilePath(filePath);
        document.setFileSize(file.getSize());
        document.setContentHash(contentHash);
        document.setStatus(DocumentStatus.PENDING.getCode());
        document.setMetadata(buildMetadata(request));
        document.setCreatedAt(LocalDateTime.now());
        document.setUpdatedAt(LocalDateTime.now());

        documentMapper.insert(document);
        log.info("Document saved to database: docId={}", document.getId());

        taskStatusManager.initProgress(document.getId());

        try {
            documentMessageProducer.sendFullProcessMessage(document.getId()).join();
            log.info("Document process message sent: docId={}", document.getId());
        } catch (Exception e) {
            log.error("Failed to send document process message: docId={}, error={}", document.getId(), e.getMessage(), e);
            throw new BusinessException("文档处理消息发送失败");
        }

        return DocumentUploadResponse.success(document.getId());
    }

    @Override
    public DocumentDTO getDocumentById(String id) {
        Optional<Document> document = documentMapper.findById(id);
        if (document.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }
        return DocumentDTO.fromEntity(document.get());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DocumentDTO updateMetadata(String id, Map<String, Object> metadata) {
        Optional<Document> optionalDocument = documentMapper.findById(id);
        if (optionalDocument.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }

        Document document = optionalDocument.get();
        try {
            Map<String, Object> existingMetadata = parseMetadata(document.getMetadata());
            existingMetadata.putAll(metadata);
            document.setMetadata(objectMapper.writeValueAsString(existingMetadata));
            document.setUpdatedAt(LocalDateTime.now());
            documentMapper.updateById(document);
            log.info("Document metadata updated: docId={}", id);
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize metadata: {}", e.getMessage(), e);
            throw new BusinessException("元数据更新失败");
        }

        return DocumentDTO.fromEntity(document);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocument(String id) {
        Optional<Document> optionalDocument = documentMapper.findById(id);
        if (optionalDocument.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }

        Document document = optionalDocument.get();

        if (document.getFilePath() != null) {
            minioService.deleteFile(document.getFilePath());
            log.info("File deleted from MinIO: {}", document.getFilePath());
        }

        documentChunkMapper.deleteByDocId(id);
        log.info("Document chunks deleted: docId={}", id);

        taskProgressMapper.deleteByDocId(id);
        log.info("Task progress deleted: docId={}", id);

        documentMapper.deleteById(id);
        log.info("Document deleted: docId={}", id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int batchDelete(List<String> ids) {
        int deletedCount = 0;
        for (String id : ids) {
            try {
                deleteDocument(id);
                deletedCount++;
            } catch (Exception e) {
                log.warn("Failed to delete document {}: {}", id, e.getMessage());
            }
        }
        log.info("Batch delete completed: {} of {} documents deleted", deletedCount, ids.size());
        return deletedCount;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void reprocessDocument(String id) {
        Optional<Document> optionalDocument = documentMapper.findById(id);
        if (optionalDocument.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }

        Document document = optionalDocument.get();
        document.setStatus(DocumentStatus.PENDING.getCode());
        document.setUpdatedAt(LocalDateTime.now());
        documentMapper.updateById(document);

        taskStatusManager.initProgress(id);

        try {
            documentMessageProducer.sendFullProcessMessage(id).join();
            log.info("Document reprocess message sent: docId={}", id);
        } catch (Exception e) {
            log.error("Failed to send reprocess message: docId={}, error={}", id, e.getMessage(), e);
            throw new BusinessException("文档重新处理消息发送失败");
        }
    }

    @Override
    public ResponseEntity<Resource> downloadDocument(String id) {
        Optional<Document> optionalDocument = documentMapper.findById(id);
        if (optionalDocument.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }

        Document document = optionalDocument.get();
        
        if (document.getFilePath() == null || document.getFilePath().isEmpty()) {
            throw new BusinessException("文档文件路径不存在");
        }

        try {
            InputStream inputStream = minioService.downloadFile(document.getFilePath());
            Resource resource = new InputStreamResource(inputStream);
            
            String contentType = determineContentType(document.getDocType());
            String filename = document.getTitle() != null ? 
                document.getTitle() + getFileExtensionForType(document.getDocType()) :
                document.getSource();

            return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, 
                    "attachment; filename=\"" + filename + "\"")
                .body(resource);
        } catch (Exception e) {
            log.error("Failed to download document: docId={}, error={}", id, e.getMessage(), e);
            throw new BusinessException("文档下载失败: " + e.getMessage());
        }
    }

    private String determineContentType(String docType) {
        if (docType == null) {
            return "application/octet-stream";
        }
        return switch (docType.toUpperCase()) {
            case "PDF" -> "application/pdf";
            case "DOC", "DOCX" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "MD", "TXT" -> "text/plain";
            default -> "application/octet-stream";
        };
    }

    private String getFileExtensionForType(String docType) {
        if (docType == null) {
            return "";
        }
        return switch (docType.toUpperCase()) {
            case "PDF" -> ".pdf";
            case "DOC" -> ".doc";
            case "DOCX" -> ".docx";
            case "MD" -> ".md";
            case "TXT" -> ".txt";
            default -> "";
        };
    }

    @Override
    public PageResult<DocumentDTO> listDocuments(DocumentQueryRequest request) {
        Page<Document> page = new Page<>(request.getPageNum(), request.getPageSize());

        LambdaQueryWrapper<Document> queryWrapper = new LambdaQueryWrapper<>();

        if (request.getTitle() != null && !request.getTitle().isEmpty()) {
            queryWrapper.like(Document::getTitle, request.getTitle());
        }
        if (request.getStatus() != null && !request.getStatus().isEmpty()) {
            queryWrapper.eq(Document::getStatus, request.getStatus());
        }
        if (request.getDocType() != null && !request.getDocType().isEmpty()) {
            queryWrapper.eq(Document::getDocType, request.getDocType());
        }
        if (request.getCreatedBy() != null && !request.getCreatedBy().isEmpty()) {
            queryWrapper.eq(Document::getCreatedBy, request.getCreatedBy());
        }
        if (request.getStartTime() != null && !request.getStartTime().isEmpty()) {
            LocalDateTime startTime = parseDateTime(request.getStartTime());
            if (startTime != null) {
                queryWrapper.ge(Document::getCreatedAt, startTime);
            }
        }
        if (request.getEndTime() != null && !request.getEndTime().isEmpty()) {
            LocalDateTime endTime = parseDateTime(request.getEndTime());
            if (endTime != null) {
                queryWrapper.le(Document::getCreatedAt, endTime);
            }
        }

        queryWrapper.orderByDesc(Document::getCreatedAt);

        IPage<Document> documentPage = documentMapper.selectPage(page, queryWrapper);

        List<DocumentDTO> documentDTOList = documentPage.getRecords().stream()
                .map(DocumentDTO::fromEntity)
                .toList();

        return PageResult.of(documentDTOList, documentPage.getTotal(), documentPage.getCurrent(), documentPage.getSize());
    }

    @Override
    public ProgressResponse getProgress(String id) {
        Optional<Document> optionalDocument = documentMapper.findById(id);
        if (optionalDocument.isEmpty()) {
            throw new BusinessException("文档不存在: " + id);
        }

        TaskProgress taskProgress = taskStatusManager.getProgress(id);
        if (taskProgress == null) {
            throw new BusinessException("文档处理进度不存在: " + id);
        }

        return ProgressResponse.fromEntity(taskProgress);
    }

    private LocalDateTime parseDateTime(String dateTimeStr) {
        if (dateTimeStr == null || dateTimeStr.isEmpty()) {
            return null;
        }
        try {
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            return LocalDateTime.parse(dateTimeStr, formatter);
        } catch (Exception e) {
            try {
                DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
                return LocalDateTime.parse(dateTimeStr + " 00:00:00", DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            } catch (Exception ex) {
                log.warn("Failed to parse datetime: {}", dateTimeStr);
                return null;
            }
        }
    }

    private void validateFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new BusinessException("上传文件不能为空");
        }

        if (file.getSize() > MAX_FILE_SIZE) {
            throw new BusinessException("文件大小不能超过100MB");
        }
    }

    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf(".") + 1).toLowerCase();
    }

    private DocumentType validateDocumentType(String extension, String contentType) {
        DocumentType typeByExtension = DocumentType.getByExtension(extension);
        DocumentType typeByMimeType = DocumentType.getByMimeType(contentType);

        if (typeByExtension == null && typeByMimeType == null) {
            throw new BusinessException("不支持的文件类型，仅支持PDF、DOC、DOCX、MD、TXT格式");
        }

        return typeByExtension != null ? typeByExtension : typeByMimeType;
    }

    private String calculateContentHash(MultipartFile file) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] fileBytes = file.getBytes();
            byte[] hashBytes = digest.digest(fileBytes);

            StringBuilder hexString = new StringBuilder();
            for (byte b : hashBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException | IOException e) {
            log.error("Failed to calculate content hash: {}", e.getMessage(), e);
            throw new BusinessException("文件哈希计算失败");
        }
    }

    private String buildMetadata(DocumentUploadRequest request) {
        try {
            Map<String, Object> metadata = new HashMap<>();
            if (request.getCategory() != null) {
                metadata.put("category", request.getCategory());
            }
            if (request.getTags() != null) {
                metadata.put("tags", request.getTags());
            }
            if (request.getAccessLevel() != null) {
                metadata.put("accessLevel", request.getAccessLevel());
            }
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            log.error("Failed to build metadata: {}", e.getMessage(), e);
            return "{}";
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> parseMetadata(String metadata) {
        if (metadata == null || metadata.isEmpty()) {
            return new HashMap<>();
        }
        try {
            return objectMapper.readValue(metadata, Map.class);
        } catch (JsonProcessingException e) {
            log.error("Failed to parse metadata: {}", e.getMessage(), e);
            return new HashMap<>();
        }
    }
}
