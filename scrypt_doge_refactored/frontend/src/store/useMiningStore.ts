import { create } from 'zustand';

interface MiningState {
  isMining: boolean;
  hashrate: number;
  shares: number;
  temperature: number;
  power: number;
  profit: number;
  alerts: string[];
  startMining: () => void;
  stopMining: () => void;
  updateMetrics: (metrics: Partial<Omit<MiningState, 'isMining' | 'startMining' | 'stopMining' | 'updateMetrics' | 'alerts'>>) => void;
  addAlert: (alert: string) => void;
  clearAlerts: () => void;
}

const useMiningStore = create<MiningState>()((set) => ({
  isMining: false,
  hashrate: 0,
  shares: 0,
  temperature: 0,
  power: 0,
  profit: 0,
  alerts: [],
  startMining: () => set({ isMining: true }),
  stopMining: () => set({ isMining: false }),
  updateMetrics: (metrics) => set((state) => ({ ...state, ...metrics })),
  addAlert: (alert) => set((state) => ({ alerts: [...state.alerts, alert] })),
  clearAlerts: () => set({ alerts: [] })
}));

export default useMiningStore;