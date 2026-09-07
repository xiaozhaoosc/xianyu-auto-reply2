/**
 * 线索池 - 高意向评论流页面（核心页面）
 *
 * 功能：
 * 1. 分页查看线索评论，按意向层级（strong/medium/weak）与处理状态筛选
 * 2. 人工动作：打开商品页 / 复制建议话术 / 标记跟进 / 忽略
 *    - followed 为终态，同一评论只允许跟进一次（后端强校验）
 *    - 系统不提供任何自动发送通道，话术由人工复制后自行判断使用
 */
import { useEffect, useState } from 'react'
import { ArrowUpRight, Check, Copy, ExternalLink, Loader2, RefreshCw, Search, X } from 'lucide-react'
import {
  COMMENT_STATUS_BADGE,
  COMMENT_STATUS_LABELS,
  getLeadCommentSuggestions,
  getLeadComments,
  INTENT_LEVEL_BADGE,
  INTENT_LEVEL_LABELS,
  recordLeadCommentAction,
  type LeadComment,
} from '@/api/leadCapture'
import { PageLoading } from '@/components/common/Loading'
import { useUIStore } from '@/store/uiStore'
import { copyToClipboard } from '@/utils/clipboard'
import { getApiErrorMessage } from '@/utils/apiError'

export function LeadComments() {
  const { addToast } = useUIStore()

  const [loading, setLoading] = useState(true)
  const [comments, setComments] = useState<LeadComment[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [intentFilter, setIntentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [keyword, setKeyword] = useState('')
  const [actingId, setActingId] = useState<number | null>(null)

  // 建议话术弹层
  const [suggestFor, setSuggestFor] = useState<LeadComment | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [suggestLoading, setSuggestLoading] = useState(false)

  const loadComments = async (nextPage = page) => {
    try {
      setLoading(true)
      const result = await getLeadComments(nextPage, pageSize, {
        intentLevel: intentFilter || undefined,
        status: statusFilter || undefined,
        keyword: keyword || undefined,
      })
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '加载评论失败' })
        return
      }
      setComments(result.data.list)
      setTotal(result.data.total)
      setPage(nextPage)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载评论失败') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadComments(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const doAction = async (comment: LeadComment, actionType: 'opened' | 'ignored' | 'followed', extra?: { suggestedReply?: string }) => {
    try {
      setActingId(comment.id)
      const result = await recordLeadCommentAction(comment.id, {
        action_type: actionType,
        suggested_reply: extra?.suggestedReply ?? null,
      })
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '操作失败' })
        return
      }
      if (actionType === 'followed') {
        addToast({ type: 'success', message: '已标记人工跟进（该评论为终态，不可重复跟进）' })
      }
      loadComments(page)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '操作失败') })
    } finally {
      setActingId(null)
    }
  }

  const openItem = async (comment: LeadComment) => {
    const url = comment.item?.item_url || (comment.item ? `https://www.goofish.com/item?id=${comment.item.item_id}` : null)
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
      await doAction(comment, 'opened')
    }
  }

  const openSuggestions = async (comment: LeadComment) => {
    setSuggestFor(comment)
    setSuggestions([])
    setSuggestLoading(true)
    try {
      const result = await getLeadCommentSuggestions(comment.id)
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '生成话术失败' })
        return
      }
      setSuggestions(result.data.suggestions || [])
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '生成话术失败') })
    } finally {
      setSuggestLoading(false)
    }
  }

  const copySuggestion = async (comment: LeadComment, text: string) => {
    const ok = await copyToClipboard(text)
    if (ok) {
      addToast({ type: 'success', message: '已复制（请自行判断修改后使用，系统不自动发送）' })
      await recordLeadCommentAction(comment.id, { action_type: 'copied', suggested_reply: text })
      loadComments(page)
    } else {
      addToast({ type: 'error', message: '复制失败，请手动选择文本复制' })
    }
  }

  if (loading && comments.length === 0) {
    return <PageLoading />
  }

  return (
    <div className="p-4 lg:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">高意向评论流</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          系统只负责发现与整理，是否留言、怎么留言由人工判断；同一评论仅可跟进一次
        </p>
      </div>

      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg bg-gray-100 p-0.5 dark:bg-gray-800">
          {[
            { value: '', label: '全部' },
            { value: 'strong', label: '强意向' },
            { value: 'medium', label: '中意向' },
            { value: 'weak', label: '弱意向' },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setIntentFilter(opt.value)}
              className={`rounded-md px-3 py-1.5 text-xs ${
                intentFilter === opt.value ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
        >
          <option value="">全部状态</option>
          {Object.entries(COMMENT_STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadComments(1)}
            placeholder="搜索评论内容"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          />
        </div>
        <button
          onClick={() => loadComments(1)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm text-gray-700 ring-1 ring-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700"
        >
          <RefreshCw className="h-4 w-4" />
          查询
        </button>
      </div>

      {/* 评论卡片列表 */}
      {comments.length === 0 ? (
        <div className="rounded-xl bg-white py-12 text-center text-sm text-gray-400 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
          暂无线索评论，等待采集任务扫描入库
        </div>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${INTENT_LEVEL_BADGE[comment.intent_level] || INTENT_LEVEL_BADGE.weak}`}>
                      {INTENT_LEVEL_LABELS[comment.intent_level] || comment.intent_level}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${COMMENT_STATUS_BADGE[comment.status] || ''}`}>
                      {COMMENT_STATUS_LABELS[comment.status] || comment.status}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">{comment.commenter_name || '匿名用户'}</span>
                    <span className="text-xs text-gray-400">
                      {comment.comment_time ? new Date(comment.comment_time).toLocaleString() : comment.created_at ? new Date(comment.created_at).toLocaleString() : ''}
                    </span>
                    {comment.intent_keywords.length > 0 && (
                      <span className="text-xs text-gray-400">命中：{comment.intent_keywords.join('、')}</span>
                    )}
                  </div>
                  <p className="mt-2 break-words text-sm text-gray-900 dark:text-gray-100">{comment.content}</p>
                  {comment.item && (
                    <p className="mt-2 truncate text-xs text-gray-500 dark:text-gray-400">
                      商品「{comment.item.title || comment.item.item_id}」
                      {comment.item.price ? ` · ${comment.item.price}` : ''}
                      {comment.item.seller_nick ? ` · 卖家 ${comment.item.seller_nick}` : ''}
                    </p>
                  )}
                </div>
                {/* 操作区：仅 4 个只读/低敏动作 */}
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    onClick={() => openItem(comment)}
                    disabled={!comment.item}
                    title="打开商品页"
                    className="rounded p-1.5 text-blue-600 hover:bg-blue-50 disabled:opacity-30 dark:hover:bg-blue-900/30"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => openSuggestions(comment)}
                    title="查看建议话术"
                    className="rounded p-1.5 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/30"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => doAction(comment, 'followed')}
                    disabled={actingId === comment.id || comment.status === 'followed'}
                    title={comment.status === 'followed' ? '已跟进（终态）' : '标记已人工跟进'}
                    className="rounded p-1.5 text-green-600 hover:bg-green-50 disabled:opacity-30 dark:hover:bg-green-900/30"
                  >
                    {actingId === comment.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  </button>
                  <button
                    onClick={() => doAction(comment, 'ignored')}
                    disabled={actingId === comment.id}
                    title="忽略"
                    className="rounded p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>共 {total} 条</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadComments(page - 1)}
              disabled={page <= 1}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => loadComments(page + 1)}
              disabled={page >= totalPages}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 建议话术弹层 */}
      {suggestFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-5 shadow-xl dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">建议跟进话术（人工参考）</h3>
              <button onClick={() => setSuggestFor(null)} className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              话术仅为模板参考，请自行判断与修改；系统不提供自动发送通道
            </p>
            <div className="mt-3 space-y-2">
              {suggestLoading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : suggestions.length === 0 ? (
                <p className="py-4 text-center text-sm text-gray-400">暂无话术</p>
              ) : (
                suggestions.map((text, idx) => (
                  <div
                    key={idx}
                    className="group flex items-start justify-between gap-2 rounded-lg bg-gray-50 p-3 text-sm text-gray-700 dark:bg-gray-900/50 dark:text-gray-200"
                  >
                    <span className="break-all">{text}</span>
                    <button
                      onClick={() => copySuggestion(suggestFor, text)}
                      className="shrink-0 rounded p-1 text-blue-600 opacity-60 hover:opacity-100"
                      title="复制"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setSuggestFor(null)}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50 dark:text-gray-300 dark:ring-gray-700"
              >
                关闭
              </button>
              <button
                onClick={() => {
                  doAction(suggestFor, 'followed')
                  setSuggestFor(null)
                }}
                disabled={suggestFor.status === 'followed'}
                className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-40"
              >
                <ArrowUpRight className="h-4 w-4" />
                标记已跟进
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
