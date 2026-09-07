/**
 * 线索池 - 采集任务页面
 *
 * 功能：
 * 1. 分页查看 / 启停 / 删除线索采集任务
 * 2. 创建 / 编辑任务（间隔最低30分钟、每轮最多10商品，风控下限提示）
 * 3. 手动触发单任务扫描（调 scheduler internal，忽略间隔执行一次）
 */
import { useEffect, useState } from 'react'
import { Loader2, Pencil, Plus, RefreshCw, Search, Trash2, Zap } from 'lucide-react'
import {
  createLeadTask,
  deleteLeadTask,
  getLeadTasks,
  runLeadTask,
  updateLeadTask,
  updateLeadTaskStatus,
  type LeadCaptureTask,
  type LeadTaskPayload,
} from '@/api/leadCapture'
import { getAccountDetails } from '@/api/accounts'
import { getListingMonitorTaskOptions } from '@/api/listingMonitor'
import { PageLoading } from '@/components/common/Loading'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/apiError'

interface MonitorTaskOption {
  id: number
  keyword?: string | null
}

const emptyForm: LeadTaskPayload = {
  name: '',
  source_type: 'monitor',
  keyword: '',
  monitor_task_id: null,
  price_min: null,
  price_max: null,
  interval_minutes: 60,
  max_items_per_round: 5,
  include_weak: false,
  account_ids: [],
  rescan_cooldown_hours: 24,
  is_enabled: true,
  remark: '',
}

