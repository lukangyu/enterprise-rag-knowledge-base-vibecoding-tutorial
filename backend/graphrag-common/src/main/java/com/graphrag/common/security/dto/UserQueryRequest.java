package com.graphrag.common.security.dto;

import com.graphrag.common.core.domain.PageResult;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "用户查询请求")
public class UserQueryRequest extends PageResult.PageRequest {

    @Schema(description = "用户名")
    private String username;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "手机号")
    private String phone;

    @Schema(description = "真实姓名")
    private String realName;

    @Schema(description = "状态:0-正常,1-禁用")
    private Integer status;

    @Schema(description = "角色ID")
    private Long roleId;
}
