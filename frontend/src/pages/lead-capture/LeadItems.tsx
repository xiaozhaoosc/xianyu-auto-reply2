/**
 * 线索池 - 线索商品页面
 *
 * 功能：
 * 1. 分页查看线索商品池（按需求热度分降序）
 * 2. 行内查看商品下的评论（弹层）
 * 3. 归档/恢复商品（归档后不再扫描）
 */
import { useEffect, useState } from 'react'
import { Archive, ArchiveRestore, ExternalLink, Loader2, RefreshCw, Search, X } from 'lucide-react'
import {
  getLeadItemComments,
  getLeadItems,
  INTENT_LEVEL_BADGE,
  INTENT_LEVEL_LABELS,
  updateLeadItemStatus,
  type LeadComment,
  type LeadItem,
} from '@/api/leadCapture'
import { PageLoading } from '@/components/common/Loading'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'

export function LeadItems() {
  const { addToast } = useUIStore()

  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<LeadItem[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState('active')
  const [keyword, setKeyword] = useState('')
  const [actingId, setActingId] = useState<number | null>(null)

  // 商品评论弹层
  const [viewItem, setViewItem] = useState<LeadItem | null>(null)
  const [itemComments, setItemComments] = useState<LeadComment[]>([])
  const [commentsLoading, setCommentsLoading] = useState(false)

  const loadItems = async (nextPage = page) => {
    try {
      setLoading(true)
      const result = await getLeadItems(nextPage, pageSize, {
        status: statusFilter || undefined,
        keyword: keyword || undefined,
      })
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '加载线索商品失败' })
        return
      }
      setItems(result.data.list)
      setTotal(result.data.total)
      setPage(nextPage)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载线索商品失败') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadItems(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const handleArchive = async (item: LeadItem) => {
    try {
      setActingId(item.id)
      const nextStatus = item.status === 'archived' ? 'active' : 'archived'
      const result = await updateLeadItemStatus(item.id, nextStatus)
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '操作失败' })
        return
      }
      addToast({ type: 'success', message: nextStatus === 'archived' ? '已归档（不再扫描该商品评论区）' : '已恢复观察' })
      loadItems(page)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '操作失败') })
    } finally {
      setActingId(null)
    }
  }

  const openItemComments = async (item: LeadItem) => {
    setViewItem(item)
    setItemComments([])
    setCommentsLoading(true)
    try {
      const result = await getLeadItemComments(item.id, 1, 50)
      if (result.success && result.data) {
        setItemComments(result.data.list)
      } else {
        addToast({ type: 'error', message: result.message || '加载评论失败' })
      }
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载评论失败') })
    } finally {
      setCommentsLoading(false)
    }
  }

  if (loading && items.length === 0) {
    return <PageLoading />
  }

  return (
    <div className="p-4 lg:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">线索商品池</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          需求热度分 = 强意向 × 3 + 中意向 × 1；按分数排序定位「评论区求购密集」的商品
        </p>
      </div>

      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg bg-gray-100 p-0.5 dark:bg-gray-800">
          {[
            { value: 'active', label: '观察中' },
            { value: 'archived', label: '已归档' },
            { value: '', label: '全部' },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`rounded-md px-3 py-1.5 text-xs ${
                statusFilter === opt.value ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadItems(1)}
            placeholder="搜索商品标题"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          />
        </div>
        <button
          onClick={() => loadItems(1)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm text-gray-700 ring-1 ring-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700"
        >
          <RefreshCw className="h-4 w-4" />
          查询
        </button>
      </div>

      {/* 商品表格 */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              {['商品', '价格', '卖家', '强意向', '中意向', '需求分', '最近扫描', '操作'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-sm text-gray-400">
                  暂无线索商品，等待采集任务扫描入库
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="max-w-xs px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      {item.pic_url && (
                        <img src={item.pic_url} alt="" className="h-9 w-9 shrink-0 rounded object-cover" loading="lazy" />
                      )}
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100" title={item.title || ''}>
                          {item.title || item.item_id}
                        </div>
                        <div className="text-xs text-gray-400">ID {item.item_id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{item.price || '-'}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{item.seller_nick || '-'}</td>
                  <td className="px-3 py-2.5">
                    <span className="text-sm font-semibold text-red-600 dark:text-red-400">{item.strong_count}</span>
                  </td>
                  <td className="px-3 py-2.5 text-sm text-amber-600 dark:text-amber-400">{item.medium_count}</td>
                  <td className="px-3 py-2.5">
                    <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
                      {item.demand_score}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-gray-500 dark:text-gray-400">
                    {item.last_comment_scan_at ? new Date(item.last_comment_scan_at).toLocaleString() : '未扫描'}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openItemComments(item)}
                        className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                        title="查看评论"
                      >
                        评论 {item.comment_count}
                      </button>
                      <a
                        href={item.item_url || `https://www.goofish.com/item?id=${item.item_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                        title="打开商品页"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                      <button
                        onClick={() => handleArchive(item)}
                        disabled={actingId === item.id}
                        className="rounded p-1.5 text-gray-500 hover:bg-gray-100 disabled:opacity-40 dark:hover:bg-gray-700"
                        title={item.status === 'archived' ? '恢复观察' : '归档（不再扫描）'}
                      >
                        {actingId === item.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : item.status === 'archived' ? (
                          <ArchiveRestore className="h-4 w-4" />
                        ) : (
                          <Archive className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>共 {total} 条</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadItems(page - 1)}
              disabled={page <= 1}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => loadItems(page + 1)}
              disabled={page >= totalPages}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 商品评论弹层 */}
      {viewItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-gray-800">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-base font-semibold text-gray-900 dark:text-gray-100">{viewItem.title || viewItem.item_id}</h3>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  需求分 {viewItem.demand_score} · 强意向 {viewItem.strong_count} · 中意向 {viewItem.medium_count}
                </p>
              </div>
              <button onClick={() => setViewItem(null)} className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {commentsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : itemComments.length === 0 ? (
                <p className="py-6 text-center text-sm text-gray-400">该商品暂无入库评论</p>
              ) : (
                itemComments.map((comment) => (
                  <div key={comment.id} className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900/50">
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${INTENT_LEVEL_BADGE[comment.intent_level] || ''}`}>
                        {INTENT_LEVEL_LABELS[comment.intent_level] || comment.intent_level}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{comment.commenter_name || '匿名用户'}</span>
                    </div>
                    <p className="mt-1.5 break-words text-sm text-gray-700 dark:text-gray-200">{comment.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
