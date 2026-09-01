/**
 * 多账号商品同步页面
 *
 * 功能：把源账号的商品通过「素材库中转」批量发布到多个目标账号。
 * 流程：源账号商品列表（闲鱼API）→ 标题关键词/价格区间筛选 → 转素材（按标题去重）
 *       → PublishExecutorService.batch_publish 批量发布。
 * 注意：同步 = 真实发布动作，命中风控关键词后端会拒绝；量大请分批。
 */
import { useState, useEffect, useMemo } from 'react'
import { ArrowLeftRight, Send, AlertTriangle, CheckSquare, Square, RefreshCw } from 'lucide-react'
import { syncAccounts, type AccountSyncResult } from '@/api/accountSync'
import { getAccountDetails } from '@/api/accounts'
import { useUIStore } from '@/store/uiStore'
import { ConfirmModal } from '@/components/common/ConfirmModal'

export function AccountSync() {
  const { addToast } = useUIStore()

  const [accounts, setAccounts] = useState<{ id: string; note?: string; enabled: boolean }[]>([])
  const [sourceAccountId, setSourceAccountId] = useState('')
  const [targetAccountIds, setTargetAccountIds] = useState<Set<string>>(new Set())
  const [keyword, setKeyword] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<{ message: string; data?: AccountSyncResult } | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)

  const loadAccounts = async () => {
    try {
      const list = await getAccountDetails()
      setAccounts(list.filter((a) => a.enabled))
    } catch {
      addToast({ type: 'error', message: '获取账号列表失败' })
    }
  }

  useEffect(() => {
    loadAccounts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 目标账号候选 = 排除源账号
  const targetCandidates = useMemo(
    () => accounts.filter((a) => a.id !== sourceAccountId),
    [accounts, sourceAccountId],
  )

  const toggleTarget = (id: string) => {
    setTargetAccountIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAllTargets = () => {
    if (targetAccountIds.size === targetCandidates.length) {
      setTargetAccountIds(new Set())
    } else {
      setTargetAccountIds(new Set(targetCandidates.map((a) => a.id)))
    }
  }

  const canSubmit =
    !!sourceAccountId && targetAccountIds.size > 0 && !syncing

  const doSync = async () => {
    setShowConfirm(false)
    setSyncing(true)
    setResult(null)
    try {
      const resp = await syncAccounts({
        source_account_id: sourceAccountId,
        target_account_ids: Array.from(targetAccountIds),
        keyword_filter: keyword.trim() || undefined,
        min_price: minPrice.trim() ? Number(minPrice) : undefined,
        max_price: maxPrice.trim() ? Number(maxPrice) : undefined,
        sync_mode: 'material',
      })
      if (resp.success) {
        addToast({ type: 'success', message: resp.message || '同步完成' })
        setResult({ message: resp.message, data: resp.data })
      } else {
        addToast({ type: 'error', message: resp.message || '同步失败' })
        setResult({ message: resp.message })
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '同步请求失败'
      addToast({ type: 'error', message: msg })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="page-header flex-between flex-wrap gap-4">
        <div>
          <h1 className="page-title">账号商品同步</h1>
          <p className="page-description">把源账号的商品经素材库中转，批量发布到多个目标账号</p>
        </div>
        <button type="button" className="btn-ios-secondary" onClick={loadAccounts}>
          <RefreshCw className="w-4 h-4 mr-1 inline" /> 刷新账号
        </button>
      </div>

      {/* 同步配置 */}
      <div className="vben-card">
        <div className="vben-card-body space-y-5">
          {/* 源账号 */}
          <div className="input-group">
            <label className="input-label">源账号（从它拉取商品列表）</label>
            <select
              className="input-ios"
              value={sourceAccountId}
              onChange={(e) => {
                setSourceAccountId(e.target.value)
                setTargetAccountIds(new Set())
              }}
            >
              <option value="">请选择源账号</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.note ? `${a.note}（${a.id}）` : a.id}
                </option>
              ))}
            </select>
          </div>

          {/* 目标账号（多选） */}
          <div className="input-group">
            <div className="flex items-center justify-between">
              <label className="input-label">目标账号（可多选，已排除源账号）</label>
              {targetCandidates.length > 0 && (
                <button
                  type="button"
                  className="text-sm text-blue-500 hover:underline"
                  onClick={toggleAllTargets}
                >
                  {targetAccountIds.size === targetCandidates.length ? '取消全选' : '全选'}
                </button>
              )}
            </div>
            {targetCandidates.length === 0 ? (
              <p className="text-sm text-gray-400 py-2">请先选择源账号</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {targetCandidates.map((a) => {
                  const checked = targetAccountIds.has(a.id)
                  return (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => toggleTarget(a.id)}
                      className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-colors ${
                        checked
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
                      }`}
                    >
                      {checked ? (
                        <CheckSquare className="w-4 h-4 text-blue-500 shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-gray-400 shrink-0" />
                      )}
                      <span className="text-sm truncate">
                        {a.note ? `${a.note}（${a.id}）` : a.id}
                      </span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* 筛选条件 */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="input-group">
              <label className="input-label">标题关键词（可选）</label>
              <input
                className="input-ios"
                placeholder="包含该关键词才同步"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label">最低价（可选）</label>
              <input
                className="input-ios"
                type="number"
                min="0"
                step="0.01"
                placeholder="不限"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label">最高价（可选）</label>
              <input
                className="input-ios"
                type="number"
                min="0"
                step="0.01"
                placeholder="不限"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
              />
            </div>
          </div>

          {/* 风控提示 */}
          <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 text-sm">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>
              同步 = 真实批量发布：源商品会先去重转换为素材，再逐个发布到目标账号。
              命中风控关键词（滑块/验证）会立即中断。商品多时请分批执行。
            </span>
          </div>

          {/* 提交 */}
          <div>
            <button
              type="button"
              className="btn-ios-primary"
              disabled={!canSubmit}
              onClick={() => setShowConfirm(true)}
            >
              <Send className="w-4 h-4 mr-1 inline" />
              {syncing ? '同步中…' : `开始同步${targetAccountIds.size > 0 ? `（${targetAccountIds.size} 个目标账号）` : ''}`}
            </button>
          </div>
        </div>
      </div>

      {/* 同步结果 */}
      {result && (
        <div className="vben-card">
          <div className="vben-card-body space-y-3">
            <div className="flex items-center gap-2">
              <ArrowLeftRight className="w-4 h-4 text-blue-500" />
              <span className="font-medium">{result.message}</span>
            </div>
            {result.data && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                  <div className="text-gray-400">源商品数</div>
                  <div className="text-lg font-semibold">{result.data.source_items_count}</div>
                </div>
                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                  <div className="text-gray-400">素材数</div>
                  <div className="text-lg font-semibold">{result.data.materials_created}</div>
                </div>
                <div className="p-3 rounded-xl bg-green-50 dark:bg-green-900/20">
                  <div className="text-green-600">发布成功</div>
                  <div className="text-lg font-semibold text-green-600">
                    {result.data.publish_result?.success_count ?? '—'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-red-50 dark:bg-red-900/20">
                  <div className="text-red-500">发布失败</div>
                  <div className="text-lg font-semibold text-red-500">
                    {result.data.publish_result?.failed_count ?? '—'}
                  </div>
                </div>
              </div>
            )}
            {result.data?.batch_id && (
              <p className="text-xs text-gray-400">批次号：{result.data.batch_id}</p>
            )}
          </div>
        </div>
      )}

      <ConfirmModal
        isOpen={showConfirm}
        title="确认开始同步"
        message={`将把源账号 ${sourceAccountId} 的商品${keyword ? `（关键词「${keyword}」）` : ''}同步发布到 ${targetAccountIds.size} 个目标账号。这会真实发布商品，是否继续？`}
        type="warning"
        loading={syncing}
        onConfirm={doSync}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  )
}
