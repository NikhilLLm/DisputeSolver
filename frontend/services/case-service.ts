import { getScenario, type Evidence, type Scenario } from '@/data/scenarios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type ReasoningStatement = {
  statement: string
  weight: number
  source_tier: 'TIER_1_TELEMETRY' | 'TIER_2_COMMUNICATION' | 'TIER_3_ASSERTION'
  supports: 'cardholder' | 'merchant'
  evidence_ids?: string[]
}

export type DeterministicMetrics = {
  cardholder_score: number
  merchant_score: number
  cardholder_pct: string
  merchant_pct: string
  net_direction: string
  date_verifications_count: number
  amount_verifications_count: number
  misstatements_detected: number
}

export type BackendDecision = {
  case_id: string
  verdict: 'CARDHOLDER' | 'MERCHANT' | 'INSUFFICIENT_EVIDENCE'
  confidence_score: number
  confidence_band: string
  primary_reason: string
  policy_basis: string
  reasoning_statements: ReasoningStatement[]
  counterarguments_addressed: string[]
  executive_summary: string
  deterministic_metrics: DeterministicMetrics
  pipeline: string
  execution_time_seconds?: number
  run_at?: string
  source?: 'cache' | 'live_pipeline' | 'fallback_evaluator'
}

export const caseService = {
  async getCase(id: string): Promise<Scenario> {
    return getScenario(id)
  },

  async getEvidence(id: string, side: 'customer' | 'merchant', scenarioId: string): Promise<Evidence[]> {
    const scenario = getScenario(scenarioId)
    return side === 'customer' ? scenario.customerEvidence : scenario.merchantEvidence
  },

  async getDecision(caseId: string): Promise<BackendDecision | null> {
    try {
      const res = await fetch(`${API_BASE}/api/decisions/${caseId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        return data as BackendDecision
      }
    } catch {
      // Backend offline or not found
    }
    return null
  },

  async askCopilot(caseId: string, query: string): Promise<{ text: string; highlights?: string[] } | null> {
    try {
      const res = await fetch(`${API_BASE}/api/copilot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10000),
        body: JSON.stringify({ case_id: caseId, query }),
      })
      if (res.ok) {
        return await res.json()
      }
    } catch {
      // Fallback handled by caller
    }
    return null
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
  }): Promise<{ accepted: boolean; processing: boolean; caseId: string; liveDecision: BackendDecision | null }> {
    const scenario = getScenario(input.scenarioId)

    try {
      // 120-second timeout to allow full OCR, Neo4j Graph building and LLM reasoning
      const res = await fetch(`${API_BASE}/api/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(120000),
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
          processing: false,
          caseId: scenario.caseId,
          liveDecision: { ...(data.decision as BackendDecision), source: data.source },
        }
      }
    } catch (err) {
      console.warn('[case-service] Pipeline fetch error or timeout:', err)
      // If live run threw, check if decision was computed and saved
      const cached = await caseService.getDecision(scenario.caseId)
      if (cached) {
        return { accepted: true, processing: false, caseId: scenario.caseId, liveDecision: { ...cached, source: 'cache' } }
      }
    }

    return { accepted: true, processing: false, caseId: scenario.caseId, liveDecision: null }
  },
}
