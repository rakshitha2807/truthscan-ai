const STORAGE_KEY = 'truthscan.demo-analysis-history'

export function readAnalysisHistory() {
  const savedHistory = window.localStorage.getItem(STORAGE_KEY)
  if(savedHistory === null) return []

  let history
  try {
    history = JSON.parse(savedHistory)
  } catch {
    throw new Error('Saved demo history could not be read. Clear the browser storage entry to continue.')
  }

  if(!Array.isArray(history)) {
    throw new Error('Saved demo history has an invalid format.')
  }
  const isValidHistory = history.every(entry =>
    entry &&
    typeof entry.claim==='string' &&
    typeof entry.submittedAt==='string' &&
    !Number.isNaN(Date.parse(entry.submittedAt)) &&
    entry.analysis &&
    typeof entry.analysis.verdict==='string' &&
    Number.isFinite(entry.analysis.credibilityScore)
  )
  if(!isValidHistory) {
    throw new Error('Saved demo history contains an invalid record.')
  }
  return history
}

export function writeAnalysisHistory(history) {
  const serializableHistory = history.map(entry => {
    const {image, ...record} = entry
    const imageName = typeof image==='string' ? image : image?.name || entry.imageName
    return {...record, ...(imageName ? {imageName} : {})}
  })
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializableHistory))
}

export function clearAnalysisHistory() {
  window.localStorage.removeItem(STORAGE_KEY)
}
