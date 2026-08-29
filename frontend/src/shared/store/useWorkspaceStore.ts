import { create } from "zustand";

export type ChatScope = "current_page" | "entire_document";

interface WorkspaceState {
  activeProjectId: string | null;
  activePage: number;
  totalPages: number;
  chatScope: ChatScope;
  currentProvider: string;
  currentModel: string;
  
  // Actions
  setActiveProjectId: (id: string | null) => void;
  setActivePage: (page: number) => void;
  setTotalPages: (total: number) => void;
  setChatScope: (scope: ChatScope) => void;
  setCurrentProvider: (provider: string) => void;
  setCurrentModel: (model: string) => void;
  
  /**
   * Action triggered by CitationPills or direct selection.
   * Jumps the PDF viewer to the specified page index (bounded between 1 and totalPages).
   */
  jumpToPage: (pageNumber: number) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  activeProjectId: null,
  activePage: 1,
  totalPages: 1,
  chatScope: "entire_document",
  currentProvider: "OLLAMA",
  currentModel: "llama3",
  
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setActivePage: (page) => set({ activePage: page }),
  setTotalPages: (total) => set({ totalPages: total }),
  setChatScope: (scope) => set({ chatScope: scope }),
  setCurrentProvider: (provider) => set({ currentProvider: provider }),
  setCurrentModel: (model) => set({ currentModel: model }),
  
  jumpToPage: (pageNumber) => set((state) => ({
    activePage: Math.min(Math.max(1, pageNumber), state.totalPages),
  })),
}));
