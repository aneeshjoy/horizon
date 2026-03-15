import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDateTime(date: string | Date): string {
  return `${formatDate(date)} ${formatTime(date)}`
}

export function getDaysBetween(start: string | Date, end: string | Date): number {
  const s = typeof start === 'string' ? new Date(start) : start
  const e = typeof end === 'string' ? new Date(end) : end
  return Math.ceil((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24))
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-score-high'
  if (confidence >= 0.6) return 'text-score-medium'
  return 'text-score-low'
}

export function getClassificationColor(classification: string): string {
  switch (classification.toLowerCase()) {
    case 'commuter':
      return 'text-commuter-600 bg-commuter-50 border-commuter-200'
    case 'unknown':
      return 'text-unknown-600 bg-unknown-50 border-unknown-200'
    case 'suspicious':
      return 'text-suspicious-600 bg-suspicious-50 border-suspicious-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function getClassificationBadgeColor(classification: string): string {
  switch (classification.toLowerCase()) {
    case 'commuter':
      return 'bg-commuter-500 text-white hover:bg-commuter-600'
    case 'unknown':
      return 'bg-unknown-500 text-white hover:bg-unknown-600'
    case 'suspicious':
      return 'bg-suspicious-500 text-white hover:bg-suspicious-600'
    default:
      return 'bg-gray-500 text-white hover:bg-gray-600'
  }
}
