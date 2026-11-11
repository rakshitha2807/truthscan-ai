const environment = import.meta.env || {}
const configuredApiBaseUrl = environment.VITE_API_BASE_URL?.trim()
const timeoutValue = environment.VITE_API_TIMEOUT_MS?.trim()
const configuredTimeout = timeoutValue ? Number(timeoutValue) : 15000

export const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/+$/, '')
  : ''

if(!Number.isSafeInteger(configuredTimeout) || configuredTimeout <= 0) {
  throw new Error('VITE_API_TIMEOUT_MS must be a positive whole number of milliseconds.')
}

export const API_TIMEOUT_MS = configuredTimeout
