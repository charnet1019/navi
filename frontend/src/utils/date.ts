/**
 * Format an ISO datetime string to YYYY-MM-DD HH:mm:ss.
 * Assumes the backend returns UTC+8 naive datetimes.
 */
export function formatDateTime(dateString: string): string {
  if (!dateString) return ''
  const d = new Date(dateString)
  if (isNaN(d.getTime())) return dateString
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
