package com.graphrag.document.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.document.entity.Document;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.Optional;

@Mapper
public interface DocumentMapper extends BaseMapper<Document> {

    @Select("SELECT * FROM documents WHERE content_hash = #{contentHash} LIMIT 1")
    Optional<Document> findByContentHash(String contentHash);

    @Select("SELECT * FROM documents WHERE id = #{id}")
    Optional<Document> findById(String id);
}
