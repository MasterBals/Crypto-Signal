import React, { useEffect, useState } from 'react'
import { useStore } from './store'
import { ChartPanel } from './components/ChartPanel'

const tabs = ['Dashboard', 'Live EURJPY', 'AI Confidence', 'Offene Positionen (Read Only)', 'Backtest', 'Einstellungen']

const defaultSettings = {
  symbol: 'EURJPY',
  risk_per_trade: 1,
  min_ai_probability: 0.72,
  min_rr: 2.2,
  analysis_interval_minutes: 5,
  session_filter: true,
  timeframes: ['H4', 'H1', 'M15'],
  etoro_base_url: 'https://api.etoro.example',
  etoro_client_id: '',
  etoro_client_secret: '',
  etoro_refresh_token: '',
}

export function App() {
  const { signal, positions, refresh, loadSettings, saveSettings, settings } = useStore()
  const [active, setActive] = useState(tabs[0])
  const [form, setForm] = useState(defaultSettings)
  const [message, setMessage] = useState('')

  useEffect(() => {
    refresh().catch(console.error)
    loadSettings().then((data) => setForm(data)).catch(console.error)
    const id = setInterval(() => refresh().catch(console.error), 300000)
    return () => clearInterval(id)
  }, [refresh, loadSettings])

  useEffect(() => {
    if (settings) setForm(settings)
  }, [settings])

  const updateField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }))

  const onSave = async () => {
    try {
      await saveSettings({
        ...form,
        risk_per_trade: Number(form.risk_per_trade),
        min_ai_probability: Number(form.min_ai_probability),
        min_rr: Number(form.min_rr),
        analysis_interval_minutes: Number(form.analysis_interval_minutes),
      })
      setMessage('Einstellungen gespeichert')
    } catch (err) {
      console.error(err)
      setMessage('Speichern fehlgeschlagen')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <h1 className="text-2xl font-bold mb-4">eurjpy-institutional-analyst</h1>
      <div className="flex gap-2 mb-4 flex-wrap">{tabs.map((t) => <button key={t} className={`px-3 py-2 rounded ${active===t?'bg-blue-600':'bg-slate-800'}`} onClick={() => setActive(t)}>{t}</button>)}</div>

      {active !== 'Einstellungen' && (
        <>
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
        </>
      )}

      {active === 'Einstellungen' && (
        <div className="bg-slate-900 p-4 rounded border border-slate-700 space-y-4 max-w-3xl">
          <h2 className="text-xl font-semibold">System-Einstellungen</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <label className="field">Symbol<input value={form.symbol} onChange={(e) => updateField('symbol', e.target.value)} /></label>
            <label className="field">Risk per Trade %<input type="number" step="0.1" value={form.risk_per_trade} onChange={(e) => updateField('risk_per_trade', e.target.value)} /></label>
            <label className="field">Min AI Probability<input type="number" step="0.01" value={form.min_ai_probability} onChange={(e) => updateField('min_ai_probability', e.target.value)} /></label>
            <label className="field">Min RR<input type="number" step="0.1" value={form.min_rr} onChange={(e) => updateField('min_rr', e.target.value)} /></label>
            <label className="field">Intervall (Minuten)<input type="number" value={form.analysis_interval_minutes} onChange={(e) => updateField('analysis_interval_minutes', e.target.value)} /></label>
            <label className="field">Session Filter
              <select value={String(form.session_filter)} onChange={(e) => updateField('session_filter', e.target.value === 'true')}>
                <option value="true">Aktiv</option>
                <option value="false">Inaktiv</option>
              </select>
            </label>
            <label className="field col-span-2">Timeframes (CSV)<input value={(form.timeframes || []).join(',')} onChange={(e) => updateField('timeframes', e.target.value.split(',').map((x) => x.trim()).filter(Boolean))} /></label>
          </div>

          <h3 className="text-lg font-semibold">eToro API (Read Only)</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <label className="field col-span-2">Base URL<input value={form.etoro_base_url} onChange={(e) => updateField('etoro_base_url', e.target.value)} /></label>
            <label className="field">Client ID<input value={form.etoro_client_id} onChange={(e) => updateField('etoro_client_id', e.target.value)} /></label>
            <label className="field">Client Secret<input type="password" value={form.etoro_client_secret} onChange={(e) => updateField('etoro_client_secret', e.target.value)} /></label>
            <label className="field col-span-2">Refresh Token<input type="password" value={form.etoro_refresh_token} onChange={(e) => updateField('etoro_refresh_token', e.target.value)} /></label>
          </div>

          <div className="flex items-center gap-3">
            <button className="px-4 py-2 rounded bg-blue-600" onClick={onSave}>Speichern</button>
            <span className="text-sm text-emerald-300">{message}</span>
          </div>
        </div>
      )}
    </div>
  )
}
