/**
 * 系统设置页面。
 *
 * 功能模块按 Tab 展示，各卡片使用独立保存入口，避免跨模块覆盖未保存内容。
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import {
  buildHiddenMenuSettingsPayload,
  getHiddenMenuKeysFromSettings,
  getSystemSettings,
  normalizeAuthFooterAdSettings,
  normalizeDisclaimerSettings,
  normalizeLoginBrandingSettings,
  testEmailSend,
} from '@/api/settings'
import { PageLoading } from '@/components/common/Loading'
import { useAuthStore } from '@/store/authStore'
import { useMenuVisibilityStore } from '@/store/menuVisibilityStore'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'
import {
  applyThemeSettings,
  normalizeThemeAppearanceSettings,
  normalizeThemeFontSettings,
} from '@/utils/theme'
import type {
  AuthFooterAdSettings,
  DisclaimerSettings,
  LoginBrandingSettings,
  SystemSettings,
  ThemeAppearanceSettings,
  ThemeColorPreset,
  ThemeEffect,
  ThemeFontFamily,
  ThemeFontSettings,
} from '@/types'
import { AppearanceSettingsTab } from './AppearanceSettingsTab'
import { BasicSettingsTab } from './BasicSettingsTab'
import { ContactSettingsTab } from './ContactSettingsTab'
import { PaymentSettingsTab } from './PaymentSettingsTab'
import { ServiceRestartCard } from './ServiceRestartCard'
import { SystemSettingsTabs } from './SystemSettingsTabs'
import { TestEmailModal } from './TestEmailModal'
import { UserNetworkSettingsTab } from './UserNetworkSettingsTab'
import { useQrcodeSettings } from './useQrcodeSettings'
import { useSettingsActions } from './useSettingsActions'
import type { SettingsTab } from './settingsTypes'

export function Settings() {
  const { addToast } = useUIStore()
  const { isAuthenticated, token, _hasHydrated, user } = useAuthStore()
  const { isExeMode, setHiddenMenuKeys, setIsExeMode } = useMenuVisibilityStore()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<SettingsTab>('basic')
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [showTestEmailModal, setShowTestEmailModal] = useState(false)
  const [testEmail, setTestEmail] = useState('')
  const [sendingTestEmail, setSendingTestEmail] = useState(false)
  const settingsRef = useRef<SystemSettings | null>(null)
  const qrcodes = useQrcodeSettings()

  settingsRef.current = settings
  const getCurrentSettings = useCallback(() => settingsRef.current, [])
  const actions = useSettingsActions(getCurrentSettings)

  const loadSettings = useCallback(async () => {
    if (!_hasHydrated || !isAuthenticated || !token || !user?.is_admin) return
    setLoading(true)
    try {
      const result = await getSystemSettings()
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: '加载系统设置失败' })
        return
      }
      applyThemeSettings(result.data)
      setSettings(result.data)
      setIsExeMode(Boolean(result.data['runtime.is_exe_mode']))
      setHiddenMenuKeys(getHiddenMenuKeysFromSettings(result.data))
      await qrcodes.loadQrcodes()
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载系统设置失败') })
    } finally {
      setLoading(false)
    }
  }, [_hasHydrated, addToast, isAuthenticated, qrcodes.loadQrcodes, setHiddenMenuKeys, setIsExeMode, token, user?.is_admin])

  useEffect(() => {
    if (!_hasHydrated || !isAuthenticated || !token) return
    if (!user?.is_admin) {
      setLoading(false)
      return
    }
    void loadSettings()
  }, [_hasHydrated, isAuthenticated, loadSettings, token, user?.is_admin])

  const handleTestEmail = useCallback(async () => {
    const email = testEmail.trim()
    setSendingTestEmail(true)
    try {
      const result = await testEmailSend(email)
      if (result.success) {
        addToast({ type: 'success', message: result.message || '测试邮件发送成功' })
        setShowTestEmailModal(false)
        setTestEmail('')
      } else {
        addToast({ type: 'error', message: result.message || '发送测试邮件失败' })
      }
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '发送测试邮件失败') })
    } finally {
      setSendingTestEmail(false)
    }
  }, [addToast, testEmail])

  const handleThemeAppearanceChange = (key: keyof ThemeAppearanceSettings, value: ThemeEffect | ThemeColorPreset) => {
    setSettings((current) => {
      const next = { ...(current ?? {}), [key]: value }
      applyThemeSettings(next)
      return next
    })
  }

  const handleThemeFontChange = (key: keyof ThemeFontSettings, value: ThemeFontFamily) => {
    setSettings((current) => {
      const next = { ...(current ?? {}), [key]: value }
      applyThemeSettings(next)
      return next
    })
  }

  if (!user?.is_admin) return <Navigate to="/dashboard" replace />
  if (loading) return <PageLoading />

  const themeAppearance = normalizeThemeAppearanceSettings(settings)
  const themeFont = normalizeThemeFontSettings(settings)
  const loginBranding = normalizeLoginBrandingSettings(settings)
  const authFooterAd = normalizeAuthFooterAdSettings(settings)
  const disclaimer = normalizeDisclaimerSettings(settings)

  return (
    <div className="space-y-4">
      <div className="page-header flex-between flex-wrap gap-4">
        <div>
          <h1 className="page-title">系统设置</h1>
          <p className="page-description">配置系统全局设置</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadSettings} className="btn-ios-secondary">
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-ios-primary">
            {saving ? <ButtonLoading /> : <Save className="w-4 h-4" />}
            保存设置
          </button>
        </div>
      </div>

      {/* 服务管理：消息服务 / 后端服务 / 定时任务服务 重启（仅管理员可见，置于最上方） */}
      {user?.is_admin && <ServiceRestartCard />}

      {/* 基础设置 + SMTP邮件配置（仅管理员可见） */}
      {user?.is_admin && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* 基础设置 */}
          <div className="vben-card">
            <div className="vben-card-header">
              <h2 className="vben-card-title">
                <SettingsIcon className="w-4 h-4" />
                基础设置
              </h2>
            </div>
            <div className="vben-card-body space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-700">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">允许用户注册</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">开启后允许新用户注册账号</p>
                </div>
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={Boolean(settings?.registration_enabled ?? false)}
                    onChange={(e) => setSettings(s => s ? { ...s, registration_enabled: e.target.checked } : null)}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <div className="flex items-center justify-between py-3">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">显示默认登录信息</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">登录页面显示默认账号密码提示</p>
                </div>
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={Boolean(settings?.show_default_login_info ?? false)}
                    onChange={(e) => setSettings(s => s ? { ...s, show_default_login_info: e.target.checked } : null)}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <div className="flex items-center justify-between py-3 border-t border-slate-100 dark:border-slate-700">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">登录滑动验证码</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">开启后账号密码登录需要完成滑动验证</p>
                </div>
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={Boolean(settings?.login_captcha_enabled ?? true)}
                    onChange={(e) => setSettings(s => s ? { ...s, login_captcha_enabled: e.target.checked } : null)}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <div className="flex items-center justify-between py-3 border-t border-slate-100 dark:border-slate-700">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">日志保留天数</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">所有模块日志保留天数，修改后实时生效（1~365天）</p>
                </div>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={settings?.['log.retention_days'] || '7'}
                  onChange={(e) => {
                    const val = e.target.value
                    if (val === '' || /^\d+$/.test(val)) {
                      setSettings(s => s ? { ...s, 'log.retention_days': val } : null)
                    }
                  }}
                  className="input-ios w-24 text-center"
                />
              </div>
              <div className="flex items-center justify-between py-3 border-t border-slate-100 dark:border-slate-700">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">人脸验证超时自动禁用</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">关闭后人脸验证超时不会自动禁用账号</p>
                </div>
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={Boolean(settings?.['account.face_verify_timeout_disable'] ?? true)}
                    onChange={(e) => setSettings(s => s ? { ...s, 'account.face_verify_timeout_disable': e.target.checked } : null)}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
              <PasswordLoginModeSetting
                value={settings?.['password_login.mode']}
                remoteUrl={settings?.['password_login.remote_url']}
                remoteSecretKey={settings?.['password_login.remote_secret_key']}
                onSaved={(mode, remoteUrl, remoteSecretKey) => setSettings((current) => (
                  current
                    ? {
                        ...current,
                        'password_login.mode': mode,
                        'password_login.remote_url': remoteUrl ?? String(current['password_login.remote_url'] || ''),
                        'password_login.remote_secret_key': remoteSecretKey ?? String(current['password_login.remote_secret_key'] || ''),
                      }
                    : current
                ))}
              />
              <SliderModeSetting
                value={settings?.['captcha.slider_mode']}
                onSaved={(mode) => setSettings((current) => (
                  current ? { ...current, 'captcha.slider_mode': mode } : current
                ))}
              />
              <div className="flex items-center justify-between gap-4 py-3 border-t border-slate-100 dark:border-slate-700">
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 dark:text-slate-100">滑块验证通知邮箱</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    自动滑动失败需人工操作时发送邮件通知（留空=不通知）
                  </p>
                </div>
                <input
                  type="email"
                  value={String(settings?.['captcha.slider_notify_email'] || '')}
                  onChange={(e) => setSettings(s => s ? { ...s, 'captcha.slider_notify_email': e.target.value } : null)}
                  placeholder="your-email@qq.com"
                  className="input-ios w-56"
                />
              </div>
              <TokenApiModeSetting
                value={settings?.['token.api_mode']}
                remoteUrl={settings?.['token.remote_url']}
                remoteSecretKey={settings?.['token.remote_secret_key']}
                onSaved={(mode, remoteUrl, remoteSecretKey) => setSettings((current) => (
                  current
                    ? {
                        ...current,
                        'token.api_mode': mode,
                        'token.remote_url': remoteUrl ?? String(current['token.remote_url'] || ''),
                        'token.remote_secret_key': remoteSecretKey ?? String(current['token.remote_secret_key'] || ''),
                      }
                    : current
                ))}
              />
              <div className="flex items-center justify-between py-3 border-t border-slate-100 dark:border-slate-700">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Token过期通知</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">开启后Token正常过期也会发送通知（默认关闭）</p>
                </div>
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={String(settings?.['notify.token_expiry_notify'] || 'false') === 'true'}
                    onChange={(e) => setSettings(s => s ? { ...s, 'notify.token_expiry_notify': e.target.checked ? 'true' : 'false' } : null)}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
            </div>
          </div>
          {/* SMTP邮件配置 */}
          <div className="vben-card">
            <div className="vben-card-header">
              <h2 className="vben-card-title">
                <Mail className="w-4 h-4" />
                SMTP邮件配置
              </h2>
            </div>
            <div className="vben-card-body space-y-4">
              <p className="text-sm text-slate-500 dark:text-slate-400">配置SMTP服务器用于发送注册验证码等邮件通知</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">SMTP服务器</label>
                  <input
                    type="text"
                    value={settings?.smtp_server || ''}
                    onChange={(e) => setSettings(s => s ? { ...s, smtp_server: e.target.value } : null)}
                    placeholder="smtp.qq.com"
                    className="input-ios"
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">SMTP端口</label>
                  <input
                    type="number"
                    value={settings?.smtp_port || 587}
                    onChange={(e) => setSettings(s => s ? { ...s, smtp_port: parseInt(e.target.value) } : null)}
                    placeholder="587"
                    className="input-ios"
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">发件邮箱</label>
                  <input
                    type="email"
                    value={settings?.smtp_user || ''}
                    onChange={(e) => setSettings(s => s ? { ...s, smtp_user: e.target.value } : null)}
                    placeholder="your-email@qq.com"
                    className="input-ios"
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">邮箱密码/授权码</label>
                  <div className="relative">
                    <input
                      type={showSmtpPassword ? 'text' : 'password'}
                      value={settings?.smtp_password || ''}
                      onChange={(e) => setSettings(s => s ? { ...s, smtp_password: e.target.value } : null)}
                      placeholder="输入密码或授权码"
                      className="input-ios pr-20"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                        className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                        title={showSmtpPassword ? '隐藏' : '显示'}
                      >
                        {showSmtpPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          // 先校验是否有内容可复制，避免误操作
                          if (!settings?.smtp_password) {
                            addToast({ type: 'warning', message: '密码为空，无内容可复制' })
                            return
                          }
                          // 使用 copyToClipboard 工具：自动 fallback execCommand，
                          // 兼容 HTTP 部署（非 secure context）以及 navigator.clipboard 不可用的场景。
                          // 旧实现直接 navigator.clipboard.writeText 且未捕获 Promise，
                          // 在 HTTP 环境下会静默失败但 toast 仍显示成功，误导用户。
                          const ok = await copyToClipboard(settings.smtp_password)
                          if (ok) {
                            addToast({ type: 'success', message: '已复制到剪贴板' })
                          } else {
                            addToast({ type: 'error', message: '复制失败，请手动选择文本复制' })
                          }
                        }}
                        className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                        title="复制"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">发件人显示名（可选）</label>
                  <input
                    type="text"
                    value={settings?.smtp_from || ''}
                    onChange={(e) => setSettings(s => s ? { ...s, smtp_from: e.target.value } : null)}
                    placeholder="闲鱼自动回复系统"
                    className="input-ios"
                  />
                </div>
              </div>
              <p className="text-xs text-slate-400">端口说明：25-无加密，465-SSL，587-TLS（推荐）</p>
              <button onClick={() => setShowTestEmailModal(true)} className="btn-ios-secondary">
                发送测试邮件
              </button>
            </div>
          </div>

          {/* 群二维码管理 */}
          <div className="vben-card lg:col-span-2">
            <div className="vben-card-header">
              <h2 className="vben-card-title">
                <MessageCircle className="w-4 h-4" />
                群二维码管理
              </h2>
            </div>
            <div className="vben-card-body">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">上传的二维码将显示在"关于"页面</p>
              <div className="grid grid-cols-5 gap-4">
                {/* 微信群 */}
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center justify-center gap-1">
                    <MessageCircle className="w-4 h-4 text-green-500" />
                    微信群
                  </p>
                  <div className="w-24 h-24 mx-auto mb-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800">
                    {wechatQrcode ? (
                      <img src={wechatQrcode} alt="微信群" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">未上传</div>
                    )}
                  </div>
                  <input
                    ref={wechatFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadWechatQrcode}
                    className="hidden"
                  />
                  <button
                    onClick={() => wechatFileRef.current?.click()}
                    disabled={uploadingWechat}
                    className="btn-ios-secondary btn-sm"
                  >
                    {uploadingWechat ? <ButtonLoading /> : <Upload className="w-3 h-3" />}
                    上传
                  </button>
                </div>
                {/* QQ群 */}
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center justify-center gap-1">
                    <Users className="w-4 h-4 text-blue-500" />
                    QQ群
                  </p>
                  <div className="w-24 h-24 mx-auto mb-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800">
                    {qqQrcode ? (
                      <img src={qqQrcode} alt="QQ群" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">未上传</div>
                    )}
                  </div>
                  <input
                    ref={qqFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadQqQrcode}
                    className="hidden"
                  />
                  <button
                    onClick={() => qqFileRef.current?.click()}
                    disabled={uploadingQq}
                    className="btn-ios-secondary btn-sm"
                  >
                    {uploadingQq ? <ButtonLoading /> : <Upload className="w-3 h-3" />}
                    上传
                  </button>
                </div>
                {/* 微信公众号 */}
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center justify-center gap-1">
                    <MessageCircle className="w-4 h-4 text-green-600" />
                    公众号
                  </p>
                  <div className="w-24 h-24 mx-auto mb-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800">
                    {wechatOfficialQrcode ? (
                      <img src={wechatOfficialQrcode} alt="微信公众号" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">未上传</div>
                    )}
                  </div>
                  <input
                    ref={wechatOfficialFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadWechatOfficialQrcode}
                    className="hidden"
                  />
                  <button
                    onClick={() => wechatOfficialFileRef.current?.click()}
                    disabled={uploadingWechatOfficial}
                    className="btn-ios-secondary btn-sm"
                  >
                    {uploadingWechatOfficial ? <ButtonLoading /> : <Upload className="w-3 h-3" />}
                    上传
                  </button>
                </div>
                {/* TG */}
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center justify-center gap-1">
                    <MessageCircle className="w-4 h-4 text-blue-400" />
                    Telegram
                  </p>
                  <div className="w-24 h-24 mx-auto mb-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800">
                    {telegramQrcode ? (
                      <img src={telegramQrcode} alt="Telegram" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">未上传</div>
                    )}
                  </div>
                  <input
                    ref={telegramFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadTelegramQrcode}
                    className="hidden"
                  />
                  <button
                    onClick={() => telegramFileRef.current?.click()}
                    disabled={uploadingTelegram}
                    className="btn-ios-secondary btn-sm"
                  >
                    {uploadingTelegram ? <ButtonLoading /> : <Upload className="w-3 h-3" />}
                    上传
                  </button>
                </div>
                {/* 赞赏码 */}
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center justify-center gap-1">
                    <Heart className="w-4 h-4 text-red-500" />
                    赞赏码
                  </p>
                  <div className="w-24 h-24 mx-auto mb-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800">
                    {rewardQrcode ? (
                      <img src={rewardQrcode} alt="赞赏码" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">未上传</div>
                    )}
                  </div>
                  <input
                    ref={rewardFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadRewardQrcode}
                    className="hidden"
                  />
                  <button
                    onClick={() => rewardFileRef.current?.click()}
                    disabled={uploadingReward}
                    className="btn-ios-secondary btn-sm"
                  >
                    {uploadingReward ? <ButtonLoading /> : <Upload className="w-3 h-3" />}
                    上传
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {user?.is_admin && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <ThemeAppearanceSettingsCard
            settings={themeAppearanceSettings}
            saving={themeAppearanceSaving}
            onChange={handleThemeAppearanceChange}
            onSave={handleThemeAppearanceSave}
          />
          <ThemeFontSettingsCard
            settings={themeFontSettings}
            saving={themeFontSaving}
            onChange={handleThemeFontChange}
            onSave={handleThemeFontSave}
          />
        </div>
      )}

      {user?.is_admin && (
        <LoginBrandingSettingsCard
          settings={loginBrandingSettings}
          saving={loginBrandingSaving}
          onChange={handleLoginBrandingChange}
          onSave={handleLoginBrandingSave}
        />
      )}

      {user?.is_admin && (
        <AuthFooterAdSettingsCard
          settings={authFooterAdSettings}
          saving={authFooterAdSaving}
          onChange={handleAuthFooterAdChange}
          onSave={handleAuthFooterAdSave}
        />
      )}

      {user?.is_admin && (
        <DisclaimerSettingsCard
          settings={disclaimerSettings}
          saving={disclaimerSaving}
          onChange={handleDisclaimerChange}
          onSave={handleDisclaimerSave}
        />
      )}
        <div><h1 className="page-title">系统设置</h1><p className="page-description">配置系统全局设置</p></div>
        <button type="button" onClick={() => void loadSettings()} className="btn-ios-secondary"><RefreshCw className="h-4 w-4" />刷新</button>
      </div>

      <SystemSettingsTabs activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'basic' && <BasicSettingsTab
        settings={settings}
        setSettings={setSettings}
        isExeMode={isExeMode}
        basicSaving={actions.saving('basic')}
        hiddenMenuSaving={actions.saving('menus')}
        onBasicSave={() => void actions.saveBasic()}
        onHiddenMenusChange={(keys) => setSettings((current) => current ? { ...current, ...buildHiddenMenuSettingsPayload(keys) } : null)}
        onHiddenMenusSave={() => void actions.saveHiddenMenus()}
      />}

      {activeTab === 'contact' && <ContactSettingsTab
        settings={settings}
        setSettings={setSettings}
        smtpSaving={actions.saving('smtp')}
        qrcodeUrls={qrcodes.urls}
        qrcodeUploading={qrcodes.uploading}
        onSmtpSave={() => void actions.saveSmtp()}
        onOpenTestEmail={() => setShowTestEmailModal(true)}
        onUploadQrcode={(type, file) => void qrcodes.upload(type, file)}
      />}

      {activeTab === 'appearance' && <AppearanceSettingsTab
        themeAppearanceSettings={themeAppearance}
        themeFontSettings={themeFont}
        loginBrandingSettings={loginBranding}
        authFooterAdSettings={authFooterAd}
        disclaimerSettings={disclaimer}
        themeAppearanceSaving={actions.saving('themeAppearance')}
        themeFontSaving={actions.saving('themeFont')}
        loginBrandingSaving={actions.saving('branding')}
        authFooterAdSaving={actions.saving('footerAd')}
        disclaimerSaving={actions.saving('disclaimer')}
        onThemeAppearanceChange={handleThemeAppearanceChange}
        onThemeAppearanceSave={() => void actions.saveThemeAppearance(themeAppearance)}
        onThemeFontChange={handleThemeFontChange}
        onThemeFontSave={() => void actions.saveThemeFont(themeFont)}
        onLoginBrandingChange={(key: keyof LoginBrandingSettings, value: string) => setSettings((current) => ({ ...(current ?? {}), [key]: value }))}
        onLoginBrandingSave={() => void actions.saveLoginBranding(loginBranding)}
        onAuthFooterAdChange={(key: keyof AuthFooterAdSettings, value: string) => setSettings((current) => ({ ...(current ?? {}), [key]: value }))}
        onAuthFooterAdSave={() => void actions.saveAuthFooterAd(authFooterAd)}
        onDisclaimerChange={(key: keyof DisclaimerSettings, value: string) => setSettings((current) => ({ ...(current ?? {}), [key]: value }))}
        onDisclaimerSave={() => void actions.saveDisclaimer(disclaimer)}
      />}

      {activeTab === 'payment' && <PaymentSettingsTab
        settings={settings}
        setSettings={setSettings}
        paymentSaving={actions.saving('payment')}
        adPriceSaving={actions.saving('adPrice')}
        withdrawSaving={actions.saving('withdraw')}
        distributionSaving={actions.saving('distribution')}
        onPaymentSave={() => void actions.savePayment()}
        onAdPriceSave={(payload) => void actions.saveAdPrices(payload)}
        onWithdrawSave={() => void actions.saveWithdraw()}
        onDistributionSave={() => void actions.saveDistribution()}
      />}

      {activeTab === 'user' && <UserNetworkSettingsTab
        settings={settings}
        setSettings={setSettings}
        userExpirySaving={actions.saving('expiry')}
        proxySaving={actions.saving('proxy')}
        onUserExpirySave={() => void actions.saveUserExpiry()}
        onProxySave={() => void actions.saveProxy()}
      />}

      {activeTab === 'runtime' && <ServiceRestartCard />}

      {showTestEmailModal && <TestEmailModal email={testEmail} sending={sendingTestEmail} onChange={setTestEmail} onClose={() => { setShowTestEmailModal(false); setTestEmail('') }} onSend={() => void handleTestEmail()} />}
    </div>
  )
}
