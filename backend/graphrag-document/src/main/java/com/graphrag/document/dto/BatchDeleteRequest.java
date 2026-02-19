package com.graphrag.document.dto;

import lombok.Data;

import java.util.List;

@Data
public class BatchDeleteRequest {
    private List<String> ids;
}
