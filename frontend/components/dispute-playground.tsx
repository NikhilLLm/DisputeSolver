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
import { caseService } from '@/services/case-service'

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
  const [detail, setDetail] = useState<'reasoning' | 'graph' | null>('reasoning')
  const [pipelineStage, setPipelineStage] = useState(0)

  // Stagger pipeline stages after merchant submits for visual pacing
  useEffect(() => {
    if (!merchantSubmitted) { setPipelineStage(0); return }
    const t1 = setTimeout(() => setPipelineStage(1), 800)
    const t2 = setTimeout(() => setPipelineStage(2), 1600)
    const t3 = setTimeout(() => setPipelineStage(3), 2200)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [merchantSubmitted])

  const events = useMemo(() => {
    const next = initialTimeline()
    if (customerSubmitted) {
      next[0] = { label: 'Dispute filed', detail: `Cardholder claim & ${scenario.customerEvidence.length} docs ingested`, status: 'complete' }
      next[1] = { label: 'Merchant notified', detail: `Representment package sent to ${scenario.merchant}`, status: 'current' }
    }
    if (merchantSubmitted) {
      next[1].status = 'complete'
      next[2] = { label: 'Merchant defense', detail: `Telemetry & ${scenario.merchantEvidence.length} records submitted`, status: 'complete' }
      next[3] = {
        label: 'AI investigation',
        detail: pipelineStage >= 1 ? '5-layer graph & deterministic checks verified' : 'Analyzing evidence graph…',
        status: pipelineStage >= 1 ? 'complete' : 'current',
      }
      next[4] = {
        label: 'Decision ready',
        detail: pipelineStage >= 2 ? 'Explainable verdict synthesized' : 'Awaiting analysis',
        status: pipelineStage >= 2 ? 'complete' : pipelineStage >= 1 ? 'current' : 'pending',
      }
    }
    return next
  }, [customerSubmitted, merchantSubmitted, pipelineStage, scenario])

  const reset = (id = scenarioId) => {
    const next = getScenario(id)
    setScenarioId(id)
    setClaim(next.claim)
    setMerchantResponse(next.merchantResponse)
    setCustomerEvidence(next.customerEvidence.map((e) => e.id))
    setMerchantEvidence(next.merchantEvidence.map((e) => e.id))
    setCustomerSubmitted(false)
    setMerchantSubmitted(false)
    setDetail('reasoning')
    setPipelineStage(0)
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
              Simulating end-to-end data pipeline: Real files from <code className="rounded bg-muted px-1 text-[11px] font-mono">{scenario.categoryFolder}</code> ingested into Canonical JSON $\to$ 5-layer Neo4j graph $\to$ Tri-agent reasoning engine.
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
                      disabled={merchantSubmitted || merchantEvidence.length < scenario.merchantEvidence.length}
                      onClick={async () => {
                        await caseService.submitMerchant({
                          scenarioId,
                          caseId: scenario.caseId,
                          response: merchantResponse,
                          evidenceIds: merchantEvidence,
                        })
                        setMerchantSubmitted(true)
                      }}
                    >
                      {merchantSubmitted ? (
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
                      Executed extraction $\to$ graph topology $\to$ tri-agent reasoning engine.
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
        {merchantSubmitted && pipelineStage >= 3 && (
          <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-sm" style={{ animation: 'fadeSlideIn 0.5s ease-out' }}>
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
                    ⚡ {scenario.resolutionTime.cycleDays} Days Resolution ({scenario.resolutionTime.timeSavedDays} Days Saved vs {scenario.resolutionTime.industryBaselineDays}d Industry SLA)
                  </span>
                </div>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground">{scenario.decision.outcome}</h2>
                <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{scenario.decision.summary}</p>
              </div>

              <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-5 py-3 dark:border-emerald-900/40 dark:bg-emerald-950/40">
                <Sparkles className="size-5 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <p className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">Confidence Score</p>
                  <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">{scenario.decision.confidence}</p>
                </div>
              </div>
            </div>

            {/* Key Factors */}
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {scenario.decision.factors.map((factor) => (
                <div
                  key={factor}
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
                Tri-Agent Reasoning Breakdown
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
              <div className="mt-4 grid gap-4 rounded-xl border border-border bg-muted/30 p-5 md:grid-cols-2 text-xs">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Core Dispute Question</p>
                  <p className="mt-1 text-foreground leading-5">{scenario.reasoning.question}</p>
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Primary Decisive Reason</p>
                  <p className="mt-1 text-foreground leading-5">{scenario.decision.primaryReason || scenario.decision.summary}</p>
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Evaluation Signals</p>
                  <ul className="mt-1 flex flex-col gap-1 text-muted-foreground leading-5">
                    {scenario.reasoning.signals.map((item) => (
                      <li key={item} className="flex items-start gap-1.5">
                        <span className="text-primary">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Policy & Rule Basis</p>
                  <p className="mt-1 text-foreground leading-5">{scenario.decision.policyBasis || 'Card Scheme Dispute Regulations'}</p>
                </div>
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
        )}
      </div>
    </main>
  )
}
