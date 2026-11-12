/**
 * 商品迁移页面
 *
 * 功能：把源账号（默认 2221611389164）中【有卡券关联】的商品，
 * 以随机 3~10 分钟/个的低频节奏，发布到目标账号（默认 2222909890293）。
 * 卡券会自动复制并按映射重建关联。命中风控特征（滑块/验证）时批次自动暂停。
 */
import { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw, Plus, Play, Pause, XCircle, Clock, AlertTriangle,
  CheckSquare, Square, Edit2, Eye, Package, ArrowRight, RotateCcw, Tag,
} from 'lucide-react'
import {
  getSourceItems, createBatch, getBatches, getBatchDetail,
  startBatch, pauseBatch, cancelBatch, updateMigrationTask,
  getCategoryCandidates, retryTask,
  type SourceItem, type MigrationBatch, type MigrationTask, type BatchDetail, type CategoryCandidate,
} from '@/api/migration'
import { getAccountDetails } from '@/api/accounts'
import { useUIStore } from '@/store/uiStore'
import { PageLoading } from '@/components/common/Loading'
import { ConfirmModal } from '@/components/common/ConfirmModal'

const DEFAULT_SOURCE = '2221611389164'
const DEFAULT_TARGET = '2222909890293'
const DEFAULT_TEMPLATE = '{title}\n下单后自动发货，卡密/兑换码将通过聊天发送，请注意查收。\n如有问题请先联系客服，谢谢支持！'

const statusMeta: Record<MigrationBatch['status'], { label: string; cls: string }> = {
  prepared: { label: '待启动', cls: 'bg-gray-100 text-gray-600' },
  running: { label: '运行中', cls: 'bg-green-100 text-green-700' },
  paused: { label: '已暂停', cls: 'bg-yellow-100 text-yellow-700' },
  done: { label: '已完成', cls: 'bg-blue-100 text-blue-700' },
  cancelled: { label: '已取消', cls: 'bg-red-100 text-red-600' },
}

const taskStatusMeta: Record<MigrationTask['status'], { label: string; cls: string }> = {
  pending: { label: '待发布', cls: 'bg-gray-100 text-gray-600' },
  publishing: { label: '发布中', cls: 'bg-blue-100 text-blue-700' },
  done: { label: '已发布', cls: 'bg-green-100 text-green-700' },
  failed: { label: '失败', cls: 'bg-red-100 text-red-600' },
  skipped: { label: '已跳过', cls: 'bg-yellow-100 text-yellow-700' },
}

