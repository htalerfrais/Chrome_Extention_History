import { create } from 'zustand';
import { extensionBridge } from '../services/extensionBridge';
import type { SessionResults, SessionAnalysisStates, SessionAnalysisState } from '../types/session';

interface SessionStore {
  // State
  availableSessions: any[];
  activeSessionId: string | null;
  sessionResults: SessionResults;
  sessionAnalysisStates: SessionAnalysisStates;
  isReanalyzing: boolean;
  error: string | null;
  isInitialized: boolean;

  // Actions
  initializeSessions: () => Promise<void>;
  setActiveSession: (sessionId: string) => Promise<void>;
  analyzeSession: (sessionId: string) => Promise<void>;
  reanalyzeActiveSession: () => Promise<void>;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  // Initial state
  availableSessions: [],
  activeSessionId: null,
  sessionResults: {},
  sessionAnalysisStates: {},
  isReanalyzing: false,
  error: null,
  isInitialized: false,

  initializeSessions: async () => {
    try {
      set({ error: null });

      await extensionBridge.waitForExtensionServices();
      console.log('Extension services are ready');

      const constants = extensionBridge.getConstants();

      // Check API health
      const healthCheck = await extensionBridge.checkApiHealth();
      if (!healthCheck.success) {
        throw new Error(`API not available: ${healthCheck.error}`);
      }

      // Get all sessions
      const sessions = await extensionBridge.getAllSessions();
      console.log('Sessions:', sessions);
      if (sessions.length === 0) {
        throw new Error(constants.ERROR_NO_SESSIONS);
      }

      // Sort sessions by newest first
      const sortedSessions = sessions.sort((a: any, b: any) =>
        new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
      );

      // Add session_id field for internal use
      const sessionsWithId = sortedSessions.map((session: any) => ({
        ...session,
        session_id: session.session_identifier,
      }));

      // Initialize analysis states
      const initialStates: { [sessionId: string]: SessionAnalysisState } = {};
      sessionsWithId.forEach((session: any) => {
        initialStates[session.session_identifier] = 'pending';
      });

      set({
        availableSessions: sessionsWithId,
        sessionAnalysisStates: initialStates,
        isInitialized: true,
      });

      // Auto-analyze the first (most recent) session
      if (sessionsWithId.length > 0) {
        const firstSession = sessionsWithId[0];
        const firstSessionId = firstSession.session_identifier;

        set({ activeSessionId: firstSessionId });

        set((state) => ({
          sessionAnalysisStates: {
            ...state.sessionAnalysisStates,
            [firstSessionId]: 'loading' as SessionAnalysisState,
          },
        }));

        const clusterResult = await extensionBridge.clusterSession(firstSession);
        if (!clusterResult.success) {
          throw new Error(`Clustering failed: ${clusterResult.error}`);
        }

        set((state) => ({
          sessionResults: {
            ...state.sessionResults,
            [firstSessionId]: clusterResult.data,
          },
          sessionAnalysisStates: {
            ...state.sessionAnalysisStates,
            [firstSessionId]: 'completed' as SessionAnalysisState,
          },
        }));
      }
    } catch (error) {
      console.error('Session initialization failed:', error);
      set({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  setActiveSession: async (sessionId: string) => {
    set({ activeSessionId: sessionId });

    const { sessionAnalysisStates } = get();
    if (sessionAnalysisStates[sessionId] === 'pending') {
      await get().analyzeSession(sessionId);
    }
  },

  analyzeSession: async (sessionId: string) => {
    const { availableSessions, sessionAnalysisStates } = get();
    const session = availableSessions.find((s) => s.session_id === sessionId);
    if (!session) {
      console.error(`Session ${sessionId} not found`);
      return;
    }

    if (sessionAnalysisStates[sessionId] === 'completed') {
      return;
    }

    try {
      set((state) => ({
        sessionAnalysisStates: {
          ...state.sessionAnalysisStates,
          [sessionId]: 'loading' as SessionAnalysisState,
        },
      }));

      const clusterResult = await extensionBridge.clusterSession(session);
      if (!clusterResult.success) {
        throw new Error(`Clustering failed: ${clusterResult.error}`);
      }

      set((state) => ({
        sessionResults: {
          ...state.sessionResults,
          [sessionId]: clusterResult.data,
        },
        sessionAnalysisStates: {
          ...state.sessionAnalysisStates,
          [sessionId]: 'completed' as SessionAnalysisState,
        },
      }));
    } catch (error) {
      console.error(`Session analysis failed for ${sessionId}:`, error);
      set((state) => ({
        sessionAnalysisStates: {
          ...state.sessionAnalysisStates,
          [sessionId]: 'error' as SessionAnalysisState,
        },
      }));
    }
  },

  reanalyzeActiveSession: async () => {
    const { activeSessionId, availableSessions } = get();
    if (!activeSessionId) return;

    const session = availableSessions.find((s) => s.session_id === activeSessionId);
    if (!session) return;

    try {
      set({ isReanalyzing: true });

      const result = await extensionBridge.clusterSession(session, { force: true });
      if (!result.success) {
        throw new Error(`Clustering failed: ${result.error}`);
      }

      set((state) => ({
        sessionResults: {
          ...state.sessionResults,
          [activeSessionId]: result.data,
        },
        sessionAnalysisStates: {
          ...state.sessionAnalysisStates,
          [activeSessionId]: 'completed' as SessionAnalysisState,
        },
      }));
    } catch (error) {
      console.error('Re-analysis failed:', error);
    } finally {
      set({ isReanalyzing: false });
    }
  },
}));
