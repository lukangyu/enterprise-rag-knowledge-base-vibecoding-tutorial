package com.graphrag.document.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.io.Serializable;
import java.util.List;

@Data
public class DocumentUploadRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    @NotBlank(message = "文档标题不能为空")
    @Size(max = 255, message = "文档标题长度不能超过255个字符")
    private String title;

    @Size(max = 100, message = "文档分类长度不能超过100个字符")
    private String category;

    @Size(max = 10, message = "标签数量不能超过10个")
    private List<String> tags;

    private String accessLevel;
}
