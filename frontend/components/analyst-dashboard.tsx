'use client'

import { useMemo, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Building2,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  CreditCard,
  FileText,
  Filter,
  GitBranch,
  Layers,
  MessageSquare,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UserCheck,
  UserRound,
  X,
  XCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { scenarios, type Scenario, type Evidence } from '@/data/scenarios'

const cx = (...classes: Array<string | false | undefined>) => classes.filter(Boolean).join(' ')

type CaseReviewStatus = 'PENDING' | 'AI_ACCEPTED' | 'OVERRIDDEN'

type CaseReviewState = {
  status: CaseReviewStatus
  decidedAt?: string
  analystNote?: string
  overrideOutcome?: string
}

type ChatMessage = {
  id: string
  sender: 'analyst' | 'ai'
  text: string
  timestamp: string
  highlights?: string[]
}

// Generate grounded response for the AI Graph Chat Assistant based on scenario context
function generateGraphAiResponse(query: string, scenario: Scenario): { text: string; highlights: string[] } {
  const q = query.toLowerCase()

  if (q.includes('node') || q.includes('graph') || q.includes('topology') || q.includes('relation')) {
    const nodeNames = scenario.graph.nodes.map((n) => `${n.label} (${n.kind})`).join(', ')
    return {
      text: `The 5-Layer Knowledge Graph for Case ${scenario.caseId} contains ${scenario.graph.nodes.length} connected entities and ${scenario.graph.edges.length} directed relational bridges:\n\n• Nodes: ${nodeNames}\n\nThis graph structures raw document extractions into a topological representation where carrier telemetry, policy terms, and parties are linked deterministically.`,
      highlights: scenario.graph.nodes.map((n) => n.label),
    }
  }

  if (q.includes('why') || q.includes('reason') || q.includes('verdict') || q.includes('favor') || q.includes('win') || q.includes('decision')) {
    return {
      text: `AI Recommendation: ${scenario.decision.outcome} (${scenario.decision.confidence} confidence).\n\nPrimary Decisive Factor: ${scenario.decision.primaryReason || scenario.decision.summary}\n\nEvidence Evaluation:\n${scenario.reasoning.signals.map((s) => `• ${s}`).join('\n')}`,
      highlights: [scenario.decision.outcome, scenario.decision.confidence],
    }
  }

  if (q.includes('date') || q.includes('timeline') || q.includes('gap') || q.includes('sla') || q.includes('time')) {
    return {
      text: `Timeline & SLA Audit for Case ${scenario.caseId}:\n\n• Transaction Date: ${scenario.date}\n• Resolution Cycle: ${scenario.resolutionTime.cycleDays} Days (vs ${scenario.resolutionTime.industryBaselineDays}d Industry SLA)\n• Time Saved: ${scenario.resolutionTime.timeSavedDays} Days (${scenario.resolutionTime.reductionPct} efficiency gain)\n• AI Processing Latency: ${scenario.resolutionTime.aiLatencySeconds}s\n\nAll date claims were verified against card scheme regulations.`,
      highlights: [`${scenario.resolutionTime.cycleDays} Days Resolution`, `${scenario.resolutionTime.timeSavedDays} Days Saved`],
    }
  }

  if (q.includes('policy') || q.includes('rule') || q.includes('scheme') || q.includes('visa') || q.includes('mastercard')) {
    return {
      text: `Applicable Dispute Policy & Rules:\n\n• Reason Code: ${scenario.reasonCode} (${scenario.category})\n• Governing Basis: ${scenario.decision.policyBasis || 'Card Scheme Dispute Regulations'}\n• Core Evaluation: "${scenario.reasoning.question}"`,
      highlights: [scenario.reasonCode, scenario.category],
    }
  }

  if (q.includes('telemetry') || q.includes('evidence') || q.includes('tier') || q.includes('document')) {
    const customerDocs = scenario.customerEvidence.map((e) => `• [${e.tier?.replace('TIER_', 'Tier ') || 'Tier 2'}]: ${e.name} — ${e.detail}`).join('\n')
    const merchantDocs = scenario.merchantEvidence.map((e) => `• [${e.tier?.replace('TIER_', 'Tier ') || 'Tier 2'}]: ${e.name} — ${e.detail}`).join('\n')
    return {
      text: `Evidentiary Hierarchy Audit:\n\nCardholder Evidence:\n${customerDocs}\n\nMerchant Defense Records:\n${merchantDocs}\n\nTier-1 Telemetry (tamper-resistant 3rd-party data) is weighted at 1.0, Tier-2 Records at 0.7, and Tier-3 Assertions at 0.35 in our deterministic formula.`,
      highlights: ['Tier 1 Telemetry', 'Tier 2 Record', 'Tier 3 Assertion'],
    }
  }

  // Fallback grounded answer
  return {
    text: `Analysis for Case ${scenario.caseId} (${scenario.category}):\n\n${scenario.decision.summary}\n\nKey Supporting Factors:\n${scenario.decision.factors.map((f) => `• ${f}`).join('\n')}\n\nYou can query graph nodes, date gap checks, evidence tiers, or policy reason codes.`,
    highlights: scenario.decision.factors,
  }
}

export function AnalystDashboard({
  onNavigateToPlayground,
}: {
  onNavigateToPlayground?: (scenarioId?: string) => void
}) {
  // Case review state storage
  const [reviews, setReviews] = useState<Record<string, CaseReviewState>>({
    category_0_item_not_recieved: { status: 'AI_ACCEPTED', decidedAt: 'Aug 29, 2026 10:15 AM' },
    category_1_not_as_described: { status: 'PENDING' },
    category_2_fraudulent: { status: 'PENDING' },
    category_3_duplicate: { status: 'AI_ACCEPTED', decidedAt: 'Aug 29, 2026 09:40 AM' },
    category_4_refund: { status: 'PENDING' },
    category_5_subscription: { status: 'PENDING' },
    category_6_error: { status: 'PENDING' },
    category_7_weak: { status: 'PENDING' },
  })

  // Selected case for deep-dive investigation
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const selectedScenario = useMemo(
    () => (selectedCaseId ? scenarios.find((s) => s.id === selectedCaseId) || null : null),
    [selectedCaseId]
  )

  // Filters & search
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'PENDING' | 'AI_ACCEPTED' | 'OVERRIDDEN'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Override dialog state
  const [showOverrideModal, setShowOverrideModal] = useState(false)
  const [overrideOutcome, setOverrideOutcome] = useState('Cardholder Refund (Manual Override)')
  const [overrideNote, setOverrideNote] = useState('')

  // Graph Chat Assistant state
  const [chatMessages, setChatMessages] = useState<Record<string, ChatMessage[]>>({})
  const [chatInput, setChatInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Filtered scenario list
  const filteredScenarios = useMemo(() => {
    return scenarios.filter((s) => {
      const state = reviews[s.id] || { status: 'PENDING' }
      if (filterStatus !== 'ALL' && state.status !== filterStatus) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        return (
          s.caseId.toLowerCase().includes(q) ||
          s.category.toLowerCase().includes(q) ||
          s.customer.toLowerCase().includes(q) ||
          s.merchant.toLowerCase().includes(q) ||
          s.decision.outcome.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [filterStatus, searchQuery, reviews])

  // Summary Metrics
  const metrics = useMemo(() => {
    const total = scenarios.length
    let pending = 0
    let accepted = 0
    let overridden = 0
    Object.values(reviews).forEach((r) => {
      if (r.status === 'PENDING') pending++
      if (r.status === 'AI_ACCEPTED') accepted++
      if (r.status === 'OVERRIDDEN') overridden++
    })
    return { total, pending, accepted, overridden }
  }, [reviews])

  // Handle Accept AI Decision
  const handleAcceptDecision = (scenarioId: string) => {
    setReviews((prev) => ({
      ...prev,
      [scenarioId]: {
        status: 'AI_ACCEPTED',
        decidedAt: new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }),
        analystNote: 'AI Verdict validated and approved by Fraud Analyst.',
      },
    }))
  }

  // Handle Re-open / reset review to PENDING
  const handleReopen = (scenarioId: string) => {
    setReviews((prev) => ({
      ...prev,
      [scenarioId]: {
        status: 'PENDING',
      },
    }))
  }

  // Handle Override Decision
  const handleSaveOverride = () => {
    if (!selectedCaseId) return
    setReviews((prev) => ({
      ...prev,
      [selectedCaseId]: {
        status: 'OVERRIDDEN',
        decidedAt: new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }),
        overrideOutcome,
        analystNote: overrideNote || 'Manual override applied based on analyst review.',
      },
    }))
    setShowOverrideModal(false)
    setOverrideNote('')
  }

  // Active chat conversation for current scenario
  const currentChat = useMemo(() => {
    if (!selectedCaseId) return []
    if (!chatMessages[selectedCaseId]) {
      const initial: ChatMessage = {
        id: 'init-1',
        sender: 'ai',
        text: `Hello Analyst. I have mapped the 5-layer Knowledge Graph for Case ${selectedScenario?.caseId}. I can explain our deterministic weighting, query graph relationships, or verify specific evidence tiers. What would you like to investigate?`,
        timestamp: 'Just now',
      }
      return [initial]
    }
    return chatMessages[selectedCaseId]
  }, [selectedCaseId, chatMessages, selectedScenario])

  // Handle Send Chat
  const handleSendChat = (textToSend?: string) => {
    const query = (textToSend || chatInput).trim()
    if (!query || !selectedScenario || !selectedCaseId) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'analyst',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const updated = [...(chatMessages[selectedCaseId] || currentChat), userMsg]
    setChatMessages((prev) => ({ ...prev, [selectedCaseId]: updated }))
    setChatInput('')
    setIsTyping(true)

    setTimeout(() => {
      const response = generateGraphAiResponse(query, selectedScenario)
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: response.text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        highlights: response.highlights,
      }
      setChatMessages((prev) => ({
        ...prev,
        [selectedCaseId]: [...(prev[selectedCaseId] || updated), aiMsg],
      }))
      setIsTyping(false)
    }, 600)
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top Header Bar */}
      <header className="border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-20">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-5 py-3.5 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-xs">
              <Sparkles className="size-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-400">
                  DisputeSolver Ops
                </span>
                <span className="rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
                  Analyst Decision Center
                </span>
              </div>
              <h1 className="text-lg font-bold tracking-tight text-foreground">
                Dispute Review & Knowledge Graph Copilot
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {onNavigateToPlayground && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigateToPlayground(selectedCaseId || undefined)}
                className="gap-1.5 text-xs font-semibold"
              >
                <Layers className="size-3.5 text-muted-foreground" />
                Switch to Intake Playground
              </Button>
            )}
            <div className="flex items-center gap-1.5 rounded-xl border border-border bg-muted/30 px-3 py-1.5 text-xs">
              <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-foreground">Tri-Agent Pipeline Online</span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-5 py-6 lg:px-8">
        {/* KPI Ribbon */}
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:gap-4">
          <div className="rounded-2xl border border-border bg-card p-4 shadow-xs">
            <p className="text-xs font-semibold text-muted-foreground">Total Ingested Disputes</p>
            <p className="mt-1 text-2xl font-bold text-foreground">{metrics.total}</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">8 Test Scenarios across 8 Categories</p>
          </div>

          <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-4 shadow-xs dark:border-amber-900/40 dark:bg-amber-950/20">
            <p className="text-xs font-semibold text-amber-800 dark:text-amber-300">Pending Analyst Review</p>
            <p className="mt-1 text-2xl font-bold text-amber-900 dark:text-amber-100">{metrics.pending}</p>
            <p className="mt-0.5 text-[11px] text-amber-700 dark:text-amber-400">Requires validation or approval</p>
          </div>

          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-xs dark:border-emerald-900/40 dark:bg-emerald-950/20">
            <p className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">AI Decisions Accepted</p>
            <p className="mt-1 text-2xl font-bold text-emerald-900 dark:text-emerald-100">{metrics.accepted}</p>
            <p className="mt-0.5 text-[11px] text-emerald-700 dark:text-emerald-400">Validated with 0-touch SLA</p>
          </div>

          <div className="rounded-2xl border border-purple-200 bg-purple-50/50 p-4 shadow-xs dark:border-purple-900/40 dark:bg-purple-950/20">
            <p className="text-xs font-semibold text-purple-800 dark:text-purple-300">Analyst Overrides</p>
            <p className="mt-1 text-2xl font-bold text-purple-900 dark:text-purple-100">{metrics.overridden}</p>
            <p className="mt-0.5 text-[11px] text-purple-700 dark:text-purple-400">Human-in-the-loop adjustments</p>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-[260px] flex-1 sm:flex-none">
              <Search className="absolute left-3 top-2.5 size-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search case ID, customer, merchant..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-full rounded-xl border border-input bg-card pl-9 pr-3 text-xs outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div className="flex items-center rounded-xl border border-border bg-card p-1 text-xs">
              {(['ALL', 'PENDING', 'AI_ACCEPTED', 'OVERRIDDEN'] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => setFilterStatus(status)}
                  className={cx(
                    'rounded-lg px-2.5 py-1 font-medium transition',
                    filterStatus === status
                      ? 'bg-primary text-primary-foreground shadow-2xs font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {status === 'ALL'
                    ? 'All Cases'
                    : status === 'PENDING'
                    ? 'Pending'
                    : status === 'AI_ACCEPTED'
                    ? 'Approved'
                    : 'Overridden'}
                </button>
              ))}
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            Showing <strong>{filteredScenarios.length}</strong> of {scenarios.length} cases
          </p>
        </div>

        {/* Case List Table */}
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3.5">Case ID & Reason</th>
                  <th className="px-4 py-3.5">Disputed Amount</th>
                  <th className="px-4 py-3.5">Parties (Cardholder / Merchant)</th>
                  <th className="px-4 py-3.5">AI Recommended Verdict</th>
                  <th className="px-4 py-3.5">Confidence & SLA</th>
                  <th className="px-4 py-3.5">Review Status</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredScenarios.map((item) => {
                  const state = reviews[item.id] || { status: 'PENDING' }
                  const isSelected = selectedCaseId === item.id

                  return (
                    <tr
                      key={item.id}
                      onClick={() => setSelectedCaseId(item.id)}
                      className={cx(
                        'cursor-pointer transition-colors hover:bg-muted/30',
                        isSelected && 'bg-primary/5 dark:bg-primary/10'
                      )}
                    >
                      {/* Case ID & Reason */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-foreground">{item.caseId}</span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                            {item.reasonCode}
                          </span>
                        </div>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">{item.category}</p>
                      </td>

                      {/* Disputed Amount */}
                      <td className="px-4 py-3.5 font-bold text-foreground">
                        {item.amount} {item.currency}
                      </td>

                      {/* Parties */}
                      <td className="px-4 py-3.5">
                        <p className="font-medium text-foreground">{item.customer}</p>
                        <p className="text-[11px] text-muted-foreground">vs {item.merchant}</p>
                      </td>

                      {/* AI Verdict */}
                      <td className="px-4 py-3.5 max-w-xs">
                        <div className="flex items-center gap-1.5 font-semibold text-foreground">
                          {item.decision.outcome.toLowerCase().includes('merchant') ? (
                            <ShieldCheck className="size-3.5 text-emerald-600 shrink-0" />
                          ) : (
                            <CheckCircle2 className="size-3.5 text-blue-600 shrink-0" />
                          )}
                          <span className="truncate">{item.decision.outcome}</span>
                        </div>
                        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                          {item.decision.primaryReason || item.decision.summary}
                        </p>
                      </td>

                      {/* Confidence & SLA */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <span className="rounded-md bg-emerald-100 px-2 py-0.5 font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            {item.decision.confidence}
                          </span>
                          <span className="text-[11px] text-muted-foreground">
                            {item.resolutionTime.cycleDays}d cycle
                          </span>
                        </div>
                      </td>

                      {/* Review Status */}
                      <td className="px-4 py-3.5">
                        {state.status === 'AI_ACCEPTED' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            <Check className="size-3" /> Approved
                          </span>
                        ) : state.status === 'OVERRIDDEN' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 font-semibold text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                            <UserCheck className="size-3" /> Overridden
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 font-semibold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                            <AlertCircle className="size-3" /> Pending Review
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          {state.status === 'PENDING' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleAcceptDecision(item.id)}
                              className="h-7 gap-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/50"
                            >
                              <Check className="size-3" /> Accept AI
                            </Button>
                          )}

                          <Button
                            size="sm"
                            variant={isSelected ? 'default' : 'secondary'}
                            onClick={() => setSelectedCaseId(item.id)}
                            className="h-7 gap-1 text-[11px] font-semibold"
                          >
                            <MessageSquare className="size-3" /> Dig In & Chat
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Deep-Dive Investigation & AI Graph Chat Workspace */}
        {selectedScenario && (
          <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-sm">
            {/* Dossier Header with Live Review Status Badge */}
            <div className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-primary">
                    Deep-Dive Case Investigation Dossier
                  </span>
                  <span className="rounded-md bg-primary/10 px-2 py-0.5 text-xs font-bold text-primary font-mono">
                    {selectedScenario.caseId}
                  </span>
                  <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                    {selectedScenario.reasonCode} ({selectedScenario.category})
                  </span>
                  <span className="rounded-md bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                    ⚡ {selectedScenario.resolutionTime.cycleDays} Days Resolution ({selectedScenario.resolutionTime.timeSavedDays}d Saved)
                  </span>

                  {/* Dynamic Status Badge directly in the header line */}
                  {(reviews[selectedScenario.id]?.status || 'PENDING') === 'AI_ACCEPTED' ? (
                    <span className="inline-flex items-center gap-1 rounded-md bg-emerald-600 text-white px-2.5 py-0.5 text-xs font-bold shadow-2xs">
                      <Check className="size-3" /> Case Approved (AI Ratified)
                    </span>
                  ) : (reviews[selectedScenario.id]?.status || 'PENDING') === 'OVERRIDDEN' ? (
                    <span className="inline-flex items-center gap-1 rounded-md bg-purple-600 text-white px-2.5 py-0.5 text-xs font-bold shadow-2xs">
                      <UserCheck className="size-3" /> Manually Overridden
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 border border-amber-300 text-amber-800 dark:bg-amber-950/60 dark:border-amber-800 dark:text-amber-300 px-2.5 py-0.5 text-xs font-bold">
                      <AlertCircle className="size-3" /> Awaiting Analyst Sign-off
                    </span>
                  )}
                </div>
                <h2 className="mt-1.5 text-2xl font-bold tracking-tight text-foreground">
                  {selectedScenario.label}
                </h2>
              </div>

              {/* Action Bar */}
              <div className="flex flex-wrap items-center gap-2">
                {(reviews[selectedScenario.id]?.status || 'PENDING') === 'AI_ACCEPTED' ? (
                  <>
                    <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mr-1">
                      <CheckCircle2 className="size-4" /> Decision Executed
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowOverrideModal(true)}
                      className="gap-1 text-xs text-purple-700 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/40"
                    >
                      <UserCheck className="size-3.5" /> Change to Override
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleReopen(selectedScenario.id)}
                      className="gap-1 text-xs text-muted-foreground hover:text-foreground"
                    >
                      <RotateCcw className="size-3" /> Re-open Case
                    </Button>
                  </>
                ) : (reviews[selectedScenario.id]?.status || 'PENDING') === 'OVERRIDDEN' ? (
                  <>
                    <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 flex items-center gap-1 mr-1">
                      <UserCheck className="size-4" /> Override Logged
                    </span>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handleAcceptDecision(selectedScenario.id)}
                      className="gap-1 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                      <Check className="size-3.5" /> Approve AI Instead
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowOverrideModal(true)}
                      className="gap-1 text-xs"
                    >
                      Edit Override Note
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleReopen(selectedScenario.id)}
                      className="gap-1 text-xs text-muted-foreground"
                    >
                      <RotateCcw className="size-3" /> Re-open
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowOverrideModal(true)}
                      className="gap-1.5 text-xs font-semibold text-purple-700 dark:text-purple-400"
                    >
                      <UserCheck className="size-3.5" />
                      Override AI Decision
                    </Button>

                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handleAcceptDecision(selectedScenario.id)}
                      className="gap-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                    >
                      <Check className="size-3.5" />
                      Accept & Approve Verdict
                    </Button>
                  </>
                )}

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedCaseId(null)}
                  className="size-8 p-0"
                >
                  <X className="size-4" />
                </Button>
              </div>
            </div>

            {/* Main Investigation Split */}
            <div className="mt-6 grid gap-6 lg:grid-cols-12">
              {/* Left Column */}
              <div className="flex flex-col gap-5 lg:col-span-7">
                {/* Dynamic Verdict & Execution Record Box */}
                {(reviews[selectedScenario.id]?.status || 'PENDING') === 'AI_ACCEPTED' ? (
                  <div className="rounded-2xl border-2 border-emerald-500/80 bg-emerald-50/90 p-5 shadow-sm dark:border-emerald-700/80 dark:bg-emerald-950/50 transition-all">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-emerald-200/80 pb-3 dark:border-emerald-800/60">
                      <div className="flex items-center gap-2.5">
                        <span className="flex size-7 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
                          <CheckCircle2 className="size-4" />
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-900 dark:text-emerald-300">
                              Official Resolution Record
                            </span>
                            <span className="rounded-md bg-emerald-600 px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                              Approved & Executed
                            </span>
                          </div>
                          <p className="text-[11px] text-emerald-800/80 dark:text-emerald-400">
                            Ratified on {reviews[selectedScenario.id]?.decidedAt || 'Aug 29, 2026'} by Operations Analyst
                          </p>
                        </div>
                      </div>
                      <span className="rounded-xl border border-emerald-300 bg-white/90 px-3 py-1 text-xs font-bold text-emerald-900 dark:border-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-100">
                        {selectedScenario.decision.confidence} Confidence Score
                      </span>
                    </div>

                    <div className="mt-3.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                        Final Binding Outcome:
                      </p>
                      <h3 className="mt-0.5 text-lg font-bold text-emerald-950 dark:text-emerald-50">
                        {selectedScenario.decision.outcome}
                      </h3>
                      <p className="mt-1 text-xs leading-5 text-emerald-900/90 dark:text-emerald-200/90">
                        {selectedScenario.decision.summary}
                      </p>
                    </div>

                    <div className="mt-3.5 grid gap-2 rounded-xl border border-emerald-200/90 bg-white/70 p-3 text-xs dark:border-emerald-900/70 dark:bg-emerald-950/70 sm:grid-cols-3">
                      <div>
                        <span className="text-[10px] font-bold uppercase text-muted-foreground">Governing Policy</span>
                        <p className="font-semibold text-foreground">{selectedScenario.decision.policyBasis || 'Card Scheme Dispute Regulations'}</p>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase text-muted-foreground">Disputed Amount</span>
                        <p className="font-semibold text-foreground">{selectedScenario.amount} {selectedScenario.currency}</p>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase text-muted-foreground">Representment Status</span>
                        <p className="font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                          <Check className="size-3" /> Transmitted to Card Scheme
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (reviews[selectedScenario.id]?.status || 'PENDING') === 'OVERRIDDEN' ? (
                  <div className="rounded-2xl border-2 border-purple-500/80 bg-purple-50/90 p-5 shadow-sm dark:border-purple-700/80 dark:bg-purple-950/50 transition-all">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-purple-200/80 pb-3 dark:border-purple-800/60">
                      <div className="flex items-center gap-2.5">
                        <span className="flex size-7 items-center justify-center rounded-xl bg-purple-600 text-white shadow-xs">
                          <UserCheck className="size-4" />
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-900 dark:text-purple-300">
                              Official Resolution Record
                            </span>
                            <span className="rounded-md bg-purple-600 px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                              Manual Override Applied
                            </span>
                          </div>
                          <p className="text-[11px] text-purple-800/80 dark:text-purple-400">
                            Logged on {reviews[selectedScenario.id]?.decidedAt || 'Aug 29, 2026'} by Operations Analyst
                          </p>
                        </div>
                      </div>
                      <span className="rounded-xl border border-purple-300 bg-white/90 px-3 py-1 text-xs font-bold text-purple-900 dark:border-purple-800 dark:bg-purple-900/60 dark:text-purple-100">
                        Human Decision
                      </span>
                    </div>

                    <div className="mt-3.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300">
                        Overridden Final Outcome:
                      </p>
                      <h3 className="mt-0.5 text-lg font-bold text-purple-950 dark:text-purple-50">
                        {reviews[selectedScenario.id]?.overrideOutcome || 'Manual Override Outcome'}
                      </h3>
                      <div className="mt-2.5 rounded-xl border border-purple-200/90 bg-white/70 p-3 dark:border-purple-900/70 dark:bg-purple-950/70">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300">
                          Analyst Evidentiary Justification:
                        </p>
                        <p className="mt-1 text-xs text-foreground leading-5">
                          "{reviews[selectedScenario.id]?.analystNote || 'Manual override applied based on evidentiary review of graph telemetry.'}"
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 text-xs text-muted-foreground flex flex-wrap items-center gap-2">
                      <span>Original AI Recommendation:</span>
                      <span className="font-semibold line-through text-muted-foreground">{selectedScenario.decision.outcome}</span>
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">{selectedScenario.decision.confidence} AI score</span>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/20">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                          AI Synthesized Verdict (Pending Sign-off)
                        </span>
                        <span className="rounded bg-amber-200 px-1.5 py-0.5 text-[9px] font-bold text-amber-900 dark:bg-amber-900 dark:text-amber-200">
                          Awaiting Action
                        </span>
                      </div>
                      <span className="rounded bg-emerald-200/80 px-2 py-0.5 text-xs font-bold text-emerald-900 dark:bg-emerald-900 dark:text-emerald-200">
                        {selectedScenario.decision.confidence} Confidence Score
                      </span>
                    </div>
                    <h3 className="mt-1 text-base font-bold text-emerald-950 dark:text-emerald-100">
                      {selectedScenario.decision.outcome}
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground leading-5">
                      {selectedScenario.decision.summary}
                    </p>
                  </div>
                )}

                {/* 5-Layer Knowledge Graph Explorer */}
                <div className="rounded-xl border border-border bg-muted/30 p-4">
                  <div className="flex items-center justify-between border-b border-border/60 pb-2">
                    <div className="flex items-center gap-2">
                      <GitBranch className="size-4 text-primary" />
                      <h4 className="text-xs font-bold text-foreground">5-Layer Knowledge Graph Topology</h4>
                    </div>
                    <span className="text-[11px] text-muted-foreground">
                      {selectedScenario.graph.nodes.length} Entity Nodes · {selectedScenario.graph.edges.length} Directed Relational Bridges
                    </span>
                  </div>

                  {/* Visual Node Chain */}
                  <div className="mt-4 flex flex-wrap items-center justify-center gap-2 py-3 overflow-x-auto">
                    {selectedScenario.graph.nodes.map((node, index) => (
                      <div key={node.id} className="flex items-center gap-2">
                        <div className="rounded-xl border border-border bg-card px-3 py-2 text-center shadow-xs">
                          <p className="text-[9px] font-bold uppercase tracking-wider text-primary">{node.kind}</p>
                          <p className="mt-0.5 text-xs font-semibold text-foreground">{node.label}</p>
                        </div>
                        {index < selectedScenario.graph.nodes.length - 1 && (
                          <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidentiary Hierarchy Table */}
                <div className="rounded-xl border border-border bg-card p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <h4 className="text-xs font-bold text-foreground">Evidentiary Hierarchy Breakdown</h4>
                    <span className="text-[10px] font-mono text-muted-foreground">Hierarchy of Truth: Tier 1 &gt; Tier 2 &gt; Tier 3</span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 text-xs">
                    {/* Cardholder Column */}
                    <div className="rounded-lg border border-border/80 bg-muted/20 p-3">
                      <p className="font-bold text-[11px] text-primary uppercase tracking-wider">
                        Cardholder Evidence ({selectedScenario.customerEvidence.length})
                      </p>
                      <div className="mt-2 flex flex-col gap-2">
                        {selectedScenario.customerEvidence.map((e) => (
                          <div key={e.id} className="rounded-md border border-border/60 bg-card p-2 text-[11px]">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-foreground">{e.name}</span>
                              <span className="rounded bg-muted px-1.5 text-[9px] font-medium text-muted-foreground">
                                {e.tier?.replace('TIER_', 'Tier ') || 'Tier 2'}
                              </span>
                            </div>
                            <p className="mt-0.5 text-muted-foreground">{e.detail}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Merchant Column */}
                    <div className="rounded-lg border border-border/80 bg-muted/20 p-3">
                      <p className="font-bold text-[11px] text-amber-700 dark:text-amber-400 uppercase tracking-wider">
                        Merchant Telemetry & Proof ({selectedScenario.merchantEvidence.length})
                      </p>
                      <div className="mt-2 flex flex-col gap-2">
                        {selectedScenario.merchantEvidence.map((e) => (
                          <div key={e.id} className="rounded-md border border-border/60 bg-card p-2 text-[11px]">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-foreground">{e.name}</span>
                              <span className={cx(
                                'rounded px-1.5 text-[9px] font-medium',
                                e.tier === 'TIER_1_TELEMETRY'
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                                  : 'bg-muted text-muted-foreground'
                              )}>
                                {e.tier?.replace('TIER_', 'Tier ') || 'Tier 2'}
                              </span>
                            </div>
                            <p className="mt-0.5 text-muted-foreground">{e.detail}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Policy & Deterministic Factors */}
                <div className="rounded-xl border border-border bg-muted/20 p-4 text-xs">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Decisive Factors & Policy Basis</p>
                  <p className="mt-1 font-semibold text-foreground">{selectedScenario.decision.policyBasis || 'Card Scheme Dispute Regulations'}</p>
                  <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
                    {selectedScenario.decision.factors.map((factor) => (
                      <li key={factor} className="flex items-start gap-1.5 rounded-lg border border-border/60 bg-card p-2 text-[11px]">
                        <Check className="mt-0.5 size-3.5 shrink-0 text-emerald-600" />
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Right Column: Interactive AI Graph Copilot Chat */}
              <div className="flex flex-col rounded-2xl border border-border bg-card shadow-xs lg:col-span-5 h-[680px]">
                {/* Chat Header */}
                <div className="flex items-center justify-between border-b border-border p-4">
                  <div className="flex items-center gap-2.5">
                    <div className="flex size-8 items-center justify-center rounded-xl bg-indigo-600 text-white">
                      <Bot className="size-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-foreground">AI Graph Copilot</p>
                      <p className="text-[10px] text-muted-foreground">Grounded in Case {selectedScenario.caseId} Topology</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (selectedCaseId) {
                        setChatMessages((prev) => ({ ...prev, [selectedCaseId]: [] }))
                      }
                    }}
                    className="h-7 text-[10px] text-muted-foreground hover:text-foreground"
                  >
                    <RefreshCw className="mr-1 size-3" /> Reset Chat
                  </Button>
                </div>

                {/* Quick Query Prompt Chips */}
                <div className="border-b border-border/60 bg-muted/30 p-2.5">
                  <p className="mb-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Quick Graph Inquiries:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      '🔍 Explain why this party won',
                      '🕸️ What nodes & telemetry exist in the graph?',
                      '📅 Verify date gap & SLA',
                      '📜 What dispute rules apply?',
                      '⚡ Audit evidence tiers',
                    ].map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleSendChat(prompt)}
                        className="rounded-lg border border-border bg-card px-2 py-1 text-[10px] font-medium text-foreground transition hover:border-primary hover:bg-primary/5"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chat Message Stream */}
                <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 text-xs">
                  {currentChat.map((msg) => (
                    <div
                      key={msg.id}
                      className={cx(
                        'flex flex-col max-w-[85%] rounded-2xl p-3 leading-5',
                        msg.sender === 'analyst'
                          ? 'self-end bg-primary text-primary-foreground rounded-tr-xs'
                          : 'self-start border border-border bg-muted/40 text-foreground rounded-tl-xs'
                      )}
                    >
                      <div className="flex items-center justify-between gap-3 text-[10px] opacity-75 mb-1">
                        <span className="font-semibold">{msg.sender === 'analyst' ? 'You (Analyst)' : 'Graph Copilot'}</span>
                        <span>{msg.timestamp}</span>
                      </div>
                      <p className="whitespace-pre-line text-xs">{msg.text}</p>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="self-start rounded-2xl border border-border bg-muted/40 p-3 rounded-tl-xs flex items-center gap-1.5 text-xs text-muted-foreground">
                      <span className="size-1.5 rounded-full bg-primary animate-bounce" />
                      <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:0.2s]" />
                      <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:0.4s]" />
                      <span className="ml-1 text-[11px]">Traversing graph relationships…</span>
                    </div>
                  )}
                </div>

                {/* Chat Input Bar */}
                <div className="border-t border-border p-3">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      handleSendChat()
                    }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="text"
                      placeholder={`Ask anything about Case ${selectedScenario.caseId} graph nodes, telemetry, rules...`}
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      className="h-9 flex-1 rounded-xl border border-input bg-background px-3 text-xs outline-none focus:ring-2 focus:ring-ring"
                    />
                    <Button type="submit" size="sm" disabled={!chatInput.trim() || isTyping} className="h-9 gap-1 text-xs">
                      <Send className="size-3.5" />
                    </Button>
                  </form>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Override Modal */}
        {showOverrideModal && selectedScenario && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
            <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <UserCheck className="size-5 text-purple-600" />
                  <h3 className="font-bold text-base text-foreground">Manual Analyst Decision Override</h3>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setShowOverrideModal(false)} className="size-7 p-0">
                  <X className="size-4" />
                </Button>
              </div>

              <div className="mt-4 flex flex-col gap-4 text-xs">
                <div>
                  <label className="font-semibold text-foreground">Dispute Case</label>
                  <p className="mt-0.5 text-muted-foreground">{selectedScenario.caseId} — {selectedScenario.label}</p>
                </div>

                <div>
                  <label htmlFor="outcome-select" className="font-semibold text-foreground">Select Manual Verdict</label>
                  <select
                    id="outcome-select"
                    value={overrideOutcome}
                    onChange={(e) => setOverrideOutcome(e.target.value)}
                    className="mt-1.5 h-9 w-full rounded-xl border border-input bg-background px-3 text-xs outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="Cardholder Refund (Manual Override)">Cardholder Refund (Rule 13.1 / 13.3 Override)</option>
                    <option value="Merchant Defense Upheld (Manual Override)">Merchant Defense Upheld (Proof of Delivery Verified)</option>
                    <option value="Split Liability 50/50 (Goodwill)">Split Liability 50/50 (Merchant Goodwill / Concession)</option>
                    <option value="Escalate to Pre-Arbitration Scheme Review">Escalate to Pre-Arbitration Scheme Review</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="override-notes" className="font-semibold text-foreground">Analyst Reason & Justification Notes</label>
                  <textarea
                    id="override-notes"
                    value={overrideNote}
                    onChange={(e) => setOverrideNote(e.target.value)}
                    placeholder="Document evidentiary justification for overriding the AI recommendation..."
                    className="mt-1.5 min-h-24 w-full rounded-xl border border-input bg-background p-3 text-xs leading-5 outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              </div>

              <div className="mt-5 flex items-center justify-end gap-2 border-t border-border pt-4">
                <Button variant="outline" size="sm" onClick={() => setShowOverrideModal(false)} className="text-xs">
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveOverride}
                  className="text-xs bg-purple-600 hover:bg-purple-700 text-white"
                >
                  Confirm & Log Override
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
