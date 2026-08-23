import { getScenario, type Evidence, type Scenario } from '@/data/scenarios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const caseService = {
  async getCase(id: string): Promise<Scenario> {
    return getScenario(id)
  },

  async getEvidence(id: string, side: 'customer' | 'merchant', scenarioId: string): Promise<Evidence[]> {
    const scenario = getScenario(scenarioId)
    return side === 'customer' ? scenario.customerEvidence : scenario.merchantEvidence
  },

  async submitCustomer(input: { scenarioId: string; caseId?: string; claim: string; evidenceIds: string[] }) {
    const scenario = getScenario(input.scenarioId)
    return {
      caseId: scenario.caseId,
      received: true,
      receivedAt: new Date().toISOString(),
    }
  },

  async submitMerchant(input: {
    scenarioId: string
    caseId?: string
    response: string
    evidenceIds: string[]
  }) {
    const scenario = getScenario(input.scenarioId)

    // Attempt to invoke backend worker API
    try {
      const res = await fetch(`${API_BASE}/api/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category_id: scenario.id,
          case_id: scenario.caseId,
          claim: scenario.claim,
          merchant_response: input.response,
          customer_evidence_ids: scenario.customerEvidence.map((e) => e.id),
          merchant_evidence_ids: input.evidenceIds,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        return {
          accepted: true,
          processing: true,
          caseId: scenario.caseId,
          liveDecision: data.decision,
        }
      }
    } catch {
      // Backend not running / fallback to local scenario data
    }

    return {
      accepted: true,
      processing: true,
      caseId: scenario.caseId,
      liveDecision: null,
    }
  },
}
