import { describe, it, expect } from 'vitest'
import { formatDateTime } from '../utils/date'

describe('date.ts - formatDateTime', () => {
  it('应当正确格式化合法日期对象和日期字符串', () => {
    const d = new Date('2026-06-12T19:57:09')
    const result = formatDateTime(d)
    expect(result).toContain('2026')
    expect(result).toContain('06')
  })

  it('传入空值时应当返回横杠占位符', () => {
    expect(formatDateTime(null)).toBe('-')
    expect(formatDateTime(undefined)).toBe('-')
    expect(formatDateTime('')).toBe('-')
  })

  it('传入非法日期时应当安全返回横杠占位符', () => {
    expect(formatDateTime('invalid-date-string')).toBe('-')
  })
})
