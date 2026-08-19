import { getScenario, type Evidence, type Scenario } from '@/data/scenarios'

export const caseService = {
  async getCase(id: string): Promise<Scenario> { return getScenario(id) },
  async getEvidence(id: string, side: 'customer' | 'merchant', scenarioId: string): Promise<Evidence[]> {
    const scenario = getScenario(scenarioId)
    return side === 'customer' ? scenario.customerEvidence : scenario.merchantEvidence
  },
  async submitCustomer(input: { scenarioId: string; claim: string; evidenceIds: string[] }) {
    return { caseId: `CASE-${input.scenarioId.toUpperCase()}-1048`, received: true, receivedAt: new Date().toISOString() }
  },
  async submitMerchant(input: { scenarioId: string; response: string; evidenceIds: string[] }) {
    return { accepted: true, processing: true, caseId: `CASE-${input.scenarioId.toUpperCase()}-1048` }
  },
}
