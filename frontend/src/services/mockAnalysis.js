const demoOutcomes = [
  {verdict: 'True', credibilityScore: 86},
  {verdict: 'False', credibilityScore: 28},
  {verdict: 'Misleading', credibilityScore: 54}
]
let nextOutcome = 0

export async function analyzeClaimWithMock(input) {
  if (!input.claim?.trim() && !input.image) {
    throw new Error('Enter a claim or attach an image before running the demo.')
  }

  await new Promise(resolve => setTimeout(resolve, 700))
  const outcome = demoOutcomes[nextOutcome++ % demoOutcomes.length]

  return {
    isDemo: true,
    claim: input.claim || input.image?.name || 'Image submission',
    ...outcome,
    explanation: `Sample ${outcome.verdict.toLowerCase()} explanation for previewing the interface. Demo verdicts rotate independently of your submission and are not based on claim research or source verification.`,
    evidence: [
      {
        title: 'Example evidence item',
        source: 'Demo source',
        summary: 'Sample evidence placeholder. A connected service would provide researched sources here.'
      },
      {
        title: 'Example context item',
        source: 'Demo source',
        summary: 'Sample context placeholder. No external sources were consulted for this demo.'
      }
    ]
  }
}
