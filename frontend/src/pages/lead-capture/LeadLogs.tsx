/**
 * 线索池 - 扫描日志页面
 *
 * 功能：
 * 1. 分页查看评论扫描日志（任务/状态筛选）
 * 2. 展示扫描量、入库量、强意向增量、风控触发情况
 */
import { useEffect, useState } from 'react'
import { Loader2, RefreshCw, Search } from 'lucide-react'
import {
  getLeadLogs,
  getLeadTasks,
  SCAN_STATUS_BADGE,
  SCAN_STATUS_LABELS,
  type LeadCaptureTask,
  type LeadScanLog,
} from '@/api/leadCapture'
import { PageLoading } from '@/components/common/Loading'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'

const TRIGGER_LABELS: Record<string, string> = {
  auto: '定时',
  manual: '手动',
}

export function LeadLogs() {
  const { addToast } = useUIStore()

  const [loading, setLoading] = useState(true)
  const [logs, setLogs] = useState<LeadScanLog[]>([])
  const [tasks, setTasks] = useState<LeadCaptureTask[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [taskIdFilter, setTaskIdFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const loadLogs = async (nextPage = page) => {
    try {
      setLoading(true)
      const result = await getLeadLogs(nextPage, pageSize, {
        taskId: taskIdFilter ? Number(taskIdFilter) : undefined,
        status: statusFilter || undefined,
      })
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '加载扫描日志失败' })
        return
      }
      setLogs(result.data.list)
      setTotal(result.data.total)
      setPage(nextPage)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载扫描日志失败') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs(1)
    // 加载任务列表用于筛选下拉
    getLeadTasks(1, 100)
      .then((result) => {
        if (result.success && result.data) setTasks(result.data.list)
      })
      .catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  if (loading && logs.length === 0) {
    return <PageLoading />
  }

  return (
    <div className="p-4 lg:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">扫描日志</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          每轮评论扫描的执行记录；「触发风控终止」代表当轮检测到风控并立即停止后续请求
        </p>
      </div>

      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={taskIdFilter}
          onChange={(e) => setTaskIdFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
        >
          <option value="">全部任务</option>
          {tasks.map((task) => (
            <option key={task.id} value={task.id}>
              #{task.id} {task.name}
            </option>
          ))}
        </select>
        <div className="flex rounded-lg bg-gray-100 p-0.5 dark:bg-gray-800">
          {[
            { value: '', label: '全部' },
            { value: 'success', label: '成功' },
            { value: 'partial', label: '部分成功' },
            { value: 'failed', label: '失败' },
            { value: 'risk_stopped', label: '风控终止' },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`rounded-md px-3 py-1.5 text-xs ${
                statusFilter === opt.value
                  ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => loadLogs(1)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm text-gray-700 ring-1 ring-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          查询
        </button>
      </div>

      {/* 日志表格 */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              {['时间', '任务', '触发方式', '账号', '扫描商品', '抓取评论', '新入库', '强意向', '状态', '说明'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-3 py-8 text-center text-sm text-gray-400">
                  暂无扫描日志
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="whitespace-nowrap px-3 py-2.5 text-xs text-gray-500 dark:text-gray-400">
                    {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="max-w-[160px] px-3 py-2.5">
                    <div className="truncate text-sm text-gray-900 dark:text-gray-100" title={log.task_name || ''}>
                      {log.task_name || `任务 #${log.task_id}`}
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-gray-500 dark:text-gray-400">
                    {TRIGGER_LABELS[log.trigger_type] || log.trigger_type}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-gray-500 dark:text-gray-400">{log.account_id || '-'}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{log.scanned_count}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{log.comment_fetched}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{log.comment_new}</td>
                  <td className="px-3 py-2.5">
                    {log.strong_new > 0 ? (
                      <span className="text-sm font-semibold text-red-600 dark:text-red-400">{log.strong_new}</span>
                    ) : (
                      <span className="text-sm text-gray-400">0</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${SCAN_STATUS_BADGE[log.status] || ''}`}>
                      {SCAN_STATUS_LABELS[log.status] || log.status}
                    </span>
                    {log.risk_triggered && (
                      <span className="ml-1 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-400">
                        风控
                      </span>
                    )}
                  </td>
                  <td className="max-w-[220px] px-3 py-2.5">
                    <div className="truncate text-xs text-gray-500 dark:text-gray-400" title={log.message || ''}>
                      {log.message || '-'}
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
              onClick={() => loadLogs(page - 1)}
              disabled={page <= 1}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => loadLogs(page + 1)}
              disabled={page >= totalPages}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {logs.length === 0 && !loading && (
        <div className="flex items-center justify-center gap-2 py-4 text-sm text-gray-400">
          <Search className="h-4 w-4" />
          调整筛选条件后点击「查询」重新加载
        </div>
      )}
    </div>
  )
}
