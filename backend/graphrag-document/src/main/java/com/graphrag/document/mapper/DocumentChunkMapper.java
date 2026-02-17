package com.graphrag.document.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.document.entity.DocumentChunk;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface DocumentChunkMapper extends BaseMapper<DocumentChunk> {

    @Delete("DELETE FROM document_chunks WHERE doc_id = #{docId}")
    int deleteByDocId(@Param("docId") String docId);
}
