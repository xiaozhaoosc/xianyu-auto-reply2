/**
 * 线索池 - 总览页面
 *
 * 功能：
 * 1. 展示线索池核心统计（任务数/商品数/评论数/待处理数/今日新增）
 * 2. 近7天评论新增趋势（按意向层级）
 */
import { useEffect, useState } from 'react'
import { Activity, Eye, Loader2, MessageSquare, Package, RefreshCw, ShoppingCart } from 'lucide-react'
import { getLeadOverview, INTENT_LEVEL_LABELS, type LeadOverview } from '@/api/leadCapture'
import { PageLoading } from '@/components/common/Loading'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'

export function LeadOverview() {
  const { addToast } = useUIStore()
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<LeadOverview | null>(null)

  const loadOverview = async () => {
    try {
      setLoading(true)
      const result = await getLeadOverview()
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '加载总览失败' })
        return
      }
      setOverview(result.data)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载总览失败') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOverview()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading && !overview) {
    return <PageLoading />
  }

  const cards = [
    { label: '采集任务', value: overview?.total_tasks ?? 0, sub: `启用中 ${overview?.enabled_tasks ?? 0}`, icon: Activity, cls: 'text-blue-600' },
    { label: '线索商品', value: overview?.total_items ?? 0, sub: `观察中 ${overview?.active_items ?? 0}`, icon: Package, cls: 'text-indigo-600' },
    { label: '线索评论', value: overview?.total_comments ?? 0, sub: `强意向 ${overview?.strong_comments ?? 0}`, icon: MessageSquare, cls: 'text-amber-600' },
    { label: '待处理评论', value: overview?.pending_comments ?? 0, sub: `已跟进 ${overview?.followed_comments ?? 0}`, icon: Eye, cls: 'text-cyan-600' },
    { label: '今日新增', value: overview?.today_new_comments ?? 0, sub: `强意向 ${overview?.today_new_strong ?? 0}`, icon: ShoppingCart, cls: 'text-green-600' },
  ]

  // 趋势条形图数据（纯 div 实现，避免额外图表依赖）
  const trend = overview?.trend ?? []
  const maxTrend = Math.max(1, ...trend.map((d) => d.strong + d.medium + d.weak))

  return (
    <div className="p-4 lg:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">线索池总览</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            只读监控别人商品评论区的高意向需求，服务选品 / 补货 / 定价；触达动作一律人工确认
          </p>
        </div>
        <button
          onClick={loadOverview}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm text-gray-700 shadow-sm ring-1 ring-gray-200 hover:bg-gray-50 disabled:opacity-60 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700 dark:hover:bg-gray-700"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">{card.label}</span>
              <card.icon className={`h-5 w-5 ${card.cls}`} />
            </div>
            <div className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{card.value}</div>
            <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">{card.sub}</div>
          </div>
        ))}
      </div>

      {/* 近7天趋势 */}
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <h2 className="text-sm font-medium text-gray-900 dark:text-gray-100">近7天评论新增趋势</h2>
        {trend.length === 0 ? (
          <p className="mt-4 text-sm text-gray-400 dark:text-gray-500">暂无数据，等待线索采集任务扫描后展示</p>
        ) : (
          <div className="mt-4 space-y-3">
            {trend.map((day) => {
              const total = day.strong + day.medium + day.weak
              return (
                <div key={day.date} className="flex items-center gap-3">
                  <span className="w-20 shrink-0 text-xs text-gray-500 dark:text-gray-400">{day.date}</span>
                  <div className="flex h-6 flex-1 overflow-hidden rounded-md bg-gray-100 dark:bg-gray-700/50" title={`强意向 ${day.strong}，中意向 ${day.medium}，弱意向 ${day.weak}`}>
                    {day.strong > 0 && (
                      <div className="flex items-center justify-center bg-red-400 text-[10px] text-white" style={{ width: `${(day.strong / maxTrend) * 100}%` }}>
                        {day.strong}
                      </div>
                    )}
                    {day.medium > 0 && (
                      <div className="flex items-center justify-center bg-amber-300 text-[10px] text-amber-900" style={{ width: `${(day.medium / maxTrend) * 100}%` }}>
                        {day.medium}
                      </div>
                    )}
                    {day.weak > 0 && (
                      <div className="flex items-center justify-center bg-gray-300 text-[10px] text-gray-700 dark:bg-gray-600 dark:text-gray-200" style={{ width: `${(day.weak / maxTrend) * 100}%` }}>
                        {day.weak}
                      </div>
                    )}
                  </div>
                  <span className="w-10 shrink-0 text-right text-xs text-gray-500 dark:text-gray-400">{total}</span>
                </div>
              )
            })}
            <div className="flex items-center gap-4 pt-1 text-xs text-gray-500 dark:text-gray-400">
              {(['strong', 'medium', 'weak'] as const).map((level) => (
                <span key={level} className="inline-flex items-center gap-1">
                  <span
                    className={`inline-block h-2.5 w-2.5 rounded-sm ${
                      level === 'strong' ? 'bg-red-400' : level === 'medium' ? 'bg-amber-300' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                  {INTENT_LEVEL_LABELS[level]}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
