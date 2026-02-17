package com.graphrag.document.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentUploadResponse implements Serializable {

    private static final long serialVersionUID = 1L;

    private String docId;

    private String status;

    private String message;

    public static DocumentUploadResponse success(String docId) {
        return DocumentUploadResponse.builder()
                .docId(docId)
                .status("PENDING")
                .message("文档上传成功，正在处理中")
                .build();
    }

    public static DocumentUploadResponse fail(String message) {
        return DocumentUploadResponse.builder()
                .status("FAILED")
                .message(message)
                .build();
    }
}