export function LeadTasks() {
  const { addToast } = useUIStore()

  const [loading, setLoading] = useState(true)
  const [tasks, setTasks] = useState<LeadCaptureTask[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')

  // 账号与监控任务选项
  const [accountOptions, setAccountOptions] = useState<Array<{ id: string; note?: string; enabled: boolean }>>([])
  const [monitorTasks, setMonitorTasks] = useState<MonitorTaskOption[]>([])

  // 创建/编辑弹层
  const [showModal, setShowModal] = useState(false)
  const [editingTask, setEditingTask] = useState<LeadCaptureTask | null>(null)
  const [form, setForm] = useState<LeadTaskPayload>({ ...emptyForm })
  const [saving, setSaving] = useState(false)
  const [runningId, setRunningId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const loadTasks = async (nextPage = page) => {
    try {
      setLoading(true)
      const result = await getLeadTasks(nextPage, pageSize, { keyword: keyword || undefined })
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '加载任务失败' })
        return
      }
      setTasks(result.data.list)
      setTotal(result.data.total)
      setPage(nextPage)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '加载任务失败') })
    } finally {
      setLoading(false)
    }
  }

  const loadOptions = async () => {
    try {
      const accounts = await getAccountDetails()
      setAccountOptions(accounts.map((a) => ({ id: a.id, note: a.note, enabled: a.enabled })))
    } catch {
      // 账号选项加载失败不阻塞页面
    }
    try {
      const result = await getListingMonitorTaskOptions()
      if (result.success && result.data) {
        setMonitorTasks(result.data.list || [])
      }
    } catch {
      // 监控任务选项加载失败不阻塞页面
    }
  }

  useEffect(() => {
    loadTasks(1)
    loadOptions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const openCreate = () => {
    setEditingTask(null)
    setForm({ ...emptyForm })
    setShowModal(true)
  }

  const openEdit = (task: LeadCaptureTask) => {
    setEditingTask(task)
    setForm({
      name: task.name,
      source_type: task.source_type,
      keyword: task.keyword || '',
      monitor_task_id: task.monitor_task_id ?? null,
      price_min: task.price_min ?? null,
      price_max: task.price_max ?? null,
      interval_minutes: task.interval_minutes,
      max_items_per_round: task.max_items_per_round,
      include_weak: task.include_weak,
      account_ids: task.account_ids || [],
      rescan_cooldown_hours: task.rescan_cooldown_hours,
      is_enabled: task.is_enabled,
      remark: task.remark || '',
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      addToast({ type: 'warning', message: '请填写任务名称' })
      return
    }
    if (form.source_type === 'monitor' && !form.monitor_task_id) {
      addToast({ type: 'warning', message: '请选择关联的商品监控任务' })
      return
    }
    if (form.source_type === 'keyword' && !form.keyword?.trim()) {
      addToast({ type: 'warning', message: '请填写搜索词' })
      return
    }
    if (form.account_ids.length === 0) {
      addToast({ type: 'warning', message: '请至少选择一个读取账号' })
      return
    }
    try {
      setSaving(true)
      const payload: LeadTaskPayload = { ...form }
      const result = editingTask ? await updateLeadTask(editingTask.id, payload) : await createLeadTask(payload)
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '保存失败' })
        return
      }
      addToast({ type: 'success', message: result.message || '保存成功' })
      setShowModal(false)
      loadTasks(editingTask ? page : 1)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '保存失败') })
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (task: LeadCaptureTask) => {
    try {
      const result = await updateLeadTaskStatus(task.id, !task.is_enabled)
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '操作失败' })
        return
      }
      loadTasks(page)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '操作失败') })
    }
  }

  const handleRun = async (task: LeadCaptureTask) => {
    try {
      setRunningId(task.id)
      const result = await runLeadTask(task.id)
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '扫描执行失败' })
        return
      }
      addToast({ type: 'success', message: result.message || '扫描已执行' })
      loadTasks(page)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '扫描执行失败') })
    } finally {
      setRunningId(null)
    }
  }

  const handleDelete = async () => {
    if (deleteId === null) return
    try {
      const result = await deleteLeadTask(deleteId)
      if (!result.success) {
        addToast({ type: 'error', message: result.message || '删除失败' })
        return
      }
      addToast({ type: 'success', message: '任务已删除' })
      setDeleteId(null)
      loadTasks(page)
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '删除失败') })
    }
  }

  if (loading && tasks.length === 0) {
    return <PageLoading />
  }

  return (
    <div className="p-4 lg:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">线索采集任务</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            扫描间隔最低 30 分钟、每轮最多 10 个商品（风控下限，后端强校验）；候选池优先复用商品监控采集结果
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          新建任务
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadTasks(1)}
            placeholder="按任务名称搜索"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-700 focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          />
        </div>
        <button
          onClick={() => loadTasks(1)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-sm text-gray-700 ring-1 ring-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700"
        >
          <RefreshCw className="h-4 w-4" />
          查询
        </button>
      </div>

      {/* 任务表格 */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-200 dark:bg-gray-800 dark:ring-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              {['任务名称', '候选来源', '间隔(分钟)', '每轮商品数', '读取账号', '最近执行', '状态', '操作'].map((h) => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-sm text-gray-400">
                  暂无线索采集任务，点击右上角新建
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-3 py-2.5">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{task.name}</div>
                    {task.remark && <div className="mt-0.5 text-xs text-gray-400">{task.remark}</div>}
                  </td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">
                    {task.source_type === 'monitor' ? (
                      <span>商品监控 #{task.monitor_task_id}</span>
                    ) : (
                      <span>关键词「{task.keyword}」</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{task.interval_minutes}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{task.max_items_per_round}</td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 dark:text-gray-300">{task.account_ids.length} 个</td>
                  <td className="px-3 py-2.5 text-xs text-gray-500 dark:text-gray-400">
                    {task.last_run_at ? new Date(task.last_run_at).toLocaleString() : '未执行'}
                  </td>
                  <td className="px-3 py-2.5">
                    <button
                      onClick={() => handleToggle(task)}
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        task.is_enabled
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                      }`}
                    >
                      {task.is_enabled ? '启用' : '停用'}
                    </button>
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleRun(task)}
                        disabled={runningId === task.id || !task.is_enabled}
                        title={task.is_enabled ? '立即扫描一次' : '任务已停用'}
                        className="rounded p-1 text-cyan-600 hover:bg-cyan-50 disabled:opacity-40 dark:hover:bg-cyan-900/30"
                      >
                        {runningId === task.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => openEdit(task)}
                        className="rounded p-1 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                        title="编辑"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteId(task.id)}
                        className="rounded p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
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
              onClick={() => loadTasks(page - 1)}
              disabled={page <= 1}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => loadTasks(page + 1)}
              disabled={page >= totalPages}
              className="rounded border border-gray-200 px-2 py-1 disabled:opacity-40 dark:border-gray-700"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 创建/编辑弹层 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-gray-800">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {editingTask ? '编辑线索任务' : '新建线索任务'}
            </h2>

            <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">任务名称 *</span>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">候选来源</span>
                <select
                  value={form.source_type}
                  onChange={(e) => setForm({ ...form, source_type: e.target.value as LeadTaskPayload['source_type'] })}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                >
                  <option value="monitor">复用商品监控采集池（推荐，零额外搜索请求）</option>
                  <option value="keyword">独立关键词搜索</option>
                </select>
              </label>

              {form.source_type === 'monitor' ? (
                <label className="text-sm">
                  <span className="text-gray-600 dark:text-gray-300">关联商品监控任务 *</span>
                  <select
                    value={form.monitor_task_id ?? ''}
                    onChange={(e) => setForm({ ...form, monitor_task_id: e.target.value ? Number(e.target.value) : null })}
                    className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  >
                    <option value="">请选择</option>
                    {monitorTasks.map((t) => (
                      <option key={t.id} value={t.id}>
                        #{t.id} {t.keyword ? `「${t.keyword}」` : ''}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <label className="text-sm">
                  <span className="text-gray-600 dark:text-gray-300">搜索词 *</span>
                  <input
                    value={form.keyword ?? ''}
                    onChange={(e) => setForm({ ...form, keyword: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  />
                </label>
              )}

              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">扫描间隔分钟（风控下限 30）</span>
                <input
                  type="number"
                  min={30}
                  max={1440}
                  value={form.interval_minutes}
                  onChange={(e) => setForm({ ...form, interval_minutes: Number(e.target.value) })}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">每轮商品数（风控上限 10）</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={form.max_items_per_round}
                  onChange={(e) => setForm({ ...form, max_items_per_round: Number(e.target.value) })}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">重扫冷却小时（默认 24）</span>
                <input
                  type="number"
                  min={1}
                  max={168}
                  value={form.rescan_cooldown_hours}
                  onChange={(e) => setForm({ ...form, rescan_cooldown_hours: Number(e.target.value) })}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
              <label className="text-sm">
                <span className="text-gray-600 dark:text-gray-300">候选价格区间（可选）</span>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="最低"
                    value={form.price_min ?? ''}
                    onChange={(e) => setForm({ ...form, price_min: e.target.value === '' ? null : Number(e.target.value) })}
                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  />
                  <span className="text-gray-400">~</span>
                  <input
                    type="number"
                    placeholder="最高"
                    value={form.price_max ?? ''}
                    onChange={(e) => setForm({ ...form, price_max: e.target.value === '' ? null : Number(e.target.value) })}
                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  />
                </div>
              </label>

              <label className="text-sm md:col-span-2">
                <span className="text-gray-600 dark:text-gray-300">读取账号（只读借用 Cookie，不发送任何消息）*</span>
                <div className="mt-1 max-h-36 overflow-y-auto rounded-lg border border-gray-200 p-2 dark:border-gray-700">
                  {accountOptions.length === 0 ? (
                    <span className="text-xs text-gray-400">暂无可用账号</span>
                  ) : (
                    accountOptions.map((acc) => (
                      <label key={acc.id} className="flex items-center gap-2 px-1 py-1 text-sm text-gray-700 dark:text-gray-200">
                        <input
                          type="checkbox"
                          checked={form.account_ids.includes(acc.id)}
                          onChange={(e) =>
                            setForm({
                              ...form,
                              account_ids: e.target.checked
                                ? [...form.account_ids, acc.id]
                                : form.account_ids.filter((id) => id !== acc.id),
                            })
                          }
                        />
                        <span>
                          {acc.id}
                          {acc.note ? `（${acc.note}）` : ''}
                        </span>
                        {!acc.enabled && <span className="text-xs text-gray-400">[禁用]</span>}
                      </label>
                    ))
                  )}
                </div>
              </label>

              <label className="text-sm md:col-span-2">
                <span className="text-gray-600 dark:text-gray-300">备注</span>
                <textarea
                  value={form.remark ?? ''}
                  onChange={(e) => setForm({ ...form, remark: e.target.value })}
                  rows={2}
                  className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50 dark:text-gray-300 dark:ring-gray-700 dark:hover:bg-gray-700"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认 */}
      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl dark:bg-gray-800">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">删除线索任务</h3>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">删除后任务停止扫描，已入库线索保留。确定删除？</p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setDeleteId(null)}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50 dark:text-gray-300 dark:ring-gray-700"
              >
                取消
              </button>
              <button onClick={handleDelete} className="rounded-lg bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700">
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
