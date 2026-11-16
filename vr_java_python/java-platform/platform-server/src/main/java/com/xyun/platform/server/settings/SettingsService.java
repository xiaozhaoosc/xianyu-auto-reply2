package com.xyun.platform.server.settings;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XySystemSetting;
import com.xyun.platform.server.mapper.XySystemSettingMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 系统设置服务 — 读写 xy_system_settings 表
 * 使用自定义 Mapper 方法（含反引号转义），避免 MySQL 保留字冲突
 */
@Service
@RequiredArgsConstructor
public class SettingsService {

    private final XySystemSettingMapper systemSettingMapper;

    /** 获取所有设置，以 key-value 映射返回 */
    public ApiResult<Map<String, String>> getAllSettings() {
        List<XySystemSetting> list = systemSettingMapper.selectAllSettings();
        Map<String, String> map = new LinkedHashMap<>();
        for (XySystemSetting s : list) {
            map.put(s.getKey(), s.getValue());
        }
        return ApiResult.ok(map);
    }

    /** 批量更新设置 */
    public ApiResult<Void> updateSettings(Map<String, String> settings) {
        settings.forEach(this::upsert);
        return ApiResult.ok(null);
    }

    /** 获取单个设置值 */
    public ApiResult<String> getSetting(String key) {
        XySystemSetting setting = systemSettingMapper.selectByKey(key);
        return ApiResult.ok(setting != null ? setting.getValue() : null);
    }

    /** 设置单个值 */
    public ApiResult<Void> setSetting(String key, String value) {
        upsert(key, value);
        return ApiResult.ok(null);
    }

    /** 插入或更新 */
    private void upsert(String key, String value) {
        XySystemSetting existing = systemSettingMapper.selectByKey(key);
        if (existing != null) {
            existing.setValue(value);
            existing.setUpdatedAt(LocalDateTime.now());
            systemSettingMapper.updateByKey(existing);
        } else {
            XySystemSetting setting = new XySystemSetting();
            setting.setKey(key);
            setting.setValue(value);
            setting.setUpdatedAt(LocalDateTime.now());
            systemSettingMapper.insertSetting(setting);
        }
    }
}
