package com.xyun.platform.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xyun.platform.common.entity.XyUser;
import org.apache.ibatis.annotations.Mapper;

/**
 * XyUser 的 Mapper 接口
 */
@Mapper
public interface XyUserMapper extends BaseMapper<XyUser> {
}
