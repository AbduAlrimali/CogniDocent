import { useCallback } from "react";
import { useWorkspaceStore } from "@/shared/store/useWorkspaceStore";

export const usePageNavigation = () => {
  const activePage = useWorkspaceStore((state) => state.activePage);
  const totalPages = useWorkspaceStore((state) => state.totalPages);
  const setActivePage = useWorkspaceStore((state) => state.setActivePage);

  const nextPage = useCallback(() => {
    if (activePage < totalPages) {
      setActivePage(activePage + 1);
    }
  }, [activePage, totalPages, setActivePage]);

  const prevPage = useCallback(() => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
    }
  }, [activePage, setActivePage]);

  const jumpTo = useCallback((page: number) => {
    const target = Math.min(Math.max(1, page), totalPages);
    setActivePage(target);
  }, [totalPages, setActivePage]);

  return { activePage, totalPages, nextPage, prevPage, jumpTo };
};
