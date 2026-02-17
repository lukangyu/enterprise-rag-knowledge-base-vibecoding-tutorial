package com.graphrag.document.dto;

import com.graphrag.document.entity.Document;
import lombok.Builder;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@Builder
public class DocumentDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    private String id;

    private String title;

    private String source;

    private String docType;

    private String filePath;

    private Long fileSize;

    private String contentHash;

    private String status;

    private String metadata;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    private String createdBy;

    private String updatedBy;

    public static DocumentDTO fromEntity(Document document) {
        if (document == null) {
            return null;
        }
        return DocumentDTO.builder()
                .id(document.getId())
                .title(document.getTitle())
                .source(document.getSource())
                .docType(document.getDocType())
                .filePath(document.getFilePath())
                .fileSize(document.getFileSize())
                .contentHash(document.getContentHash())
                .status(document.getStatus())
                .metadata(document.getMetadata())
                .createdAt(document.getCreatedAt())
                .updatedAt(document.getUpdatedAt())
                .createdBy(document.getCreatedBy())
                .updatedBy(document.getUpdatedBy())
                .build();
    }
}
