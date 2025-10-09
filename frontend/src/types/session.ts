// TypeScript types for session and clustering functionality
// These define the data structures for browsing history sessions and clusters

// === History Item ===

export interface HistoryItem {
  url: string;
  title: string;
  visit_time: string;
}

// === Cluster ===

export interface Cluster {
  theme: string;
  items: HistoryItem[];
}

// === Session Data ===

export interface SessionData {
  session_start_time: string;
  session_end_time: string;
  clusters: Cluster[];
}

// === Session Analysis State ===

export type SessionAnalysisState = 'pending' | 'loading' | 'completed' | 'error';

export interface SessionAnalysisStates {
  [sessionId: string]: SessionAnalysisState;
}

// === Status Types ===

export type StatusType = 'loading' | 'success' | 'error';

// === Session Results (for App state) ===

export interface SessionResults {
  [sessionId: string]: SessionData;
}

