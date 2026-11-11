import { clearAnalysisHistory, readAnalysisHistory, writeAnalysisHistory } from './mockHistory'
import { listEvidenceWithMock } from './mockEvidence'
import { analyzeClaimWithMock } from './mockAnalysis'

export const mockApi = Object.freeze({
  analyzeClaim: analyzeClaimWithMock,
  getEvidenceEntries: listEvidenceWithMock,
  getAnalysisHistory: readAnalysisHistory,
  saveAnalysisHistory: writeAnalysisHistory,
  clearSavedAnalysisHistory: clearAnalysisHistory
})
