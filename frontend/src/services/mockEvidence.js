const demoEvidence = [
  {
    id: 'who-climate-health',
    sourceName: 'World Health Organization',
    title: 'Climate change and health',
    url: 'https://www.who.int/news-room/fact-sheets/detail/climate-change-and-health',
    publicationDate: '2023-10-12',
    sourceType: 'Public health fact sheet',
    stance: 'supporting',
    credibilityScore: 96,
    credibilityLabel: 'High',
    summary: 'Synthetic summary for previewing a supporting evidence card. It does not represent a source review.'
  },
  {
    id: 'nasa-climate-evidence',
    sourceName: 'NASA',
    title: 'Evidence for climate change',
    url: 'https://science.nasa.gov/climate-change/evidence/',
    publicationDate: '2024-01-18',
    sourceType: 'Scientific overview',
    stance: 'supporting',
    credibilityScore: 94,
    credibilityLabel: 'High',
    summary: 'Synthetic summary for previewing source metadata. No findings were extracted from this page.'
  },
  {
    id: 'noaa-global-temperature',
    sourceName: 'NOAA Climate.gov',
    title: 'Climate change: global temperature',
    url: 'https://www.climate.gov/news-features/understanding-climate/climate-change-global-temperature',
    publicationDate: '2023-09-06',
    sourceType: 'Government data briefing',
    stance: 'supporting',
    credibilityScore: 92,
    credibilityLabel: 'High',
    summary: 'Placeholder text only. The relationship label and score are mock values for this demo.'
  },
  {
    id: 'ipcc-impacts-report',
    sourceName: 'Intergovernmental Panel on Climate Change',
    title: 'Climate Change 2022: Impacts, Adaptation and Vulnerability',
    url: 'https://www.ipcc.ch/report/ar6/wg2/',
    publicationDate: '2022-02-28',
    sourceType: 'Assessment report',
    stance: 'neutral',
    credibilityScore: 98,
    credibilityLabel: 'High',
    summary: 'Synthetic neutral entry demonstrating report-style metadata and source-type filtering.'
  },
  {
    id: 'gwpf-perspective',
    sourceName: 'Global Warming Policy Foundation',
    title: 'Sample alternative perspective on climate risk',
    url: 'https://www.thegwpf.org/',
    publicationDate: '2024-02-14',
    sourceType: 'Policy perspective',
    stance: 'contradicting',
    credibilityScore: 54,
    credibilityLabel: 'Limited',
    summary: 'Synthetic counterpoint entry for demonstrating the contradicting filter. This is not a source assessment.'
  },
  {
    id: 'who-health-context',
    sourceName: 'World Health Organization',
    title: 'Climate and health: additional context',
    url: 'https://www.who.int/health-topics/climate-change',
    publicationDate: '2024-04-22',
    sourceType: 'Topic overview',
    stance: 'neutral',
    credibilityScore: 96,
    credibilityLabel: 'High',
    summary: 'Synthetic neutral entry for demonstrating a second source type and an expandable evidence card.'
  }
]

export async function listEvidenceWithMock() {
  await new Promise(resolve => setTimeout(resolve, 350))
  return demoEvidence.map(entry => ({...entry, isDemo: true}))
}
