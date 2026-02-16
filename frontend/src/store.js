import { create } from 'zustand'
import axios from 'axios'

export const useStore = create((set) => ({
  signal: null,
  positions: null,
  backtest: null,
  async refresh() {
    const [analysis, positions] = await Promise.all([
      axios.post('http://localhost:8000/analyze'),
      axios.get('http://localhost:8000/positions'),
    ])
    set({ signal: analysis.data, positions: positions.data })
  },
}))
