package com.graphrag.document.dto;

import com.graphrag.common.core.domain.PageResult;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

@Data
@EqualsAndHashCode(callSuper = true)
public class DocumentQueryRequest extends PageResult.PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String title;

    private String status;

    private String docType;

    private String category;

    private String createdBy;

    private String startTime;

    private String endTime;
}
