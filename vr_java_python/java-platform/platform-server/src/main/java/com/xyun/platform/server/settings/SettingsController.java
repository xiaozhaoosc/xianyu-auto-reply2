package com.xyun.platform.server.settings;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XySystemSetting;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 系统设置 API — 读写 xy_system_settings 表
 */
@RestController
@RequestMapping("/api/settings")
@RequiredArgsConstructor
public class SettingsController {

    private final SettingsService settingsService;

    /** 获取所有设置（以 key-value 映射返回） */
    @GetMapping
    public ApiResult<Map<String, String>> getAllSettings() {
        return settingsService.getAllSettings();
    }

    /** 批量更新设置 */
    @PutMapping
    public ApiResult<Void> updateSettings(@RequestBody Map<String, String> settings) {
        return settingsService.updateSettings(settings);
    }

    /** 获取单个设置 */
    @GetMapping("/{key}")
    public ApiResult<String> getSetting(@PathVariable String key) {
        return settingsService.getSetting(key);
    }

    /** 设置单个值 */
    @PutMapping("/{key}")
    public ApiResult<Void> setSetting(@PathVariable String key, @RequestBody String value) {
        return settingsService.setSetting(key, value);
    }
}
