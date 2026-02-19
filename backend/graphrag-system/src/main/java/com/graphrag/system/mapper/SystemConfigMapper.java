package com.graphrag.system.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.graphrag.system.domain.entity.SystemConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Optional;

@Mapper
public interface SystemConfigMapper extends BaseMapper<SystemConfig> {
    
    Optional<SystemConfig> selectByConfigKey(@Param("configKey") String configKey);
    
    List<SystemConfig> selectByConfigType(@Param("configType") String configType);
    
    int updateByConfigKey(@Param("configKey") String configKey, @Param("configValue") String configValue);
}
