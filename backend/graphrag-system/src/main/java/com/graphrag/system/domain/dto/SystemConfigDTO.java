package com.graphrag.system.domain.dto;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;

@Data
public class SystemConfigDTO {
    private Long id;
    
    @NotBlank(message = "Config key cannot be empty")
    private String configKey;
    
    private String configValue;
    private String configType;
    private String description;
    private Integer sortOrder;
    private Integer status;
}
