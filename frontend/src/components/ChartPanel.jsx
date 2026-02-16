import React, { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export function ChartPanel() {
  const ref = useRef(null)

  useEffect(() => {
    const chart = createChart(ref.current, { width: 860, height: 420, layout: { background: { color: '#020617' }, textColor: '#cbd5e1' } })
    const series = chart.addCandlestickSeries()
    const now = Math.floor(Date.now() / 1000)
    const data = Array.from({ length: 60 }).map((_, i) => {
      const v = 160 + Math.sin(i / 5) * 0.6
      return { time: now - (60 - i) * 900, open: v, high: v + 0.2, low: v - 0.2, close: v + 0.08 }
    })
    series.setData(data)
    return () => chart.remove()
  }, [])

  return <div ref={ref} className="border border-slate-700 rounded" />
}
