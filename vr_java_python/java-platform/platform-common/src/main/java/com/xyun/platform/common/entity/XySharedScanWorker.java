package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 共享扫码工作节点实体
 */
@Getter
@Setter
@TableName("xy_shared_scan_workers")
public class XySharedScanWorker extends BaseEntity {

    /** 所属共享会话 ID */
    private String sharedSessionId;

    /** 子会话 ID */
    private String subSessionId;

    /** 闲鱼会话 ID */
    private String xianyuSessionId;

    /** 工作节点状态 */
    private String status;

    /** 二维码地址 */
    private String qrCodeUrl;

    /** 关联账户标识 */
    private String accountId;

    /** Cookie 是否已保存 */
    private Boolean cookieSaved;
}
