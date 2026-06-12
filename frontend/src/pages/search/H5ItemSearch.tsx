import { useState } from 'react'
import { Search, ShoppingBag, ExternalLink, Heart, MapPin, Sparkles } from 'lucide-react'
import { searchItems, collectToMaterial, SearchResultItem } from '@/api/search'
import { useUIStore } from '@/store/uiStore'
import { ButtonLoading } from '@/components/common/Loading'

export function H5ItemSearch() {
  const { addToast } = useUIStore()
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<SearchResultItem[]>([])

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!keyword.trim()) {
      addToast({ type: 'warning', message: '请输入搜索关键词' })
      return
    }

    addToast({ type: 'info', message: '正在检索闲鱼商品...' })
    try {
      setLoading(true)
      setResults([])
      const result = await searchItems(keyword.trim())
      if (result.success) {
        setResults(result.data || [])
        if ((result.data || []).length === 0) {
          addToast({ type: 'info', message: '未找到相关商品' })
        } else {
          addToast({ type: 'success', message: `找到 ${result.data.length} 件商品` })
        }
      }
    } catch {
      addToast({ type: 'error', message: '检索失败，请稍后重试' })
    } finally {
      setLoading(false)
    }
  }

  // 1. 采集到素材库
  const handleCollect = async (e: React.MouseEvent, item: SearchResultItem) => {
    e.preventDefault()
    e.stopPropagation()
    addToast({ type: 'info', message: '正在同步到素材库...' })
    try {
      const parsedPrice = parseFloat(item.price.replace(/[^\d.]/g, '')) || 0.0
      const result = await collectToMaterial({
        item_id: item.item_id,
        title: item.title,
        description: item.title,
        price: parsedPrice,
        images: item.main_image ? [item.main_image] : [],
        address: item.area || '',
        condition: '全新'
      })
      if (result.success) {
        addToast({ type: 'success', message: '采集成功！已存入本地素材库' })
      } else {
        addToast({ type: 'warning', message: result.message || '采集失败' })
      }
    } catch {
      addToast({ type: 'error', message: '接口调用异常，请重试' })
    }
  }

  // 2. 转草稿
  const handleToDraft = async (e: React.MouseEvent, item: SearchResultItem) => {
    e.preventDefault()
    e.stopPropagation()
    addToast({ type: 'info', message: '正在生成草稿...' })
    try {
      const parsedPrice = parseFloat(item.price.replace(/[^\d.]/g, '')) || 0.0
      const result = await collectToMaterial({
        item_id: item.item_id,
        title: item.title,
        description: item.title,
        price: parsedPrice,
        images: item.main_image ? [item.main_image] : [],
        address: item.area || '',
        condition: '全新'
      })
      if (result.success) {
        addToast({ type: 'success', message: '转草稿成功！已存入本地素材库' })
      } else {
        addToast({ type: 'warning', message: result.message || '转草稿失败' })
      }
    } catch {
      addToast({ type: 'error', message: '接口调用异常，请重试' })
    }
  }

  // 3. 发布
  const handlePublish = async (e: React.MouseEvent, item: SearchResultItem) => {
    e.preventDefault()
    e.stopPropagation()
    addToast({ type: 'info', message: '正在提取配置...' })
    try {
      const parsedPrice = parseFloat(item.price.replace(/[^\d.]/g, '')) || 0.0
      const result = await collectToMaterial({
        item_id: item.item_id,
        title: item.title,
        description: item.title,
        price: parsedPrice,
        images: item.main_image ? [item.main_image] : [],
        address: item.area || '',
        condition: '全新'
      })
      if (result.success) {
        addToast({ type: 'success', message: '发布配置成功！已保存至本地素材库' })
      } else {
        addToast({ type: 'warning', message: result.message || '发布配置准备失败' })
      }
    } catch {
      addToast({ type: 'error', message: '接口调用异常，请重试' })
    }
  }

  return (
    <div className="w-full max-w-md mx-auto px-4 pb-24 space-y-4">
      {/* Mobile Title Banner */}
      <div className="pt-2 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <Sparkles className="w-5 h-5 text-amber-500 fill-amber-500/20" />
            H5商品搜索/采集
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">专为移动端小屏优化的极速商品采集通道</p>
        </div>
        {results.length > 0 && (
          <span className="text-[10px] px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 font-medium rounded-full">
            已检出 {results.length} 件
          </span>
        )}
      </div>

      {/* Broad Mobile Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400 dark:text-slate-500 z-10" />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="输入商品名或链接检索..."
            className="w-full h-11 pl-11 pr-4 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-slate-200 transition-all shadow-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="h-11 px-5 bg-blue-600 active:bg-blue-700 text-white font-medium text-sm rounded-full flex items-center justify-center transition-colors shadow-md shadow-blue-500/10 min-w-[70px] active:scale-95"
        >
          {loading ? <ButtonLoading /> : '检索'}
        </button>
      </form>

      {/* Results Container: Mobile Vertical Layout */}
      {results.length > 0 ? (
        <div className="space-y-3">
          {results.map((item, index) => (
            <div
              key={item.item_id || index}
              onClick={() => window.open(item.item_url || `https://www.goofish.com/item?id=${item.item_id}`, '_blank')}
              className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-150 dark:border-slate-700 overflow-hidden shadow-sm flex flex-col active:bg-slate-50 dark:active:bg-slate-750 transition-colors"
            >
              {/* Product Info Row: Left Image, Right Text */}
              <div className="flex p-3 gap-3">
                {/* Product Image */}
                <div className="w-24 h-24 rounded-xl bg-slate-100 dark:bg-slate-700 relative overflow-hidden shrink-0">
                  {item.main_image ? (
                    <img
                      src={item.main_image}
                      alt={item.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-300 dark:text-slate-500">
                      <ShoppingBag className="w-8 h-8" />
                    </div>
                  )}
                  {/* Want Count Badge */}
                  {item.want_count && item.want_count > 0 ? (
                    <div className="absolute bottom-1 left-1 right-1 bg-black/40 backdrop-blur-[1px] rounded text-[9px] text-white py-0.5 px-1.5 flex items-center justify-center gap-0.5">
                      <Heart className="w-2 h-2 fill-red-500 text-red-500" />
                      {item.want_count} 想要
                    </div>
                  ) : null}
                </div>

                {/* Right Info Section */}
                <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm line-clamp-2 leading-snug">
                    {item.title}
                  </h3>
                  
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-base font-extrabold text-red-500">{item.price}</span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500 mt-1">
                    <span className="truncate max-w-[65%] font-medium">{item.seller_name || '未知卖家'}</span>
                    {item.area && (
                      <span className="flex items-center gap-0.5 max-w-[35%] truncate">
                        <MapPin className="w-2.5 h-2.5" />
                        {item.area}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons Row: Big touch areas for Mobile */}
              <div className="grid grid-cols-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50">
                <button
                  onClick={(e) => handleCollect(e, item)}
                  className="h-11 text-xs font-semibold text-blue-600 dark:text-blue-400 active:bg-blue-50 dark:active:bg-blue-900/20 border-r border-slate-100 dark:border-slate-700 flex items-center justify-center"
                >
                  采集
                </button>
                <button
                  onClick={(e) => handleToDraft(e, item)}
                  className="h-11 text-xs font-semibold text-amber-600 dark:text-amber-400 active:bg-amber-50 dark:active:bg-amber-900/20 border-r border-slate-100 dark:border-slate-700 flex items-center justify-center"
                >
                  转草稿
                </button>
                <button
                  onClick={(e) => handlePublish(e, item)}
                  className="h-11 text-xs font-semibold text-emerald-600 dark:text-emerald-400 active:bg-emerald-50 dark:active:bg-emerald-900/20 border-r border-slate-100 dark:border-slate-700 flex items-center justify-center"
                >
                  发布
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                  }}
                  className="h-11 text-xs font-semibold text-slate-500 dark:text-slate-400 active:bg-slate-100 dark:active:bg-slate-700 flex items-center justify-center"
                >
                  <a
                    href={item.item_url || `https://www.goofish.com/item?id=${item.item_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full h-full flex items-center justify-center"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        !loading && (
          <div className="text-center py-16 text-slate-400 dark:text-slate-500">
            <ShoppingBag className="w-16 h-16 text-slate-200 dark:text-slate-750 mx-auto mb-4" />
            <p className="text-sm">暂无数据，输入关键词或商品链接搜索</p>
          </div>
        )
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-flex items-center gap-2 text-blue-500 font-medium text-sm">
            <ButtonLoading />
            <span>检索闲鱼数据中...</span>
          </div>
        </div>
      )}
    </div>
  )
}
