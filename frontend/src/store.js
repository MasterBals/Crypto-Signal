import { create } from 'zustand'
import axios from 'axios'

const API = 'http://localhost:8000'

export const useStore = create((set) => ({
  signal: null,
  positions: null,
  backtest: null,
  settings: null,
  async refresh() {
    const [analysis, positions] = await Promise.all([
      axios.post(`${API}/analyze`),
      axios.get(`${API}/positions`),
    ])
    set({ signal: analysis.data, positions: positions.data })
  },
  async loadSettings() {
    const response = await axios.get(`${API}/settings`)
    set({ settings: response.data })
    return response.data
  },
  async saveSettings(payload) {
    const response = await axios.put(`${API}/settings`, payload)
    set({ settings: response.data })
    return response.data
  },
}))
