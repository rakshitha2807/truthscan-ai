import { API_BASE_URL, API_TIMEOUT_MS } from '../config/api'
import { mockApi } from './mockApi'

export class ApiError extends Error {
  constructor(message, {status, response, cause} = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.response = response
    if(cause) this.cause = cause
  }
}

async function readResponseBody(response) {
  const text = await response.text()
  if(!text) return null

  const contentType = response.headers.get('content-type') || ''
  if(!contentType.toLowerCase().includes('json')) return text

  try {
    return JSON.parse(text)
  } catch (cause) {
    throw new ApiError(`API returned invalid JSON (HTTP ${response.status}).`, {
      status: response.status,
      cause
    })
  }
}

export async function requestApi(path, options = {}) {
  if(!API_BASE_URL) {
    throw new ApiError('Backend requests are disabled. Set VITE_API_BASE_URL after the backend contract is agreed.')
  }
  if(typeof path!=='string' || !path.trim()) {
    throw new ApiError('An API request path is required.')
  }

  const endpoint = `${API_BASE_URL}/${path.trim().replace(/^\/+/, '')}`
  const controller = new AbortController()
  const {signal: callerSignal, ...requestOptions} = options
  let timedOut = false
  const abortForCaller = () => controller.abort(callerSignal.reason)
  if(callerSignal?.aborted) abortForCaller()
  else callerSignal?.addEventListener('abort', abortForCaller, {once: true})
  const timeoutId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, API_TIMEOUT_MS)

  try {
    const headers = new Headers(options.headers)
    if(!headers.has('Accept')) headers.set('Accept', 'application/json')
    const response = await fetch(endpoint, {
      ...requestOptions,
      headers,
      signal: controller.signal
    })
    const responseBody = await readResponseBody(response)

    if(!response.ok) {
      const detail = typeof responseBody==='string'
        ? responseBody
        : responseBody?.message || responseBody?.error
      const message = detail
        ? `API request failed (HTTP ${response.status}): ${detail}`
        : `API request failed with status ${response.status}.`
      throw new ApiError(message, {status: response.status, response: responseBody})
    }

    return responseBody
  } catch (error) {
    if(error instanceof ApiError) throw error
    if(timedOut) {
      throw new ApiError(`API request timed out after ${API_TIMEOUT_MS} ms.`, {cause: error})
    }
    if(error?.name==='AbortError') {
      throw new ApiError('API request was cancelled.', {cause: error})
    }
    throw new ApiError(
      error instanceof Error ? `API request failed: ${error.message}` : 'API request failed.',
      {cause: error}
    )
  } finally {
    clearTimeout(timeoutId)
    callerSignal?.removeEventListener('abort', abortForCaller)
  }
}

// Keep demo providers active until endpoint and response contracts are supplied.
export function analyzeClaim(input) {
  return mockApi.analyzeClaim(input)
}

export function getEvidenceEntries() {
  return mockApi.getEvidenceEntries()
}

export function getAnalysisHistory() {
  return mockApi.getAnalysisHistory()
}

export function saveAnalysisHistory(history) {
  return mockApi.saveAnalysisHistory(history)
}

export function clearSavedAnalysisHistory() {
  return mockApi.clearSavedAnalysisHistory()
}
