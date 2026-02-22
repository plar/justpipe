import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function shortId(id: string, chars = 12): string {
  return id.length > chars ? id.slice(0, chars) + '...' : id
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString()
}

/** Format a scalar value for display — adds commas to numbers, preserves precision. */
export function formatScalar(v: unknown): string {
  if (v === null || v === undefined) return 'null'
  if (typeof v === 'number') {
    const s = String(v)
    if (s.includes('e')) return s // scientific notation — leave as-is
    const [intPart, decPart] = s.split('.')
    const formatted = intPart!.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    return decPart !== undefined ? `${formatted}.${decPart}` : formatted
  }
  return String(v)
}

const EPOCH_MIN = 946684800   // 2000-01-01
const EPOCH_MAX = 4102444800  // 2100-01-01

export function isEpochTimestamp(key: string, value: unknown): boolean {
  if (typeof value !== 'number') return false
  if (value < EPOCH_MIN || value > EPOCH_MAX) return false
  const k = key.toLowerCase()
  return k === 'timestamp' || k.endsWith('_at') || k.endsWith('_time')
}

export function formatEpoch(epoch: number): string {
  return new Date(epoch * 1000).toLocaleString()
}

export interface DisplayEntry {
  key: string
  value: string
  subtitle?: string
}

/** Format a key-value pair for display, detecting epoch timestamps automatically. */
export function formatEntry(key: string, value: unknown): DisplayEntry {
  if (isEpochTimestamp(key, value)) {
    return { key, value: formatEpoch(value as number), subtitle: formatScalar(value) }
  }
  return { key, value: formatScalar(value) }
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
