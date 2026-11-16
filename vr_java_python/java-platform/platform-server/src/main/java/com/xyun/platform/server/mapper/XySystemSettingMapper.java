package com.xyun.platform.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xyun.platform.common.entity.XySystemSetting;
import org.apache.ibatis.annotations.*;

import java.util.List;

/**
 * XySystemSetting 的 Mapper 接口
 * — key/value 是 MySQL 保留字，需反引号转义，BaseMapper 自动生成的 SQL 不含反引号，
 *   因此用 @Select/@Insert/@Update 注解覆盖默认方法
 */
@Mapper
public interface XySystemSettingMapper extends BaseMapper<XySystemSetting> {

    /** 查询所有设置 */
    @Select("SELECT `key`, `value`, description, updated_at FROM xy_system_settings")
    List<XySystemSetting> selectAllSettings();

    /** 按 key 查询单条 */
    @Select("SELECT `key`, `value`, description, updated_at FROM xy_system_settings WHERE `key` = #{key}")
    XySystemSetting selectByKey(@Param("key") String key);

    /** 插入新设置 */
    @Insert("INSERT INTO xy_system_settings (`key`, `value`, description, updated_at) " +
            "VALUES (#{key}, #{value}, #{description}, #{updatedAt})")
    int insertSetting(XySystemSetting setting);

    /** 按 key 更新设置 */
    @Update("UPDATE xy_system_settings SET `value` = #{value}, description = #{description}, " +
            "updated_at = #{updatedAt} WHERE `key` = #{key}")
    int updateByKey(XySystemSetting setting);

    /** 按 key 删除 */
    @Delete("DELETE FROM xy_system_settings WHERE `key` = #{key}")
    int deleteByKey(@Param("key") String key);
}
