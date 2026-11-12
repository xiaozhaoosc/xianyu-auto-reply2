/**
 * 线索池 - Phase 0 探针页面（仅人工验证用）
 *
 * 功能：
 * 1. 选一个账号 + 输入一个商品 ID，读取该商品评论区
 * 2. 查看返回的评论样例与原始字段，用于确认 fetch_comments 接口可用性
 * 3. 带分布式锁（60s），不允许频繁调用
 *
 * 注意：探针仅用于人工验证评论读取链路，不写库、不做任何互动。
 */
import { useEffect, useState } from 'react'
import { AlertTriangle, Loader2, Play } from 'lucide-react'
import { getAccountDetails } from '@/api/accounts'
import { runLeadProbe, type LeadProbeResult } from '@/api/leadCapture'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'

export function LeadProbe() {
  const { addToast } = useUIStore()

  const [accounts, setAccounts] = useState<Array<{ id: string; note?: string; enabled: boolean }>>([])
  const [accountId, setAccountId] = useState('')
  const [itemId, setItemId] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<LeadProbeResult | null>(null)

  useEffect(() => {
    getAccountDetails()
      .then((list) => {
        const enabled = list.filter((account) => account.enabled)
        setAccounts(enabled)
        if (enabled.length > 0) setAccountId(enabled[0].id)
      })
      .catch((error) => addToast({ type: 'error', message: getApiErrorMessage(error, '加载账号失败') }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleRun = async () => {
    const trimmedItem = itemId.trim()
    if (!trimmedItem) {
      addToast({ type: 'warning', message: '请输入商品 ID' })
      return
    }
    if (!accountId) {
      addToast({ type: 'warning', message: '请选择账号' })
      return
    }
    try {
      setRunning(true)
      setResult(null)
      const response = await runLeadProbe(trimmedItem, accountId)
      if (!response.success || !response.data) {
        addToast({ type: 'error', message: response.message || '探针执行失败' })
        return
      }
      setResult(response.data)
      if (response.data.success) {
        addToast({ type: 'success', message: `读取成功，共 ${response.data.comment_count} 条评论` })
      } else {
        addToast({ type: 'error', message: response.data.error || '读取失败' })
      }
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '探针执行失败') })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="p-4 lg:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">评论读取探针</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Phase 0 人工验证工具：单商品读取一次评论区，不写库、不互动；60 秒内仅允许调用一次
        </p>
      </div>

      {/* 输入区 */}
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-56">
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">读取账号</label>
            <select
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            >
              {accounts.length === 0 && <option value="">暂无可用账号</option>}
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.note || account.id}
                </option>
              ))}
            </select>
          </div>
          <div className="min-w-[240px] flex-1">
            <label className="mb-1 block text-xs text-gray-500 dark:text-gray-400">商品 ID</label>
            <input
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRun()}
              placeholder="例如 952741369512"
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            />
          </div>
          <button
            onClick={handleRun}
            disabled={running || !accountId || !itemId.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            执行探针
          </button>
        </div>
      </div>

      {/* 结果区 */}
      {result && (
        <div className="space-y-3">
          {/* 摘要 */}
          <div
            className={`rounded-xl p-4 ring-1 ${
              result.success
                ? 'bg-green-50 ring-green-200 dark:bg-green-900/20 dark:ring-green-800'
                : 'bg-red-50 ring-red-200 dark:bg-red-900/20 dark:ring-red-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {result.success ? (
                <span className="text-sm font-medium text-green-700 dark:text-green-400">读取成功</span>
              ) : (
                <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
              )}
              {!result.success && (
                <span className="text-sm font-medium text-red-700 dark:text-red-400">读取失败</span>
              )}
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300 sm:grid-cols-4">
              <div>评论数：{result.comment_count}</div>
              <div>原始 total：{result.total}</div>
              <div>风控触发：{result.risk_triggered ? '是' : '否'}</div>
              <div>商品失效：{result.item_invalid ? '是' : '否'}</div>
            </div>
            {result.error && (
              <p className="mt-2 break-all rounded bg-white/60 p-2 font-mono text-xs text-red-600 dark:bg-black/20 dark:text-red-400">
                {result.error}
              </p>
            )}
            {result.risk_triggered && result.punish_url && (
              <p className="mt-2 break-all text-xs text-red-600 dark:text-red-400">风控地址：{result.punish_url}</p>
            )}
          </div>

          {/* 评论样例 */}
          {result.sample_comments.length > 0 && (
            <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">评论样例（最多 10 条）</h3>
              <div className="mt-3 space-y-2">
                {result.sample_comments.map((comment, index) => (
                  <div key={index} className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900/50">
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>{comment.commenter_name || '匿名用户'}</span>
                      {comment.comment_time && <span>· {comment.comment_time}</span>}
                    </div>
                    <p className="mt-1 break-words text-sm text-gray-700 dark:text-gray-200">{comment.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 原始字段 */}
          {result.raw_keys.length > 0 && (
            <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">响应原始字段（用于核对字段映射）</h3>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {result.raw_keys.map((key) => (
                  <span
                    key={key}
                    className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-600 dark:bg-gray-900/60 dark:text-gray-400"
                  >
                    {key}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 空状态提示 */}
      {!result && !running && (
        <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400 dark:border-gray-700">
          输入商品 ID 后点击「执行探针」，验证评论读取接口是否可用
        </div>
      )}
    </div>
  )
}
