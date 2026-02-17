package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "密码更新请求")
public class PasswordUpdateRequest {

    @NotBlank(message = "原密码不能为空")
    @Schema(description = "原密码", example = "oldPassword123")
    private String oldPassword;

    @NotBlank(message = "新密码不能为空")
    @Schema(description = "新密码", example = "newPassword123")
    private String newPassword;
}
