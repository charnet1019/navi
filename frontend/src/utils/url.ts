const SAFE_PROTOCOLS = new Set(['http:', 'https:'])

/**
 * Returns the URL if it uses an allowed protocol (http/https), otherwise '#'.
 * Guards against javascript:/data: URI injection when rendering user-supplied
 * link URLs as href/src attributes.
 */
export function safeHref(url: string | null | undefined): string {
  if (!url) return '#'
  try {
    const parsed = new URL(url, window.location.origin)
    return SAFE_PROTOCOLS.has(parsed.protocol) ? url : '#'
  } catch {
    return '#'
  }
}
