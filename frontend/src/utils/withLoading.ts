import type { Ref } from 'vue'

/**
 * Runs an async action while toggling a loading ref and capturing errors into
 * an error ref, mirroring the try/catch/finally block every store action
 * repeated by hand. Re-throws so callers can still react to failures.
 *
 * Pass `null` for `loading` when an action shouldn't drive a loading
 * indicator (e.g. a background refresh that already has its own spinner).
 */
export async function withLoading<T>(
  loading: Ref<boolean> | null,
  error: Ref<string | null>,
  fallbackMessage: string,
  action: () => Promise<T>
): Promise<T> {
  try {
    if (loading) loading.value = true
    error.value = null
    return await action()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : fallbackMessage
    throw err
  } finally {
    if (loading) loading.value = false
  }
}
