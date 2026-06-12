import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ShoppingBag, ExternalLink, MapPin, Heart, Download, Send, FileEdit, X } from 'lucide-react'
import { searchItems, SearchResultItem } from '@/api/search'
import { collectToMaterial, getAccountOptions, publishSingle, AccountOption } from '@/api/material'
import { useUIStore } from '@/store/uiStore'
import { ButtonLoading } from '@/components/common/Loading'

export function ItemSearch() {
  const { addToast } = useUIStore()
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [total, setTotal] = useState(0)

  // 按钮加载状态
  const [collectingId, setCollectingId] = useState<string | null>(null)
  const [draftingId, setDraftingId] = useState<string | null>(null)
  const [collectedIds, setCollectedIds] = useState<Set<string>>(new Set())

  // 发布弹窗状态
  const [publishModal, setPublishModal] = useState<{ open: boolean; item: SearchResultItem | null }>({ open: false, item: null })
  const [accounts, setAccounts] = useState<AccountOption[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string>('')
  const [accountsLoading, setAccountsLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!keyword.trim()) {
      addToast({ type: 'warning', message: '请输入搜索关键词' })
      return
    }

    addToast({ type: 'info', message: '正在搜索中，请稍候...' })
    
    try {
      setLoading(true)
      setResults([])
      const result = await searchItems(keyword.trim())
      
      if (result.success) {
        setResults(result.data || [])
        setTotal(result.total || result.data.length)
        
        if ((result.data || []).length === 0) {
          addToast({ type: 'info', message: '未找到相关商品' })
        } else {
          addToast({ type: 'success', message: `搜索完成，找到 ${result.data.length} 件商品` })
        }
        
        if (result.error) {
          addToast({ type: 'warning', message: result.error })
        }
      }
    } catch {
      addToast({ type: 'error', message: '搜索失败，请稍后重试' })
    } finally {
      setLoading(false)
    }
  }

  /** 采集到素材库 */
  const handleCollect = async (item: SearchResultItem) => {
    const key = item.item_id
    if (collectedIds.has(key)) return
    setCollectingId(key)
    try {
      const res = await collectToMaterial({
        item_id: item.item_id,
        title: item.title,
        price: item.price,
        main_image: item.main_image,
        item_url: item.item_url,
        area: item.area,
        seller_name: item.seller_name,
      })
      if (res.success) {
        setCollectedIds(prev => new Set(prev).add(key))
        addToast({ type: 'success', message: res.message || '采集成功，已保存到素材库' })
      } else {
        addToast({ type: 'error', message: res.message || '采集失败' })
      }
    } catch {
      addToast({ type: 'error', message: '采集失败，请稍后重试' })
    } finally {
      setCollectingId(null)
    }
  }

  /** 转草稿：采集后跳转素材编辑页 */
  const handleToDraft = async (item: SearchResultItem) => {
    setDraftingId(item.item_id)
    try {
      const res = await collectToMaterial({
        item_id: item.item_id,
        title: item.title,
        price: item.price,
        main_image: item.main_image,
        item_url: item.item_url,
        area: item.area,
        seller_name: item.seller_name,
      })
      if (res.success && res.data?.material_id) {
        setCollectedIds(prev => new Set(prev).add(item.item_id))
        addToast({ type: 'success', message: '已保存到素材库，正在跳转...' })
        // 跳转到素材编辑页（使用 hash 路由）
        window.location.hash = `#/product-publish/materials?edit=${res.data.material_id}`
      } else {
        addToast({ type: 'error', message: res.message || '采集失败' })
      }
    } catch {
      addToast({ type: 'error', message: '操作失败，请稍后重试' })
    } finally {
      setDraftingId(null)
    }
  }

  /** 打开发布弹窗 */
  const handleOpenPublish = async (item: SearchResultItem) => {
    setPublishModal({ open: true, item })
    setSelectedAccountId('')
    setAccountsLoading(true)
    try {
      const list = await getAccountOptions()
      setAccounts(list.filter(a => a.enabled))
    } catch {
      addToast({ type: 'error', message: '获取账号列表失败' })
      setAccounts([])
    } finally {
      setAccountsLoading(false)
    }
  }

  /** 确认发布 */
  const handleConfirmPublish = async () => {
    if (!publishModal.item || !selectedAccountId) {
      addToast({ type: 'warning', message: '请选择发布账号' })
      return
    }
    const item = publishModal.item
    setPublishing(true)
    try {
      const priceStr = item.price.replace('¥', '').replace(',', '').trim()
      const res = await publishSingle({
        account_id: selectedAccountId,
        title: item.title,
        description: `采集自闲鱼 | 卖家: ${item.seller_name || ''} | 地区: ${item.area || ''}\n原始链接: ${item.item_url || ''}`,
        price: parseFloat(priceStr) || 1,
        images: item.main_image ? [item.main_image] : [],
        address: item.area || undefined,
        condition: '全新',
      })
      if (res.success) {
        addToast({ type: 'success', message: res.message || '发布成功' })
        setPublishModal({ open: false, item: null })
      } else {
        addToast({ type: 'error', message: res.message || '发布失败' })
      }
    } catch {
      addToast({ type: 'error', message: '发布失败，请稍后重试' })
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">商品搜索</h1>
          <p className="page-description">在闲鱼平台搜索商品</p>
        </div>
        {total > 0 && (
          <span className="badge-primary">共 {total} 件商品</span>
        )}
      </div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="vben-card"
      >
        <div className="vben-card-body">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500 z-10" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="输入关键词搜索商品..."
                className="input-ios pl-12"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-ios-primary w-full md:w-32 flex items-center justify-center"
            >
              {loading ? <ButtonLoading /> : '搜索'}
            </button>
          </form>
        </div>
      </motion.div>

      {/* Results */}
      {results.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
          {results.map((item, index) => {
            const isCollected = collectedIds.has(item.item_id)
            const isCollecting = collectingId === item.item_id
            const isDrafting = draftingId === item.item_id

            return (
              <motion.div
                key={item.item_id || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="vben-card group hover:shadow-lg transition-all duration-300 overflow-hidden"
              >
                {/* 商品图片 - 可点击外链 */}
                <a
                  href={item.item_url || `https://www.goofish.com/item?id=${item.item_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <div className="aspect-square bg-slate-100 dark:bg-slate-800 relative overflow-hidden">
                    {item.main_image ? (
                      <img 
                        src={item.main_image} 
                        alt={item.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-slate-300 dark:text-slate-600">
                        <ShoppingBag className="w-12 h-12" />
                      </div>
                    )}
                    {/* 外链图标 */}
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="bg-black/50 rounded-full p-1.5">
                        <ExternalLink className="w-3.5 h-3.5 text-white" />
                      </div>
                    </div>
                  </div>
                </a>
                
                {/* 商品信息 */}
                <div className="p-3">
                  {/* 标题可点击 */}
                  <a
                    href={item.item_url || `https://www.goofish.com/item?id=${item.item_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <h3 className="font-medium text-slate-900 dark:text-slate-100 line-clamp-2 text-sm mb-2 min-h-[2.5rem] hover:text-blue-500 transition-colors">
                      {item.title}
                    </h3>
                  </a>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-lg font-bold text-red-500">{item.price}</span>
                    {item.want_count && item.want_count > 0 && (
                      <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        {item.want_count}人想要
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span className="truncate max-w-[60%]">{item.seller_name || '-'}</span>
                    {item.area && (
                      <span className="flex items-center gap-0.5">
                        <MapPin className="w-3 h-3" />
                        {item.area}
                      </span>
                    )}
                  </div>
                  {/* 标签 */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {item.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className="text-xs px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleCollect(item) }}
                      disabled={isCollected || isCollecting}
                      className={`flex-1 flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-lg transition-all ${
                        isCollected
                          ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 cursor-default'
                          : 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50'
                      }`}
                      title="采集到素材库"
                    >
                      {isCollecting ? <ButtonLoading /> : <Download className="w-3 h-3" />}
                      {isCollected ? '已采集' : '采集'}
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleToDraft(item) }}
                      disabled={isDrafting}
                      className="flex-1 flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-lg bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/50 transition-all"
                      title="采集并跳转编辑"
                    >
                      {isDrafting ? <ButtonLoading /> : <FileEdit className="w-3 h-3" />}
                      转草稿
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleOpenPublish(item) }}
                      className="flex-1 flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-lg bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-all"
                      title="直接发布"
                    >
                      <Send className="w-3 h-3" />
                      发布
                    </button>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </motion.div>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && (
        <div className="text-center py-12 text-slate-500 dark:text-slate-400">
          <ShoppingBag className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p>输入关键词开始搜索</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-flex items-center gap-2 text-blue-500">
            <ButtonLoading />
            <span>正在搜索中...</span>
          </div>
        </div>
      )}

      {/* 发布弹窗 */}
      <AnimatePresence>
        {publishModal.open && publishModal.item && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
            onClick={() => setPublishModal({ open: false, item: null })}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 弹窗头部 */}
              <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">选择发布账号</h3>
                <button
                  onClick={() => setPublishModal({ open: false, item: null })}
                  className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              {/* 商品预览 */}
              <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/50 flex items-center gap-3">
                {publishModal.item.main_image && (
                  <img
                    src={publishModal.item.main_image}
                    alt=""
                    className="w-12 h-12 rounded-lg object-cover"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                    {publishModal.item.title}
                  </p>
                  <p className="text-sm text-red-500 font-bold">{publishModal.item.price}</p>
                </div>
              </div>

              {/* 账号列表 */}
              <div className="p-4 max-h-64 overflow-y-auto">
                {accountsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <ButtonLoading />
                    <span className="ml-2 text-sm text-slate-500">加载账号列表...</span>
                  </div>
                ) : accounts.length === 0 ? (
                  <div className="text-center py-8 text-sm text-slate-500">
                    暂无可用账号，请先添加或启用账号
                  </div>
                ) : (
                  <div className="space-y-2">
                    {accounts.map((account) => (
                      <label
                        key={account.id}
                        className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                          selectedAccountId === account.id
                            ? 'bg-blue-50 dark:bg-blue-900/30 ring-1 ring-blue-300 dark:ring-blue-700'
                            : 'bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="publish-account"
                          value={account.id}
                          checked={selectedAccountId === account.id}
                          onChange={() => setSelectedAccountId(account.id)}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                            {account.id}
                          </p>
                          {account.remark && (
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{account.remark}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* 底部按钮 */}
              <div className="flex gap-3 p-4 border-t border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setPublishModal({ open: false, item: null })}
                  className="flex-1 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmPublish}
                  disabled={!selectedAccountId || publishing}
                  className="flex-1 py-2 text-sm rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1"
                >
                  {publishing ? <ButtonLoading /> : <Send className="w-3.5 h-3.5" />}
                  {publishing ? '发布中...' : '确认发布'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
