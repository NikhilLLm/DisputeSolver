'use client'

import { useState } from 'react'
import { DisputePlayground } from '@/components/dispute-playground'
import { AnalystDashboard } from '@/components/analyst-dashboard'

export default function Page() {
  const [activeTab, setActiveTab] = useState<'playground' | 'analyst'>('analyst')
  const [activeScenarioId, setActiveScenarioId] = useState<string | undefined>()

  const handleNavigateToPlayground = (scenarioId?: string) => {
    if (scenarioId) setActiveScenarioId(scenarioId)
    setActiveTab('playground')
  }

  const handleNavigateToAnalyst = () => {
    setActiveTab('analyst')
  }

  return (
    <>
      {activeTab === 'analyst' ? (
        <AnalystDashboard onNavigateToPlayground={handleNavigateToPlayground} />
      ) : (
        <DisputePlayground
          initialScenarioId={activeScenarioId}
          onNavigateToAnalyst={handleNavigateToAnalyst}
        />
      )}
    </>
  )
}
