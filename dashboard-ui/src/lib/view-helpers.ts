export function statusBadgeVariant(s: string): 'success' | 'destructive' | 'warning' | 'muted' {
  switch (s) {
    case 'success':
      return 'success'
    case 'failed':
    case 'error':
      return 'destructive'
    case 'timeout':
    case 'running':
      return 'warning'
    default:
      return 'muted'
  }
}

export function statusForRate(rate: number): string {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'timeout'
  return 'failed'
}

/** Return a Tailwind text color class based on success rate thresholds. */
export function rateColorClass(rate: number): string {
  if (rate >= 90) return 'text-success'
  if (rate >= 70) return 'text-warning'
  return 'text-destructive'
}

/** Return a Tailwind text color class for a timing diff (positive = slower = bad). */
export function diffColorClass(diff: number, threshold = 0.001): string {
  if (diff > threshold) return 'text-destructive'
  if (diff < -threshold) return 'text-success'
  return 'text-muted-foreground'
}

/** Return a Tailwind background color class for a timing diff bar. */
export function diffBgClass(diff: number | null, threshold = 0.001): string {
  if (diff === null) return 'bg-info/70'
  if (diff > threshold) return 'bg-destructive/60'
  if (diff < -threshold) return 'bg-success/60'
  return 'bg-info/70'
}
