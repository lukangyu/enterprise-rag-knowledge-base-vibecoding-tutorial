package com.graphrag.document.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.document.entity.TaskProgress;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.Optional;

@Mapper
public interface TaskProgressMapper extends BaseMapper<TaskProgress> {

    @Select("SELECT * FROM task_progress WHERE doc_id = #{docId}")
    Optional<TaskProgress> findByDocId(@Param("docId") String docId);

    @Delete("DELETE FROM task_progress WHERE doc_id = #{docId}")
    int deleteByDocId(@Param("docId") String docId);
}
