package com.graphrag.common.core.domain;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.List;

@Data
@Schema(description = "分页响应结果")
public class PageResult<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "数据列表")
    private List<T> list;

    @Schema(description = "总记录数")
    private Long total;

    @Schema(description = "当前页码")
    private Long pageNum;

    @Schema(description = "每页大小")
    private Long pageSize;

    @Schema(description = "总页数")
    private Long pages;

    @Schema(description = "是否有下一页")
    private Boolean hasNext;

    @Schema(description = "是否有上一页")
    private Boolean hasPrevious;

    public PageResult() {
    }

    public PageResult(List<T> list, Long total, Long pageNum, Long pageSize) {
        this.list = list;
        this.total = total;
        this.pageNum = pageNum;
        this.pageSize = pageSize;
        this.pages = (total + pageSize - 1) / pageSize;
        this.hasNext = pageNum < pages;
        this.hasPrevious = pageNum > 1;
    }

    public static <T> PageResult<T> of(List<T> list, Long total, Long pageNum, Long pageSize) {
        return new PageResult<>(list, total, pageNum, pageSize);
    }

    public static <T> PageResult<T> empty() {
        return new PageResult<>(List.of(), 0L, 1L, 10L);
    }

    @Data
    @Schema(description = "分页请求参数")
    public static class PageRequest implements Serializable {

        private static final long serialVersionUID = 1L;

        @Schema(description = "当前页码", example = "1")
        private Integer pageNum = 1;

        @Schema(description = "每页大小", example = "10")
        private Integer pageSize = 10;
    }
}
