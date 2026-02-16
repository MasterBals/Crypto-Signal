import React, { useEffect, useState } from 'react'
import { useStore } from './store'
import { ChartPanel } from './components/ChartPanel'

const tabs = ['Dashboard', 'Live EURJPY', 'AI Confidence', 'Offene Positionen (Read Only)', 'Backtest']

export function App() {
  const { signal, positions, refresh } = useStore()
  const [active, setActive] = useState(tabs[0])

  useEffect(() => {
    refresh().catch(console.error)
    const id = setInterval(() => refresh().catch(console.error), 300000)
    return () => clearInterval(id)
  }, [refresh])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <h1 className="text-2xl font-bold mb-4">eurjpy-institutional-analyst</h1>
      <div className="flex gap-2 mb-4 flex-wrap">{tabs.map((t) => <button key={t} className={`px-3 py-2 rounded ${active===t?'bg-blue-600':'bg-slate-800'}`} onClick={() => setActive(t)}>{t}</button>)}</div>
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-9"><ChartPanel /></div>
        <div className="col-span-3 bg-slate-900 p-3 rounded border border-slate-700 space-y-2 text-sm">
          <div>Trend H4: {signal?.features?.h4_trend_bull ? 'Bullish' : 'Bearish'}</div>
          <div>Setup Status H1: {signal?.features?.h1_trend_bull ? 'Aktiv' : 'Inaktiv'}</div>
          <div>Entry Validität M15: {signal?.signal?.valid ? 'Valid' : 'Invalid'}</div>
          <div>AI Probability: {((signal?.signal?.ai_probability || 0) * 100).toFixed(1)}%</div>
          <div>Risk/Reward: {signal?.signal?.risk_reward || '-'}</div>
          <div>ATR: {(signal?.features?.atr14 || 0).toFixed(4)}</div>
          <div>Session Status: {(signal?.features?.session_score || 0) > 0.9 ? 'Aktiv' : 'Off Session'}</div>
          <div className="text-xs text-red-300 mt-4">Trading disabled. Read-only analysis mode.</div>
        </div>
      </div>
      <pre className="mt-4 bg-slate-900 p-3 rounded border border-slate-700 text-xs overflow-auto">{JSON.stringify({ active, signal, positions }, null, 2)}</pre>
    </div>
  )
}
