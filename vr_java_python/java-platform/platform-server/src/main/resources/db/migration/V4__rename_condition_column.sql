-- 修复 MySQL 保留字冲突：将 condition 列重命名为 item_condition
ALTER TABLE xy_product_materials CHANGE COLUMN `condition` `item_condition` TEXT COMMENT '成色/状况';
