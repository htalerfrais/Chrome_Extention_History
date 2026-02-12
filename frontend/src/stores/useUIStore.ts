import { create } from 'zustand';

interface UIStore {
  // State
  isChatOpen: boolean;

  // Actions
  toggleChat: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isChatOpen: true,

  toggleChat: () => {
    set((state) => ({ isChatOpen: !state.isChatOpen }));
  },
}));
