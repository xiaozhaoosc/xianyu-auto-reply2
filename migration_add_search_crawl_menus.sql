-- ============================================================
-- 迁移脚本: 新增「商品搜索/采集」和「定时采集」侧边栏菜单项
-- ============================================================
-- 背景:
--   前端 navigation.ts 已定义这两个菜单项:
--     - item-search       (商品搜索/采集) → /item-search
--     - goofish-crawler   (定时采集)      → /goofish-scheduled-crawler
--
--   后端路由已存在:
--     - /api/v1/search         (商品搜索)
--     - /api/v1/goofish/crawler (定时采集 CRUD)
--     - /api/v1/goofish/tasks   (采集任务管理)
--
--   数据库表已存在:
--     - xy_goofish_crawl_jobs   (采集任务表)
--     - xy_goofish_crawl_items  (采集商品表)
--
--   本脚本确保这两个菜单对所有用户可见（从隐藏列表中移除）
-- ============================================================

-- Step 1: 从 navigation.hidden_menu_keys 中移除 item-search 和 goofish-crawler
-- 如果该设置不存在，说明所有菜单默认可见，无需操作
UPDATE `xy_system_settings`
SET `value` = TRIM(
    REPLACE(
        REPLACE(
            REPLACE(
                REPLACE(`value`, ',item-search', ''),
            'item-search,', ''),
        'item-search', ''),
    '  ', ' ')
),
    `updated_at` = NOW()
WHERE `key` = 'navigation.hidden_menu_keys'
  AND (`value` LIKE '%item-search%');

UPDATE `xy_system_settings`
SET `value` = TRIM(
    REPLACE(
        REPLACE(
            REPLACE(
                REPLACE(`value`, ',goofish-crawler', ''),
            'goofish-crawler,', ''),
        'goofish-crawler', ''),
    '  ', ' ')
),
    `updated_at` = NOW()
WHERE `key` = 'navigation.hidden_menu_keys'
  AND (`value` LIKE '%goofish-crawler%');

-- Step 2: 清理可能产生的空值或纯逗号
UPDATE `xy_system_settings`
SET `value` = TRIM(TRIM(BOTH ',' FROM `value`)),
    `updated_at` = NOW()
WHERE `key` = 'navigation.hidden_menu_keys'
  AND (`value` LIKE ',%' OR `value` LIKE '%,' OR `value` = '');

-- Step 3: 验证结果
SELECT `key`, `value`, `updated_at`
FROM `xy_system_settings`
WHERE `key` = 'navigation.hidden_menu_keys';
