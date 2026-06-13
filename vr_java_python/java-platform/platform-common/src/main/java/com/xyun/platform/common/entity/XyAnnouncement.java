package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 公告实体
 */
@Getter
@Setter
@TableName("xy_announcements")
public class XyAnnouncement extends BaseEntity {

    /** 公告标题 */
    private String title;

    /** 公告内容 */
    private String content;

    /** 是否已删除 */
    private Boolean isDeleted;
}
