'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Building2,
  Check,
  ChevronDown,
  CircleDot,
  ClipboardCheck,
  CreditCard,
  FileText,
  GitBranch,
  Landmark,
  Layers,
  Loader2,
  Plus,
  RotateCcw,
  Send,
  ShieldCheck,
  Sparkles,
  UserRound,
  WalletCards,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getScenario, initialTimeline, scenarios, type Evidence, type TimelineEvent } from '@/data/scenarios'
import { caseService, type BackendDecision } from '@/services/case-service'

const cx = (...classes: Array<string | false | undefined>) => classes.filter(Boolean).join(' ')

function EvidenceList({
  items,
  selected,
  onToggle,
  disabled,
}: {
  items: Evidence[]
  selected: string[]
  onToggle: (id: string) => void
  disabled?: boolean
}) {
  return (
    <div className="flex flex-col gap-2">
      {items.map((item) => {
        const isSelected = selected.includes(item.id)
        return (
          <div
            key={item.id}
            onClick={() => !disabled && onToggle(item.id)}
            className={cx(
              'flex items-center gap-3 rounded-xl border p-3 text-left transition select-none',
              isSelected
                ? 'border-primary/60 bg-primary/5 shadow-2xs'
                : 'border-dashed border-amber-300 bg-amber-50/20 dark:border-amber-800/60 dark:bg-amber-950/10 opacity-90',
              !disabled && 'cursor-pointer hover:border-primary hover:bg-primary/10'
            )}
          >
            <span
              className={cx(
                'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors',
                isSelected
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300'
              )}
            >
              {isSelected ? <Check className="size-4" /> : <Plus className="size-4" />}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-xs font-semibold text-foreground">{item.name}</span>
                {item.tier && (
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    {item.tier === 'TIER_1_TELEMETRY'
                      ? 'Tier 1 Telemetry'
                      : item.tier === 'TIER_2_COMMUNICATION'
                      ? 'Tier 2 Record'
                      : 'Tier 3 Assertion'}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">{item.detail}</p>
            </div>
            <button
              type="button"
              disabled={disabled}
              onClick={(e) => {
                e.stopPropagation()
                if (!disabled) onToggle(item.id)
              }}
              className={cx(
                'shrink-0 flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold transition',
                isSelected
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs'
              )}
            >
              {isSelected ? (
                <>
                  <Check className="size-3" /> Attached
                </>
              ) : (
                <>
                  <Plus className="size-3" /> Add Evidence
                </>
              )}
            </button>
          </div>
        )
      })}
    </div>
  )
}

function SectionTitle({
  icon: Icon,
  eyebrow,
  title,
  tone = 'primary',
}: {
  icon: typeof UserRound
  eyebrow: string
  title: string
  tone?: 'primary' | 'amber' | 'green'
}) {
  return (
    <div className="flex items-start gap-3">
      <span
        className={cx(
          'mt-0.5 flex size-9 items-center justify-center rounded-xl',
          tone === 'amber'
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
            : tone === 'green'
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400'
            : 'bg-primary/10 text-primary'
        )}
      >
        <Icon className="size-4" />
      </span>
      <div>
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
        <h2 className="mt-0.5 text-base font-semibold tracking-tight text-foreground">{title}</h2>
      </div>
    </div>
  )
}

function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="flex flex-col">
      {events.map((event, index) => (
        <div key={event.label} className="flex gap-3">
          <div className="flex flex-col items-center">
            <span
              className={cx(
                'mt-1 flex size-5 items-center justify-center rounded-full border-2',
                event.status === 'complete'
                  ? 'border-emerald-500 bg-emerald-500 text-white'
                  : event.status === 'current'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-background text-transparent'
              )}
            >
              {event.status === 'complete' ? <Check className="size-3" /> : <CircleDot className="size-3" />}
            </span>
            {index < events.length - 1 && (
              <span
                className={cx(
                  'w-px flex-1',
                  event.status === 'complete' ? 'bg-emerald-300 dark:bg-emerald-800' : 'bg-border'
                )}
              />
            )}
          </div>
          <div className={cx('pb-5', index === events.length - 1 && 'pb-0')}>
            <p className={cx('text-xs font-semibold', event.status === 'pending' && 'text-muted-foreground')}>
              {event.label}
            </p>
            <p className="mt-0.5 text-[11px] leading-4 text-muted-foreground">{event.detail}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export function DisputePlayground({
  initialScenarioId,
  onNavigateToAnalyst,
}: {
  initialScenarioId?: string
  onNavigateToAnalyst?: () => void
} = {}) {
  const [scenarioId, setScenarioId] = useState(initialScenarioId || scenarios[0].id)
  const scenario = useMemo(() => getScenario(scenarioId), [scenarioId])

  const [claim, setClaim] = useState(scenario.claim)
  const [merchantResponse, setMerchantResponse] = useState(scenario.merchantResponse)
  const [customerEvidence, setCustomerEvidence] = useState<string[]>(scenario.customerEvidence.map((e) => e.id))
  const [merchantEvidence, setMerchantEvidence] = useState<string[]>(scenario.merchantEvidence.map((e) => e.id))
  const [customerSubmitted, setCustomerSubmitted] = useState(false)
  const [merchantSubmitted, setMerchantSubmitted] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [detail, setDetail] = useState<'reasoning' | 'graph' | null>('reasoning')
  const [pipelineStage, setPipelineStage] = useState(0)
  const [liveDecision, setLiveDecision] = useState<BackendDecision | null>(null)

  // Clear live decision if scenario changes to prevent cross-case contamination
  useEffect(() => {
    if (liveDecision && liveDecision.case_id !== scenario.caseId) {
      setLiveDecision(null)
      setMerchantSubmitted(false)
      setCustomerSubmitted(false)
      setPipelineStage(0)
    }
  }, [scenario.caseId, liveDecision])

  const events = useMemo(() => {
    const list: TimelineEvent[] = [
      {
        label: '1. Dispute filed',
        detail: customerSubmitted
          ? `Cardholder claim & ${scenario.customerEvidence.length} documents ingested`
          : 'Waiting for cardholder dispute intake submission',
        status: customerSubmitted ? 'complete' : 'current',
      },
      {
        label: '2. Merchant notified',
        detail: customerSubmitted
          ? `Representment package delivered to ${scenario.merchant}`
          : 'Awaiting dispute intake',
        status: customerSubmitted ? (merchantSubmitted || isSubmitting ? 'complete' : 'current') : 'pending',
      },
      {
        label: '3. Merchant defense',
        detail: merchantSubmitted || isSubmitting
          ? `Telemetry & ${scenario.merchantEvidence.length} defense records submitted`
          : 'Waiting for merchant defense and telemetry submission',
        status: (merchantSubmitted || isSubmitting) ? 'complete' : 'pending',
      },
      {
        label: '4. Evidence OCR & Extraction',
        detail: pipelineStage >= 2 || merchantSubmitted
          ? 'Canonical JSON extractions and OCR text parsed'
          : isSubmitting || pipelineStage >= 1
          ? 'Extracting receipts, tracking logs & photos...'
          : 'Awaiting evidence submission',
        status: pipelineStage >= 2 || merchantSubmitted ? 'complete' : isSubmitting || pipelineStage >= 1 ? 'current' : 'pending',
      },
      {
        label: '5. 5-Layer Knowledge Graph',
        detail: pipelineStage >= 3 || merchantSubmitted
          ? `${scenario.graph.nodes.length} entity hubs & relational bridges validated in Neo4j`
          : pipelineStage >= 2
          ? 'Constructing graph topology & running validation...'
          : 'Awaiting extraction',
        status: pipelineStage >= 3 || merchantSubmitted ? 'complete' : pipelineStage >= 2 ? 'current' : 'pending',
      },
      {
        label: '6. Tri-Agent Reasoning Decision',
        detail: merchantSubmitted && pipelineStage >= 3
          ? 'Explainable multi-tier verdict & deterministic scores synthesized'
          : pipelineStage >= 2
          ? 'Evaluating evidence tiers & running arithmetic checks...'
          : 'Awaiting graph mapping',
        status: merchantSubmitted && pipelineStage >= 3 ? 'complete' : isSubmitting && pipelineStage >= 2 ? 'current' : 'pending',
      },
    ]
    return list
  }, [customerSubmitted, merchantSubmitted, isSubmitting, pipelineStage, scenario])

  const reset = (id = scenarioId) => {
    const next = getScenario(id)
    setScenarioId(id)
    setClaim(next.claim)
    setMerchantResponse(next.merchantResponse)
    setCustomerEvidence(next.customerEvidence.map((e) => e.id))
    setMerchantEvidence(next.merchantEvidence.map((e) => e.id))
    setCustomerSubmitted(false)
    setMerchantSubmitted(false)
    setIsSubmitting(false)
    setDetail('reasoning')
    setPipelineStage(0)
    setLiveDecision(null)
  }

  const toggle = (id: string, side: 'customer' | 'merchant') => {
    const setter = side === 'customer' ? setCustomerEvidence : setMerchantEvidence
    setter((current) => (current.includes(id) ? current.filter((val) => val !== id) : [...current, id]))
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      {/* Top Navigation */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-xs">
              <ShieldCheck className="size-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">DisputeSolver</p>
                <span className="rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                  Multi-Agent Hybrid Engine
                </span>
              </div>
              <h1 className="text-lg font-bold tracking-tight text-foreground">
                Intake, Extraction & Knowledge Graph Resolution Playground
              </h1>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label htmlFor="scenario" className="text-xs font-semibold text-muted-foreground">
              Dispute Category:
            </label>
            <select
              id="scenario"
              value={scenarioId}
              onChange={(e) => reset(e.target.value)}
              className="h-9 rounded-xl border border-input bg-background px-3 text-xs font-semibold outline-none focus:ring-2 focus:ring-ring"
            >
              {scenarios.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label} ({item.amount}) — {item.caseId}
                </option>
              ))}
            </select>
            <Button variant="outline" size="sm" onClick={() => reset()} className="text-xs">
              <RotateCcw className="mr-1 size-3.5" />
              Reset Case
            </Button>
            {onNavigateToAnalyst && (
              <Button
                variant="default"
                size="sm"
                onClick={onNavigateToAnalyst}
                className="gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Bot className="size-3.5" />
                Analyst Dashboard & Chat
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1500px] px-5 py-6 lg:px-8">
        {/* Case Metadata Banner */}
        <div className="mb-6 grid gap-4 rounded-2xl border border-border bg-card p-5 shadow-xs lg:grid-cols-[1fr_auto]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary">
                CASE: {scenario.caseId}
              </span>
              <span className="rounded-md bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
                Reason Code: {scenario.reasonCode} ({scenario.category})
              </span>
              <span className="rounded-md bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400">
                Disputed Amount: {scenario.amount} {scenario.currency}
              </span>
            </div>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              {scenario.label}
            </h2>
            <p className="mt-1 max-w-3xl text-xs text-muted-foreground leading-5">
              Simulating end-to-end data pipeline: Real files from <code className="rounded bg-muted px-1 text-[11px] font-mono">{scenario.categoryFolder}</code> ingested into Canonical JSON &rarr; 5-layer Neo4j graph &rarr; Tri-agent reasoning engine.
            </p>
          </div>

          <div className="flex flex-col gap-2 rounded-xl border border-border/80 bg-muted/40 p-3 text-xs">
            <div className="flex items-center gap-2">
              <UserRound className="size-3.5 text-primary" />
              <span className="font-semibold text-foreground">{scenario.customer}</span>
              <span className="text-muted-foreground">(Cardholder)</span>
            </div>
            <div className="flex items-center gap-2">
              <Building2 className="size-3.5 text-amber-600" />
              <span className="font-semibold text-foreground">{scenario.merchant}</span>
              <span className="text-muted-foreground">({scenario.merchantId})</span>
            </div>
            <div className="flex items-center gap-2">
              <CreditCard className="size-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Order Ref: {scenario.orderId} · Date: {scenario.date}</span>
            </div>
          </div>
        </div>

        {/* 2-Column Portals Grid + Timeline Sidebar */}
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_310px]">
          <div className="grid gap-5 lg:grid-cols-2">
            {/* 1. Customer Portal */}
            <section className="rounded-2xl border border-border bg-card p-5 shadow-xs">
              <SectionTitle icon={UserRound} eyebrow="Customer Portal" title="Cardholder Dispute Intake Form" />

              <div className="mt-4 flex flex-col gap-4">
                {/* Transaction details box */}
                <div className="rounded-xl border border-border/80 bg-muted/40 p-3.5">
                  <div className="flex items-center justify-between border-b border-border/60 pb-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-primary">
                      Disputed Transaction Details
                    </span>
                    <span className="text-xs font-bold text-foreground">{scenario.amount} {scenario.currency}</span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Merchant:</span>
                      <p className="font-medium text-foreground">{scenario.merchant}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Order Reference:</span>
                      <p className="font-mono text-foreground">{scenario.orderId}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Dispute Reason:</span>
                      <p className="font-medium text-foreground">{scenario.category}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Transaction Date:</span>
                      <p className="text-foreground">{scenario.date}</p>
                    </div>
                  </div>
                </div>

                {/* Pre-filled Claim Statement */}
                <div>
                  <label htmlFor="claim" className="mb-1.5 block text-xs font-bold text-foreground">
                    Customer Statement & Description
                  </label>
                  <textarea
                    id="claim"
                    value={claim}
                    readOnly
                    className="min-h-24 w-full cursor-not-allowed resize-none rounded-xl border border-input bg-muted/30 p-3 text-xs leading-5 outline-none"
                  />
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    * Pre-filled from <code className="font-mono">{scenario.categoryFolder}/cardholder/cardholder_intake_form.json</code>
                  </p>
                </div>

                {/* Supporting Documents */}
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-xs font-bold text-foreground">Attached Cardholder Evidence</label>
                    <span className="text-[11px] font-semibold text-muted-foreground">
                      {customerEvidence.length} / {scenario.customerEvidence.length} files attached
                    </span>
                  </div>
                  <EvidenceList
                    items={scenario.customerEvidence}
                    selected={customerEvidence}
                    onToggle={(id) => toggle(id, 'customer')}
                    disabled={customerSubmitted}
                  />
                </div>

                {customerEvidence.length < scenario.customerEvidence.length && !customerSubmitted && (
                  <div className="flex items-start gap-2.5 rounded-xl border border-amber-300 bg-amber-50/90 p-3 text-xs leading-5 text-amber-900 dark:border-amber-800/70 dark:bg-amber-950/40 dark:text-amber-300">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
                    <div className="flex-1">
                      <p className="font-semibold">Missing Evidence Documents ({customerEvidence.length}/{scenario.customerEvidence.length} Attached)</p>
                      <p className="text-[11px] text-amber-800/90 dark:text-amber-400/90">
                        Current evidence is incomplete. Please attach all mandatory documents using the <strong>+ Add Evidence</strong> button to prevent pipeline ingestion errors.
                      </p>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="h-7 shrink-0 text-[11px] border-amber-400 text-amber-900 hover:bg-amber-100 dark:border-amber-700 dark:text-amber-200"
                      onClick={() => setCustomerEvidence(scenario.customerEvidence.map((e) => e.id))}
                    >
                      Attach All
                    </Button>
                  </div>
                )}

                <Button
                  className="w-full gap-2 font-semibold shadow-xs"
                  disabled={customerSubmitted || customerEvidence.length < scenario.customerEvidence.length}
                  onClick={async () => {
                    await caseService.submitCustomer({
                      scenarioId,
                      caseId: scenario.caseId,
                      claim,
                      evidenceIds: customerEvidence,
                    })
                    setCustomerSubmitted(true)
                  }}
                >
                  {customerSubmitted ? (
                    <>
                      <Check className="size-4" /> 1. Dispute Ingested into Graph
                    </>
                  ) : (
                    <>
                      <Send className="size-4" /> 1. Submit Dispute Form
                    </>
                  )}
                </Button>

                {customerSubmitted && (
                  <div className="flex items-start gap-2 rounded-xl bg-emerald-50 p-3 text-xs leading-5 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                    <Check className="mt-0.5 size-4 shrink-0" />
                    Intake received. Formal representment notification delivered to {scenario.merchant}.
                  </div>
                )}
              </div>
            </section>

            {/* 2. Merchant Portal */}
            <section className="rounded-2xl border border-border bg-card p-5 shadow-xs">
              <SectionTitle icon={Landmark} eyebrow="Merchant Portal" title="Merchant Defense & Telemetry Submission" tone="amber" />

              <div className="mt-4 flex flex-col gap-4">
                {!customerSubmitted ? (
                  <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border py-14 text-center text-xs text-muted-foreground">
                    <AlertCircle className="size-6 text-muted-foreground" />
                    <p className="font-semibold">Merchant Portal Awaiting Intake</p>
                    <p className="max-w-xs text-[11px]">
                      Click &ldquo;1. Submit Dispute Form&rdquo; in the cardholder portal to simulate dispute intake and trigger the merchant notification.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Customer Claim context */}
                    <div className="rounded-xl border border-border bg-muted/40 p-3">
                      <p className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                        Customer Claim Under Review
                      </p>
                      <p className="mt-1 text-xs text-foreground leading-5">{claim}</p>
                    </div>

                    {/* Pre-filled Defense Narrative */}
                    <div>
                      <label htmlFor="merchant-response" className="mb-1.5 block text-xs font-bold text-foreground">
                        Merchant Response Statement
                      </label>
                      <textarea
                        id="merchant-response"
                        value={merchantResponse}
                        readOnly
                        className="min-h-24 w-full cursor-not-allowed resize-none rounded-xl border border-input bg-muted/30 p-3 text-xs leading-5 outline-none"
                      />
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        * Pre-filled from <code className="font-mono">{scenario.categoryFolder}/merchant/merchant_response_form.json</code>
                      </p>
                    </div>

                    {/* Merchant Supporting Evidence */}
                    <div>
                      <div className="mb-2 flex items-center justify-between">
                        <label className="text-xs font-bold text-foreground">Attached Merchant Telemetry & Proof</label>
                        <span className="text-[11px] font-semibold text-muted-foreground">
                          {merchantEvidence.length} / {scenario.merchantEvidence.length} files attached
                        </span>
                      </div>
                      <EvidenceList
                        items={scenario.merchantEvidence}
                        selected={merchantEvidence}
                        onToggle={(id) => toggle(id, 'merchant')}
                        disabled={merchantSubmitted}
                      />
                    </div>

                    {merchantEvidence.length < scenario.merchantEvidence.length && !merchantSubmitted && (
                      <div className="flex items-start gap-2.5 rounded-xl border border-amber-300 bg-amber-50/90 p-3 text-xs leading-5 text-amber-900 dark:border-amber-800/70 dark:bg-amber-950/40 dark:text-amber-300">
                        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
                        <div className="flex-1">
                          <p className="font-semibold">Missing Telemetry / Records ({merchantEvidence.length}/{scenario.merchantEvidence.length} Attached)</p>
                          <p className="text-[11px] text-amber-800/90 dark:text-amber-400/90">
                            Current merchant evidence is incomplete. Please upload all evidence documents using the <strong>+ Add Evidence</strong> button before running the AI reasoning pipeline.
                          </p>
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-7 shrink-0 text-[11px] border-amber-400 text-amber-900 hover:bg-amber-100 dark:border-amber-700 dark:text-amber-200"
                          onClick={() => setMerchantEvidence(scenario.merchantEvidence.map((e) => e.id))}
                        >
                          Attach All
                        </Button>
                      </div>
                    )}

                    <Button
                      variant="secondary"
                      className="w-full gap-2 font-semibold shadow-xs"
                      disabled={merchantSubmitted || isSubmitting || merchantEvidence.length < scenario.merchantEvidence.length}
                      onClick={async () => {
                        setIsSubmitting(true)
                        setPipelineStage(1)
                        try {
                          const result = await caseService.submitMerchant({
                            scenarioId,
                            caseId: scenario.caseId,
                            response: merchantResponse,
                            evidenceIds: merchantEvidence,
                            onProgress: (stage) => setPipelineStage(stage),
                          })
                          setLiveDecision(result.liveDecision)
                          setMerchantSubmitted(true)
                          setPipelineStage(3)
                        } catch (err) {
                          console.error(err)
                          setMerchantSubmitted(true)
                          setPipelineStage(3)
                        } finally {
                          setIsSubmitting(false)
                        }
                      }}
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="size-4 animate-spin text-primary" />
                          2. Executing AI Pipeline (OCR &rarr; Neo4j &rarr; Reasoning)...
                        </>
                      ) : merchantSubmitted ? (
                        <>
                          <Check className="size-4" /> 2. Defense Submitted & Evaluated
                        </>
                      ) : (
                        <>
                          <ArrowRight className="size-4" /> 2. Submit Merchant Defense
                        </>
                      )}
                    </Button>
                  </>
                )}
              </div>
            </section>
          </div>

          {/* Timeline Sidebar */}
          <aside className="flex flex-col gap-5">
            <section className="rounded-2xl border border-border bg-card p-5 shadow-xs">
              <div className="mb-4 flex items-center gap-2">
                <ClipboardCheck className="size-4 text-primary" />
                <h3 className="font-bold text-sm">Dispute Lifecycle Timeline</h3>
              </div>
              <Timeline events={events} />
            </section>

            {merchantSubmitted && pipelineStage >= 2 && (
              <section className="rounded-2xl border border-primary/20 bg-primary/5 p-5 shadow-xs transition-all duration-500 animate-in fade-in">
                <div className="flex items-start gap-3">
                  <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                    <Bot className="size-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold">Pipeline Complete</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground leading-4">
                      Executed extraction &rarr; graph topology &rarr; tri-agent reasoning engine.
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex flex-col gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <Check className="size-3.5 text-emerald-600" />
                    <span>Canonical Extraction Built</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="size-3.5 text-emerald-600" />
                    <span>5-Layer Knowledge Graph Mapped</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="size-3.5 text-emerald-600" />
                    <span>Deterministic & Semantic Verdict Ready</span>
                  </div>
                </div>
              </section>
            )}
          </aside>
        </div>

        {/* 3. AI Resolution & Scoring Center */}
        {merchantSubmitted && pipelineStage >= 3 && (() => {
          const isLive = !!liveDecision && liveDecision.case_id === scenario.caseId
          const active = isLive ? liveDecision : null

          const verdictLabel = active
            ? active.verdict === 'MERCHANT'
              ? 'Merchant Wins — Dispute Denied'
              : active.verdict === 'CARDHOLDER'
              ? 'Cardholder Wins — Refund Granted'
              : 'Insufficient Evidence — Case Escalated'
            : scenario.decision.outcome

          const confidenceLabel = active
            ? `${(active.confidence_score * 100).toFixed(1)}%`
            : scenario.decision.confidence

          const summaryText = active
            ? active.executive_summary
            : scenario.decision.summary

          const primaryReason = active
            ? active.primary_reason
            : scenario.decision.primaryReason || scenario.decision.summary

          const policyBasis = active
            ? active.policy_basis
            : scenario.decision.policyBasis || 'Card Scheme Dispute Regulations'

          const factors = active && active.reasoning_statements?.length
            ? active.reasoning_statements.slice(0, 3).map((r) => r.statement)
            : scenario.decision.factors

          const signals = active && active.reasoning_statements?.length
            ? active.reasoning_statements.map((r) => `[${r.source_tier.replace('TIER_', 'Tier ').replace('_', ' ')} · ${r.supports.toUpperCase()} · weight ${r.weight.toFixed(3)}] ${r.statement}`)
            : scenario.reasoning.signals

          const counterargs = active?.counterarguments_addressed ?? []
          const dm = active?.deterministic_metrics ?? null

          return (
          <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-sm" style={{ animation: 'fadeSlideIn 0.5s ease-out' }}>
            {/* Data source badge */}
            {isLive && (
              <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50/60 px-3 py-2 text-[11px] font-semibold text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/30 dark:text-emerald-300">
                <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                Live Backend Decision — Pipeline: {active!.pipeline}
                {active!.execution_time_seconds && (
                  <span className="ml-auto font-normal text-emerald-700 dark:text-emerald-400">
                    Executed in {active!.execution_time_seconds.toFixed(2)}s
                  </span>
                )}
              </div>
            )}

            {/* Header */}
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between border-b border-border pb-5">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-400">
                    Explainable AI Resolution
                  </span>
                  <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    Case {scenario.caseId}
                  </span>
                  <span className="rounded-md bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                    ⏱ {scenario.resolutionTime.cycleDays} Days Resolution ({scenario.resolutionTime.timeSavedDays} Days Saved vs {scenario.resolutionTime.industryBaselineDays}d Industry SLA)
                  </span>
                  {isLive && (
                    <span className="rounded-md bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
                      {active!.confidence_band.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground">{verdictLabel}</h2>
                <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{summaryText}</p>
              </div>

              <div className={`flex items-center gap-3 rounded-2xl border px-5 py-3 ${
                isLive && active!.confidence_score >= 0.75
                  ? 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-900/40 dark:bg-emerald-950/40'
                  : isLive && active!.confidence_score < 0.6
                  ? 'border-amber-200 bg-amber-50/80 dark:border-amber-900/40 dark:bg-amber-950/40'
                  : 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-900/40 dark:bg-emerald-950/40'
              }`}>
                <Sparkles className={`size-5 ${
                  isLive && active!.confidence_score < 0.6
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-emerald-600 dark:text-emerald-400'
                }`} />
                <div>
                  <p className="text-[11px] font-semibold text-muted-foreground">Confidence Score</p>
                  <p className="text-2xl font-bold text-foreground">{confidenceLabel}</p>
                </div>
              </div>
            </div>

            {/* Deterministic Metrics Row — only shown when live backend data exists */}
            {isLive && dm && (
              <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-border bg-muted/30 p-4 text-xs sm:grid-cols-5">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Cardholder Score</span>
                  <span className="text-sm font-bold text-foreground">{dm.cardholder_pct}</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Merchant Score</span>
                  <span className="text-sm font-bold text-foreground">{dm.merchant_pct}</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Date Checks</span>
                  <span className="text-sm font-bold text-foreground">{dm.date_verifications_count}</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Amount Checks</span>
                  <span className="text-sm font-bold text-foreground">{dm.amount_verifications_count}</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Misstatements</span>
                  <span className={`text-sm font-bold ${dm.misstatements_detected > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    {dm.misstatements_detected}
                  </span>
                </div>
              </div>
            )}

            {/* Key Factors */}
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {factors.map((factor, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2.5 rounded-xl border border-border/60 bg-muted/40 p-3 text-xs leading-5"
                >
                  <Check className="mt-0.5 size-4 shrink-0 text-emerald-600" />
                  <span className="text-foreground">{factor}</span>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-4">
              <Button
                variant={detail === 'reasoning' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDetail(detail === 'reasoning' ? null : 'reasoning')}
                className="gap-1.5 text-xs"
              >
                <Sparkles className="size-3.5" />
                {isLive ? 'Backend Reasoning Statements' : 'Tri-Agent Reasoning Breakdown'}
                <ChevronDown className={cx('size-3.5 transition-transform', detail === 'reasoning' && 'rotate-180')} />
              </Button>

              <Button
                variant={detail === 'graph' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDetail(detail === 'graph' ? null : 'graph')}
                className="gap-1.5 text-xs"
              >
                <GitBranch className="size-3.5" />
                5-Layer Knowledge Graph ({scenario.graph.nodes.length} Nodes)
                <ChevronDown className={cx('size-3.5 transition-transform', detail === 'graph' && 'rotate-180')} />
              </Button>
            </div>

            {/* Reasoning Drawer */}
            {detail === 'reasoning' && (
              <div className="mt-4 rounded-xl border border-border bg-muted/30 p-5 text-xs">
                {isLive ? (
                  <div className="flex flex-col gap-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-primary">
                      Reasoning Statements ({active!.reasoning_statements.length} evidence points evaluated)
                    </p>
                    {active!.reasoning_statements.map((r, i) => (
                      <div key={i} className="flex items-start gap-3 rounded-lg border border-border/50 bg-card p-3">
                        <span className={`mt-0.5 shrink-0 rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                          r.supports === 'merchant' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        }`}>
                          {r.supports}
                        </span>
                        <div className="flex-1">
                          <p className="leading-5 text-foreground">{r.statement}</p>
                          <div className="mt-1 flex items-center gap-3 text-[10px] text-muted-foreground">
                            <span>{r.source_tier.replace('TIER_', 'Tier ').replace('_', ' ')}</span>
                            <span>·</span>
                            <span>Weight: <strong className="text-foreground">{r.weight.toFixed(4)}</strong></span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {counterargs.length > 0 && (
                      <div className="mt-2 rounded-lg border border-border/50 bg-card p-3">
                        <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-primary">Counterarguments Addressed</p>
                        {counterargs.map((ca, i) => (
                          <p key={i} className="leading-5 text-muted-foreground">{ca}</p>
                        ))}
                      </div>
                    )}
                    <div className="rounded-lg border border-border/50 bg-card p-3">
                      <p className="mb-1 text-[11px] font-bold uppercase tracking-wider text-primary">Policy & Rule Basis</p>
                      <p className="leading-5 text-foreground">{policyBasis}</p>
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Core Dispute Question</p>
                      <p className="mt-1 text-foreground leading-5">{scenario.reasoning.question}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Primary Decisive Reason</p>
                      <p className="mt-1 text-foreground leading-5">{primaryReason}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Evaluation Signals</p>
                      <ul className="mt-1 flex flex-col gap-1 text-muted-foreground leading-5">
                        {signals.map((item, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-primary">▸</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Policy & Rule Basis</p>
                      <p className="mt-1 text-foreground leading-5">{policyBasis}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Graph Drawer */}
            {detail === 'graph' && (
              <div className="mt-4 overflow-x-auto rounded-xl border border-border bg-muted/30 p-5">
                <div className="flex min-w-[700px] items-center justify-center gap-3 py-6">
                  {scenario.graph.nodes.map((node, index) => (
                    <div key={node.id} className="flex items-center gap-3">
                      <div className="min-w-32 rounded-xl border border-border bg-card p-3 text-center shadow-xs">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-primary">{node.kind}</p>
                        <p className="mt-1 text-xs font-semibold text-foreground">{node.label}</p>
                      </div>
                      {index < scenario.graph.nodes.length - 1 && (
                        <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
                      )}
                    </div>
                  ))}
                </div>
                <p className="text-center text-[11px] text-muted-foreground">
                  Knowledge Graph Topology · {scenario.graph.edges.length} directed relational bridges in Neo4j
                </p>
              </div>
            )}
          </section>
          )
        })()}
      </div>
    </main>
  )
}
