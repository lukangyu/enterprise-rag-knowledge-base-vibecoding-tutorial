package com.graphrag.document.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Map;

@Data
@Schema(description = "元数据更新请求")
public class MetadataUpdateRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "元数据")
    private Map<String, Object> metadata;
}