function fmtCountdown(sec?: number | null): string {
  if (sec == null || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

export function Migration() {
  const { addToast } = useUIStore()

  // ===== 批次列表 =====
  const [batches, setBatches] = useState<MigrationBatch[]>([])
  const [loading, setLoading] = useState(true)

  // ===== 创建向导 =====
  const [showCreate, setShowCreate] = useState(false)
  const [accounts, setAccounts] = useState<{ id: string; note?: string }[]>([])
  const [sourceAccountId, setSourceAccountId] = useState(DEFAULT_SOURCE)
  const [targetAccountId, setTargetAccountId] = useState(DEFAULT_TARGET)
  const [sourceItems, setSourceItems] = useState<SourceItem[]>([])
  const [loadingItems, setLoadingItems] = useState(false)
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [minInterval, setMinInterval] = useState(180)
  const [maxInterval, setMaxInterval] = useState(600)
  const [descTemplate, setDescTemplate] = useState(DEFAULT_TEMPLATE)
  const [creating, setCreating] = useState(false)

  // ===== 批次详情 =====
  const [detail, setDetail] = useState<BatchDetail | null>(null)
  const [showDetail, setShowDetail] = useState(false)
  const [editingTask, setEditingTask] = useState<MigrationTask | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editPrice, setEditPrice] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [savingTask, setSavingTask] = useState(false)

  // ===== 类目覆盖 =====
  type OverrideChoice = { cat_name: string; channel_cat_id: string; channel_cat_name: string }
  const [overrideChoice, setOverrideChoice] = useState<OverrideChoice | null>(null)
  const [candTask, setCandTask] = useState<MigrationTask | null>(null)
  const [candidates, setCandidates] = useState<CategoryCandidate[]>([])
  const [candLoading, setCandLoading] = useState(false)
  const [retryingId, setRetryingId] = useState<number | null>(null)

  const [confirm, setConfirm] = useState<{ message: string; action: () => Promise<void>; type?: 'warning' | 'danger' } | null>(null)
  const [confirmLoading, setConfirmLoading] = useState(false)

  // ===== 数据加载 =====
  const loadBatches = useCallback(async () => {
    try {
      const res = await getBatches()
      if (res.success) setBatches(res.data.batches)
    } catch {
      addToast({ type: 'error', message: '加载批次列表失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    loadBatches()
    // 运行中批次每 15s 刷新一次倒计时
    const timer = setInterval(() => { loadBatches() }, 15000)
    return () => clearInterval(timer)
  }, [loadBatches])

  const openCreate = async () => {
    setShowCreate(true)
    setSourceItems([])
    setSelectedItems(new Set())
    try {
      const list = await getAccountDetails()
      setAccounts(list.map(a => ({ id: a.id, note: a.note })))
    } catch { /* 账号列表失败不阻塞，仍可手输 */ }
  }

  const loadSourceItems = async () => {
    if (!sourceAccountId.trim()) {
      addToast({ type: 'warning', message: '请填写源账号ID' })
      return
    }
    setLoadingItems(true)
    try {
      const res = await getSourceItems(sourceAccountId.trim())
      if (res.success) {
        setSourceItems(res.data.items)
        setSelectedItems(new Set(res.data.items.map(i => i.item_id))) // 默认全选
        if (res.data.total === 0) addToast({ type: 'warning', message: '该账号没有带卡券关联的商品' })
      }
    } catch {
      addToast({ type: 'error', message: '拉取源商品失败，请确认源账号ID正确' })
    } finally {
      setLoadingItems(false)
    }
  }

  const toggleItem = (id: string) => {
    const next = new Set(selectedItems)
    if (next.has(id)) next.delete(id); else next.add(id)
    setSelectedItems(next)
  }

  const handleCreate = async () => {
    if (selectedItems.size === 0) {
      addToast({ type: 'warning', message: '请先勾选要迁移的商品' })
      return
    }
    if (minInterval < 60 || maxInterval < minInterval) {
      addToast({ type: 'warning', message: '间隔不合法：最小≥60秒，最大≥最小' })
      return
    }
    setCreating(true)
    try {
      const res = await createBatch({
        source_account_id: sourceAccountId.trim(),
        target_account_id: targetAccountId.trim(),
        item_ids: Array.from(selectedItems),
        description_template: descTemplate,
        min_interval: minInterval,
        max_interval: maxInterval,
      })
      if (res.success) {
        addToast({ type: 'success', message: `批次已创建：${res.data.total}个商品，复制卡券${res.data.cards_copied}张。点击"开始"后按随机间隔发布` })
        setShowCreate(false)
        loadBatches()
      } else {
        addToast({ type: 'error', message: res.message || '创建批次失败' })
      }
    } catch {
      addToast({ type: 'error', message: '创建批次失败' })
    } finally {
      setCreating(false)
    }
  }

  // ===== 批次操作 =====
  const doAction = async (fn: () => Promise<{ success: boolean; message: string }>, okMsg: string) => {
    try {
      const res = await fn()
      if (res.success) {
        addToast({ type: 'success', message: okMsg })
        loadBatches()
      } else {
        addToast({ type: 'error', message: res.message || '操作失败' })
      }
    } catch {
      addToast({ type: 'error', message: '操作失败' })
    }
  }

  const openDetail = async (batchId: number) => {
    try {
      const res = await getBatchDetail(batchId)
      if (res.success) {
        setDetail(res.data)
        setShowDetail(true)
      }
    } catch {
      addToast({ type: 'error', message: '加载批次详情失败' })
    }
  }

  const openEditTask = (task: MigrationTask) => {
    setEditingTask(task)
    setEditTitle(task.title)
    setEditPrice(task.price || '')
    setEditDesc(task.description || '')
    setOverrideChoice(
      task.category_override
        ? {
            cat_name: task.category_override.cat_name || '',
            channel_cat_id: task.category_override.channel_cat_id || '',
            channel_cat_name: task.category_override.channel_cat_name || '',
          }
        : null
    )
  }

  const openCategoryModal = async (task: MigrationTask) => {
    setCandTask(task)
    setCandLoading(true)
    setCandidates([])
    try {
      const res = await getCategoryCandidates(task.id)
      if (res.success) {
        setCandidates(res.data.candidates || [])
        if (!(res.data.candidates || []).length) {
          addToast({ type: 'warning', message: '该账号暂无可选类目候选' })
        }
      } else {
        addToast({ type: 'error', message: res.message || '获取类目候选失败' })
        setCandTask(null)
      }
    } catch {
      addToast({ type: 'error', message: '获取类目候选失败' })
      setCandTask(null)
    } finally {
      setCandLoading(false)
    }
  }

  const handleRetry = async (task: MigrationTask) => {
    setRetryingId(task.id)
    try {
      const res = await retryTask(task.id)
      addToast({ type: res.success ? 'success' : 'error', message: res.message || (res.success ? '已重置重试' : '重置失败') })
      if (res.success && detail) openDetail(detail.batch.id)
    } catch {
      addToast({ type: 'error', message: '重置失败' })
    } finally {
      setRetryingId(null)
    }
  }

  const saveTask = async () => {
    if (!editingTask) return
    setSavingTask(true)
    try {
      const res = await updateMigrationTask(editingTask.id, {
        title: editTitle,
        price: editPrice,
        description: editDesc,
        ...(overrideChoice
          ? { category_override: overrideChoice }
          : editingTask.category_override
            ? { clear_category_override: true }
            : {}),
      })
      if (res.success) {
        addToast({ type: 'success', message: '已保存' })
        setEditingTask(null)
        if (detail) openDetail(detail.batch.id)
      } else {
        addToast({ type: 'error', message: res.message || '保存失败' })
      }
    } catch {
      addToast({ type: 'error', message: '保存失败' })
    } finally {
      setSavingTask(false)
    }
  }

  if (loading && batches.length === 0) return <PageLoading />

  return (
    <div className="space-y-4">
      {/* 页头 */}
      <div className="page-header flex-between flex-wrap gap-4">
        <div>
          <h1 className="page-title">商品迁移</h1>
          <p className="page-description">
            把有卡券关联的商品跨账号搬迁发布 · 随机间隔低频发布，命中风控自动暂停
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={openCreate} className="btn-ios-primary">
            <Plus className="w-4 h-4" />
            新建迁移批次
          </button>
          <button onClick={() => loadBatches()} className="btn-ios-secondary">
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
      </div>

      {/* 风控提示 */}
      <div className="vben-card">
        <div className="vben-card-body flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
          <div className="text-sm text-gray-600 space-y-1">
            <p>发布节奏：每发完 1 个商品，随机等待 3~10 分钟（以批次设置的间隔为准）再发下一个。</p>
            <p>若命中滑块/人机验证等风控特征，批次会自动暂停并记录原因，确认账号无恙后可手动继续。</p>
            <p className="text-gray-400">建议首个批次只勾选 1 个商品试水，确认链路通畅后再放量。</p>
          </div>
        </div>
      </div>

      {/* 批次列表 */}
      <div className="vben-card">
        <div className="vben-card-body space-y-3">
          {batches.length === 0 ? (
            <div className="text-center text-gray-400 py-10">
              <Package className="w-10 h-10 mx-auto mb-2 opacity-40" />
              暂无迁移批次，点击右上角"新建迁移批次"开始
            </div>
          ) : (
            batches.map(b => {
              const meta = statusMeta[b.status]
              const pct = b.total > 0 ? Math.round(((b.published + b.failed) / b.total) * 100) : 0
              return (
                <div key={b.id} className="border border-gray-100 rounded-lg p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <span>批次 #{b.id}</span>
                      <span className="text-gray-500 font-mono">{b.source_account_id}</span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500 font-mono">{b.target_account_id}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${meta.cls}`}>{meta.label}</span>
                  </div>

                  {/* 进度条 */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>进度 {b.published}/{b.total} 已发布{b.failed > 0 ? `，${b.failed} 失败` : ''}（{pct}%）</span>
                      {b.status === 'running' && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          下次发布：{fmtCountdown(b.next_run_in_seconds)}
                        </span>
                      )}
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 transition-all" style={{ width: `${pct}%` }} />
                    </div>
                  </div>

                  {b.last_error && (
                    <div className="text-xs text-red-600 bg-red-50 rounded px-3 py-2 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>{b.last_error}</span>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {(b.status === 'prepared' || b.status === 'paused') && (
                      <button
                        onClick={() => doAction(() => startBatch(b.id), '批次已启动/继续')}
                        className="btn-ios-primary text-xs"
                      >
                        <Play className="w-3.5 h-3.5" /> 开始{b.status === 'paused' ? '（继续）' : ''}
                      </button>
                    )}
                    {b.status === 'running' && (
                      <button
                        onClick={() => doAction(() => pauseBatch(b.id), '批次已暂停，当前发布中的商品不受影响')}
                        className="btn-ios-secondary text-xs"
                      >
                        <Pause className="w-3.5 h-3.5" /> 暂停
                      </button>
                    )}
                    <button onClick={() => openDetail(b.id)} className="btn-ios-secondary text-xs">
                      <Eye className="w-3.5 h-3.5" /> 详情
                    </button>
                    {(b.status === 'prepared' || b.status === 'paused' || b.status === 'running') && (
                      <button
                        onClick={() => setConfirm({
                          message: `确定取消批次 #${b.id}？未发布的商品将不再发布，已发布的不受影响。`,
                          type: 'danger',
                          action: async () => { await doAction(() => cancelBatch(b.id), '批次已取消') },
                        })}
                        className="btn-ios-danger text-xs"
                      >
                        <XCircle className="w-3.5 h-3.5" /> 取消
                      </button>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* ===== 创建批次弹窗 ===== */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => !creating && setShowCreate(false)}>
          <div className="modal-content max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="modal-header flex items-center justify-between sticky top-0 bg-white dark:bg-gray-900 z-10">
              <h3 className="text-lg font-semibold">新建迁移批次</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="modal-body space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">源账号（被搬）</label>
                  {accounts.length > 0 ? (
                    <select value={sourceAccountId} onChange={e => setSourceAccountId(e.target.value)} className="input-ios">
                      {accounts.map(a => <option key={a.id} value={a.id}>{a.id}{a.note ? `（${a.note}）` : ''}</option>)}
                    </select>
                  ) : (
                    <input value={sourceAccountId} onChange={e => setSourceAccountId(e.target.value)} className="input-ios" />
                  )}
                </div>
                <div className="input-group">
                  <label className="input-label">目标账号（搬入）</label>
                  {accounts.length > 0 ? (
                    <select value={targetAccountId} onChange={e => setTargetAccountId(e.target.value)} className="input-ios">
                      {accounts.map(a => <option key={a.id} value={a.id}>{a.id}{a.note ? `（${a.note}）` : ''}</option>)}
                    </select>
                  ) : (
                    <input value={targetAccountId} onChange={e => setTargetAccountId(e.target.value)} className="input-ios" />
                  )}
                </div>
              </div>

              <div className="flex items-end gap-3">
                <button onClick={loadSourceItems} disabled={loadingItems} className="btn-ios-secondary">
                  <RefreshCw className={`w-4 h-4 ${loadingItems ? 'animate-spin' : ''}`} />
                  {loadingItems ? '拉取中...' : '拉取有卡券关联的商品'}
                </button>
                {sourceItems.length > 0 && (
                  <span className="text-sm text-gray-500 pb-2">
                    共 {sourceItems.length} 个，已选 {selectedItems.size} 个
                  </span>
                )}
              </div>

              {/* 商品勾选表格 */}
              {sourceItems.length > 0 && (
                <div className="border border-gray-100 rounded-lg overflow-hidden max-h-72 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="p-2 w-10">
                          <button onClick={() => {
                            if (selectedItems.size === sourceItems.length) setSelectedItems(new Set())
                            else setSelectedItems(new Set(sourceItems.map(i => i.item_id)))
                          }}>
                            {selectedItems.size === sourceItems.length
                              ? <CheckSquare className="w-4 h-4 text-blue-500" />
                              : <Square className="w-4 h-4 text-gray-400" />}
                          </button>
                        </th>
                        <th className="p-2 text-left">商品标题</th>
                        <th className="p-2 text-left w-24">价格</th>
                        <th className="p-2 text-left w-40">关联卡券</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sourceItems.map(item => (
                        <tr key={item.item_id} className="border-t border-gray-50 hover:bg-gray-50">
                          <td className="p-2 text-center">
                            <button onClick={() => toggleItem(item.item_id)}>
                              {selectedItems.has(item.item_id)
                                ? <CheckSquare className="w-4 h-4 text-blue-500" />
                                : <Square className="w-4 h-4 text-gray-400" />}
                            </button>
                          </td>
                          <td className="p-2 truncate max-w-0" title={item.title}>{item.title || item.item_id}</td>
                          <td className="p-2">{item.price || '—'}</td>
                          <td className="p-2 text-xs text-gray-500 truncate max-w-0" title={item.card_names.join('、')}>
                            {item.card_count}张 · {item.card_names.slice(0, 2).join('、')}{item.card_names.length > 2 ? '...' : ''}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 间隔设置 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">最小间隔（秒）</label>
                  <input type="number" min={60} value={minInterval} onChange={e => setMinInterval(Number(e.target.value))} className="input-ios" />
                </div>
                <div className="input-group">
                  <label className="input-label">最大间隔（秒）</label>
                  <input type="number" min={60} value={maxInterval} onChange={e => setMaxInterval(Number(e.target.value))} className="input-ios" />
                </div>
              </div>
              <p className="text-xs text-gray-400 -mt-2">
                每个商品发布后，在 [{minInterval}~{maxInterval}] 秒内随机等待再发下一个
                （27个商品约需 {Math.round(selectedItems.size * minInterval / 3600 * 10) / 10}~{Math.round(selectedItems.size * maxInterval / 3600 * 10) / 10} 小时）
              </p>

              {/* 描述模板 */}
              <div className="input-group">
                <label className="input-label">描述模板（{'{title}'} 会被替换为商品标题，发布前可逐条编辑）</label>
                <textarea
                  rows={4}
                  value={descTemplate}
                  onChange={e => setDescTemplate(e.target.value)}
                  className="input-ios resize-none"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowCreate(false)} disabled={creating} className="btn-ios-secondary">取消</button>
              <button onClick={handleCreate} disabled={creating || selectedItems.size === 0} className="btn-ios-primary">
                {creating ? '创建中...' : `创建批次（${selectedItems.size}个商品）`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== 批次详情弹窗 ===== */}
      {showDetail && detail && (
        <div className="modal-overlay" onClick={() => setShowDetail(false)}>
          <div className="modal-content max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="modal-header flex items-center justify-between sticky top-0 bg-white dark:bg-gray-900 z-10">
              <h3 className="text-lg font-semibold">批次 #{detail.batch.id} 详情</h3>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="modal-body space-y-3">
              <div className="text-sm text-gray-500">
                已复制卡券 {detail.cards_copied} 张 · 来源 {detail.batch.source_account_id} → 目标 {detail.batch.target_account_id}
              </div>
              <div className="border border-gray-100 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="p-2 text-left w-12">图</th>
                      <th className="p-2 text-left">标题</th>
                      <th className="p-2 text-left w-20">价格</th>
                      <th className="p-2 text-left w-24">状态</th>
                      <th className="p-2 text-left w-32">新商品ID</th>
                      <th className="p-2 text-left w-16">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.tasks.map(task => (
                      <tr key={task.id} className="border-t border-gray-50">
                        <td className="p-2">
                          {task.first_image
                            ? <img src={task.first_image} alt="" className="w-8 h-8 rounded object-cover" />
                            : <span className="text-gray-300">—</span>}
                        </td>
                        <td className="p-2 truncate max-w-0" title={task.title}>
                          {task.title}
                          {task.category_override && (
                            <span className="ml-1 inline-flex items-center gap-0.5 text-xs text-purple-600 bg-purple-50 px-1 rounded" title={`发布时锁定该类目：${task.category_override.cat_name}`}>
                              <Tag className="w-3 h-3" />
                              {task.category_override.cat_name}
                            </span>
                          )}
                        </td>
                        <td className="p-2">{task.price || '—'}</td>
                        <td className="p-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${taskStatusMeta[task.status].cls}`}>
                            {taskStatusMeta[task.status].label}
                          </span>
                          {task.error && (
                            <div className="text-xs text-red-500 mt-1 truncate max-w-40" title={task.error}>{task.error}</div>
                          )}
                        </td>
                        <td className="p-2 text-xs font-mono text-gray-500">{task.new_item_id || '—'}</td>
                        <td className="p-2">
                          <div className="flex items-center gap-2">
                            {(task.status === 'pending' || task.status === 'failed') && (
                              <button onClick={() => openEditTask(task)} className="text-blue-500 hover:text-blue-700" title="编辑">
                                <Edit2 className="w-4 h-4" />
                              </button>
                            )}
                            {(task.status === 'failed' || task.status === 'skipped') && (
                              <button
                                onClick={() => handleRetry(task)}
                                disabled={retryingId === task.id}
                                className="text-green-500 hover:text-green-700 disabled:opacity-40"
                                title="重新发布该商品"
                              >
                                <RotateCcw className={`w-4 h-4 ${retryingId === task.id ? 'animate-spin' : ''}`} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowDetail(false)} className="btn-ios-secondary">关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* ===== 任务编辑弹窗 ===== */}
      {editingTask && (
        <div className="modal-overlay" onClick={() => !savingTask && setEditingTask(null)}>
          <div className="modal-content max-w-lg w-full" onClick={e => e.stopPropagation()}>
            <div className="modal-header flex items-center justify-between sticky top-0 bg-white dark:bg-gray-900 z-10">
              <h3 className="text-lg font-semibold">编辑待发布商品</h3>
              <button onClick={() => setEditingTask(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="modal-body space-y-4">
              <div className="input-group">
                <label className="input-label">标题</label>
                <input value={editTitle} onChange={e => setEditTitle(e.target.value)} className="input-ios" maxLength={30} />
                <p className="text-xs text-gray-400">{editTitle.length}/30</p>
              </div>
              <div className="input-group">
                <label className="input-label">价格（元）</label>
                <input value={editPrice} onChange={e => setEditPrice(e.target.value)} className="input-ios" />
              </div>
              <div className="input-group">
                <label className="input-label">发布类目（不改标题，只改归类）</label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700 flex-1">
                    {overrideChoice ? overrideChoice.cat_name : '自动推荐（闲鱼首选类目）'}
                  </span>
                  <button
                    type="button"
                    onClick={() => editingTask && openCategoryModal(editingTask)}
                    className="btn-ios-secondary text-xs px-2 py-1"
                  >
                    {overrideChoice ? '更换' : '选择类目'}
                  </button>
                  {overrideChoice && (
                    <button
                      type="button"
                      onClick={() => setOverrideChoice(null)}
                      className="text-xs text-gray-400 hover:text-red-500"
                    >
                      清除
                    </button>
                  )}
                </div>
                {overrideChoice?.cat_name.match(/图书|书|教材|小说|文学|杂志|报刊|绘本/) && (
                  <p className="text-xs text-amber-600 mt-1">
                    提示：图书类类目通常要求 ISBN 条码，需手工扫码发布；建议选择电子资料/服务等虚拟类目。
                  </p>
                )}
              </div>
              <div className="input-group">
                <label className="input-label">描述</label>
                <textarea rows={6} value={editDesc} onChange={e => setEditDesc(e.target.value)} className="input-ios resize-none" />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setEditingTask(null)} disabled={savingTask} className="btn-ios-secondary">取消</button>
              <button onClick={saveTask} disabled={savingTask} className="btn-ios-primary">
                {savingTask ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== 类目候选选择弹窗 ===== */}
      {candTask && (
        <div className="modal-overlay" style={{ zIndex: 60 }} onClick={() => setCandTask(null)}>
          <div className="modal-content max-w-md w-full" onClick={e => e.stopPropagation()}>
            <div className="modal-header flex items-center justify-between">
              <h3 className="text-lg font-semibold">选择发布类目</h3>
              <button onClick={() => setCandTask(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="modal-body">
              <p className="text-xs text-gray-400 mb-3">
                基于当前标题/描述向闲鱼工作台实时请求的候选类目。商品标题、描述均不变——仅改变它在新账号上的归类。
              </p>
              {candLoading && <p className="text-sm text-gray-400 py-6 text-center">正在请求闲鱼类目候选…</p>}
              {!candLoading && (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {candidates.map((c, idx) => {
                    const name = c.cat_name || c.channel_cat_name || '未名类目'
                    const channelOk = !!c.channel_cat_id
                    return (
                      <label
                        key={`${c.channel_cat_id || name}-${idx}`}
                        className={`flex items-start gap-2 p-2 rounded border cursor-pointer transition-colors
                          ${overrideChoice?.channel_cat_id === c.channel_cat_id ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-200'}
                          ${!channelOk ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <input
                          type="radio"
                          name="category-pick"
                          className="mt-1"
                          disabled={!channelOk}
                          checked={overrideChoice?.channel_cat_id === c.channel_cat_id}
                          onChange={() => {
                            if (!channelOk) return
                            setOverrideChoice({
                              cat_name: name,
                              channel_cat_id: c.channel_cat_id!,
                              channel_cat_name: c.channel_cat_name || name,
                            })
                            setCandTask(null)
                          }}
                        />
                        <span className="flex-1">
                          <span className="text-sm">{name}</span>
                          {c.is_selected && <span className="ml-2 text-xs text-green-600">平台首选</span>}
                          {c.may_need_isbn && <span className="ml-2 text-xs text-red-500">需 ISBN</span>}
                          {!c.tb_cat_id && (
                            <span className="block text-xs text-gray-400">选中后由平台二次解析即可正常发布</span>
                          )}
                        </span>
                      </label>
                    )
                  })}
                  {candidates.length === 0 && !candLoading && (
                    <p className="text-sm text-gray-400 py-4 text-center">无候选</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 确认弹窗 */}
      {confirm && (
        <ConfirmModal
          isOpen
          title="操作确认"
          message={confirm.message}
          type={confirm.type || 'warning'}
          loading={confirmLoading}
          onConfirm={async () => {
            setConfirmLoading(true)
            await confirm.action()
            setConfirmLoading(false)
            setConfirm(null)
          }}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  )
}
